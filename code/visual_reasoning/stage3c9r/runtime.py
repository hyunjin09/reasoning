"""One partition and actual suppressed cache forks for every repair condition."""

from __future__ import annotations

import copy
from contextlib import ExitStack

import torch

from visual_reasoning.stage3c4.runtime import SourceContributionWindowPatch
from visual_reasoning.stage3c9.assay import source_window_indices
from visual_reasoning.stage3c9.streaming import (
    advance_streaming_state, clone_streaming_state, patch_streaming_state,
    roll_streaming_prefix, score_preference_from_streaming_state,
)
from .protocol import shared_partition


def copy_state_to(state, device):
    """Copy only; no model execution or arithmetic/dtype conversion."""
    result = copy.deepcopy(state)
    for layer in result.cache.layers:
        layer.keys = layer.keys.to(device)
        layer.values = layer.values.to(device)
    result.rope_deltas = result.rope_deltas.to(device)
    result.last_logits = result.last_logits.to(device)
    return result


def measured_patch(recipient, *, donor, generated_positions, visual_positions):
    """Validate real before/after cache tensors instead of trusting audit flags."""
    result, audit = patch_streaming_state(
        recipient, donor=donor, generated_positions=generated_positions,
        visual_positions=visual_positions,
    )
    selected = [recipient.prompt_length + p for p in sorted(generated_positions)]
    length = recipient.cache.layers[0].keys.shape[2]
    boundaries = [-1, *selected, length]
    rows = []
    for index, (before, after, source) in enumerate(zip(recipient.cache.layers, result.cache.layers, donor.cache.layers)):
        checks = {'layer': index, 'shape': list(after.keys.shape)}
        for name in ('keys', 'values'):
            old, new, expected = getattr(before, name), getattr(after, name), getattr(source, name)
            checks[f'{name}_nonselected_exact'] = all(
                torch.equal(old[:, :, a + 1:b], new[:, :, a + 1:b])
                for a, b in zip(boundaries, boundaries[1:])
            )
            checks[f'{name}_visual_exact'] = torch.equal(old[:, :, visual_positions], new[:, :, visual_positions])
            checks[f'{name}_selected_exact'] = torch.equal(new[:, :, selected], expected[:, :, selected])
        rows.append(checks)
    audit['measured_invariance'] = {
        'layers': rows,
        'all_nonselected_exact': all(r['keys_nonselected_exact'] and r['values_nonselected_exact'] for r in rows),
        'visual_exact': all(r['keys_visual_exact'] and r['values_visual_exact'] for r in rows),
        'selected_exact': all(r['keys_selected_exact'] and r['values_selected_exact'] for r in rows),
        'logits_unchanged_at_patch': torch.equal(recipient.last_logits, result.last_logits),
    }
    return result, audit


@torch.inference_mode()
def advance_partition(*, model, state, prefix, partition, seed, suppressed=(),
                      layers=(), heads=(), target_positions=(), capture_ends=()):
    """Execute the inherited eager kernels with the already frozen query shapes."""
    captures, executions, actual_ranges = {}, [], []
    for left, right in partition:
        if right <= state.generated_length:
            continue
        if left != state.generated_length:
            raise ValueError('A fork must resume at an existing partition boundary')
        active = [p for p in suppressed if left <= p < right]
        patches = [SourceContributionWindowPatch(
            model=model, layer_index=layer,
            query_positions=[state.prompt_length + p for p in active],
            selected_heads=heads, source_positions=target_positions, gain=0.,
        ) for layer in layers] if active else []
        with ExitStack() as stack:
            for patch in patches:
                stack.enter_context(patch)
            advance_streaming_state(model=model, state=state, token_ids=prefix[left:right],
                                    seed=seed, chunk_size=right-left, release_allocator_cache=True)
        if patches:
            executions.append({'generated_query_indices': active,
                               'layer_audits': [patch.complete() for patch in patches]})
        actual_ranges.append([left, right])
        if right in capture_ends:
            captures[right] = copy_state_to(state, 'cpu')
    return state, captures, {'executed_chunk_ranges': actual_ranges,
                             'source_suppression_executions': executions}


def exact_score(left, right):
    return (left['D'] == right['D'] and all(
        left[c]['token_log_probabilities'] == right[c]['token_log_probabilities']
        for c in ('original_candidate', 'counterfactual_candidate')
    ))


@torch.inference_mode()
def score_family(*, model, prefill, sequences, event, layers, heads,
                 target_positions, visual_positions, seed, execution_prefix,
                 validate=False, compare_inherited=False, windows=('W8', 'W16'),
                 necessity=False):
    """Return both window families; every gain shares one persisted denominator.

    Native/suppressed prefix cache snapshots are exact CPU copies from their
    own single executions. Event and neighbor arms fork those saved recipients.
    The generated query partitions and candidate scoring kernels never change.
    """
    prefix = sequences['prefix_token_ids']
    partition = shared_partition(event, end=len(prefix))
    span = list(range(event['span_start_token'], event['span_end_token']))
    neighbor = list(range(event['matched_neighbor_span']['start_token'], event['matched_neighbor_span']['end_token']))
    ends = [max(span) + 1, max(neighbor) + 1]
    device = prefill.last_logits.device

    def advance(state, suppressed=(), capture=False):
        return advance_partition(model=model, state=state, prefix=prefix, partition=partition,
                                 seed=seed, suppressed=suppressed, layers=layers, heads=heads,
                                 target_positions=target_positions, capture_ends=ends if capture else ())

    def score(state):
        return score_preference_from_streaming_state(
            model=model, state=state, original_suffix_ids=sequences['original_suffix_ids'],
            counterfactual_suffix_ids=sequences['counterfactual_suffix_ids'], seed=seed,
        )

    native_state, native_roots, native_audit = advance(clone_streaming_state(prefill), capture=True)
    native = {**score(native_state), 'streaming_audit': native_audit}
    del native_state

    def branch(root, donor, positions, suppressed, execution_id):
        if validate:
            patched, patch_audit = measured_patch(root, donor=donor, generated_positions=positions,
                                                  visual_positions=visual_positions)
        else:
            patched, patch_audit = patch_streaming_state(root, donor=donor, generated_positions=positions,
                                                         visual_positions=visual_positions)
        # Moving an exact saved fork changes storage only, never numerical shape.
        state = copy_state_to(patched, device)
        del patched
        state, _, stream = advance(state, suppressed=suppressed)
        result = {**score(state), 'cache_patch': patch_audit, 'streaming_audit': stream,
                  'recipient_execution_id': execution_id,
                  'fork_generated_length': root.generated_length,
                  'partition': [list(r) for r in partition]}
        del state
        return result

    results = {}
    for window in windows:
        if event['span_start_token'] < int(window[1:]):
            continue
        indices = source_window_indices(span_start_token=event['span_start_token'], width=int(window[1:]))
        execution_id = f'{execution_prefix}/{window}/suppressed'
        suppressed_state, suppressed_roots, suppressed_audit = advance(
            clone_streaming_state(prefill), suppressed=indices, capture=True,
        )
        suppressed = {**score(suppressed_state), 'streaming_audit': suppressed_audit,
                      'execution_id': execution_id}
        del suppressed_state
        event_score = branch(suppressed_roots[ends[0]], native_roots[ends[0]], span, indices, execution_id)
        neighbor_score = branch(suppressed_roots[ends[1]], native_roots[ends[1]], neighbor, indices, execution_id)
        controls = None
        if validate:
            native_self = branch(native_roots[ends[0]], native_roots[ends[0]], span, (), 'native_self')
            suppressed_self = branch(suppressed_roots[ends[0]], suppressed_roots[ends[0]], span, indices, execution_id)
            replay = branch(suppressed_roots[ends[0]], native_roots[ends[0]], span, indices, execution_id)
            controls = {'native_self': native_self, 'suppressed_self': suppressed_self,
                        'native_to_native_exact': exact_score(native, native_self),
                        'suppressed_to_suppressed_exact': exact_score(suppressed, suppressed_self),
                        'rescue_replay_exact': exact_score(event_score, replay)}
            # A complete independent replay validates the captured recipient too.
            replay_state, _, _ = advance(clone_streaming_state(prefill), suppressed=indices)
            controls['suppressed_replay_exact'] = exact_score(suppressed, score(replay_state))
            del replay_state
        inherited = None
        if compare_inherited:
            common = dict(model=model, prefill=prefill, prefix_token_ids=prefix,
                          end_generated_index=len(prefix), seed=seed, layers=layers,
                          selected_heads=heads, source_positions=target_positions,
                          chunk_size=2048, release_allocator_cache=True,
                          forced_generated_boundaries=[b for _, b in partition[:-1]])
            old_native_state, _ = roll_streaming_prefix(**common)
            old_suppressed_state, _ = roll_streaming_prefix(**common, suppressed_generated_indices=indices)
            inherited = {'native_exact': exact_score(native, score(old_native_state)),
                         'suppressed_exact': exact_score(suppressed, score(old_suppressed_state))}
            del old_suppressed_state
            old_event, _ = roll_streaming_prefix(**common, suppressed_generated_indices=indices,
                donor=old_native_state, patch_generated_indices=span, visual_positions=visual_positions)
            inherited['event_rescue_exact'] = exact_score(event_score, score(old_event))
            del old_event, old_native_state
        necessity_score = None
        if necessity:
            necessity_score = branch(native_roots[ends[0]], suppressed_roots[ends[0]], span, (),
                                     f'{execution_prefix}/native')
        results[window] = {
            'execution_id': execution_id, 'partition': [list(r) for r in partition],
            'readout_generated_index': sequences['readout_generated_index'],
            'prefix_sha256': sequences['prefix_sha256'],
            'source_window_generated_indices': indices,
            'native': native, 'suppressed': suppressed, 'event_rescue': event_score,
            'neighbor_rescue': neighbor_score, 'self_controls': controls,
            'inherited_path_comparison': inherited, 'necessity': necessity_score,
        }
        del suppressed_roots
    del native_roots
    return results
