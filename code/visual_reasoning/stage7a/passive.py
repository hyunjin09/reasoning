"""Fixed late-layer telemetry, called only after immutable causal labels exist."""
import hashlib
import torch
from visual_reasoning.stage6b.runtime import Stage6BPassiveStep
from visual_reasoning.stage4a.runtime import event_coordinates, make_event_root
from visual_reasoning.stage3c9.streaming import clone_streaming_state, advance_streaming_state, score_preference_from_streaming_state


class StateCapture(Stage6BPassiveStep):
    def __enter__(self):
        super().__enter__()
        self.residual_vectors = {}
        for layer in (28, 29):
            def capture(module, args, index=layer):
                self.residual_vectors[str(index)] = args[0][0, -1].detach().float().cpu().numpy().copy()
            self.handles.append(self.model.model.language_model.layers[layer].register_forward_pre_hook(capture))
        return self


@torch.inference_mode()
def collect_prior_sink(model, prefill, event):
    """Historical t-minus8 definition, on an independent prefix-cache clone.

The current causal partition is rebuilt separately and remains unchanged.
"""
    current = int(event['current_query_zero_based']) - 8
    if current < 0:
        return dict(available=False, reason='t-minus8 precedes generated reasoning')
    end = current + 1
    history = event['history_before_ed_token_ids'][:end]
    adjusted = dict(event, candidate_start_token=end, current_query_zero_based=current,
                    history_before_ed_token_ids=history)
    state = make_event_root(model, prefill, adjusted) if end >= 8 else clone_streaming_state(prefill)
    for i in range(max(0, end-8), current):
        advance_streaming_state(model=model, state=state, token_ids=[history[i]],
                                seed=1234, chunk_size=1, release_allocator_cache=True)
    with Stage6BPassiveStep(model, prefill.prompt_length+current, {'sink': [0]}, None) as capture:
        advance_streaming_state(model=model, state=state, token_ids=[history[current]],
                                seed=1234, chunk_size=1, release_allocator_cache=True)
    assert set(capture.telemetry) == {'28', '29'}
    assert all(t['all_values_finite'] for t in capture.telemetry.values())
    return dict(available=True, current_query_zero_based=current, telemetry=capture.telemetry,
                residual_norms=capture.residual, attention_output_norms=capture.output_norms)


def sink_release(prior, current_telemetry):
    """Positive means lower sink mass now; missing history is not zero release."""
    if not prior['available']:
        return dict(available=False, reason=prior['reason'], layers={})
    return dict(available=True, definition='mean attention mass(t-8) minus mean attention mass(t)',
                layers={layer: prior['telemetry'][layer]['groups']['sink']['mean_attention_mass']
                        - current_telemetry[layer]['groups']['sink']['mean_attention_mass']
                        for layer in ('28', '29')})


@torch.inference_mode()
def collect_state(model, root, entry, input_meta):
    event = entry['event']
    coords = event_coordinates(event, root.prompt_length)
    state = clone_streaming_state(root)
    for i in range(coords['window_start'], coords['current']):
        advance_streaming_state(model=model, state=state, token_ids=[event['history_before_ed_token_ids'][i]],
                                seed=1234, chunk_size=1, release_allocator_cache=True)
    groups = {k: v for k, v in entry['source_groups'].items() if v and k != 'G'}
    visual = input_meta['visual_token_indices']
    if visual: groups['visual'] = visual
    groups['sink'] = [0]
    text = [i for i in range(1, root.prompt_length) if i not in set(visual)]
    if text: groups['prompt_text'] = text
    groups['reasoning'] = list(range(root.prompt_length, root.prompt_length+coords['end']))
    groups['recent_reasoning16'] = list(range(root.prompt_length+max(0, coords['current']-16),
                                             root.prompt_length+coords['current']))
    grid = (input_meta['image_grid_thw'][1]//2, input_meta['image_grid_thw'][2]//2) if visual else None
    with StateCapture(model, root.prompt_length+coords['current'], groups, grid) as capture:
        advance_streaming_state(model=model, state=state,
                                token_ids=[event['history_before_ed_token_ids'][coords['current']]],
                                seed=1234, chunk_size=1, release_allocator_cache=True)
    # Capture hooks have now been removed, before any candidate continuation.
    logits = state.last_logits.float()
    logp = torch.log_softmax(logits, dim=-1)
    report = dict(current_logits_sha256=hashlib.sha256(logits.cpu().numpy().tobytes()).hexdigest(),
                  telemetry=capture.telemetry, residual_norms=capture.residual,
                  attention_output_norms=capture.output_norms, groups=groups,
                  predictive_entropy=float(-(logp.exp()*logp).sum().item()),
                  generated_prefix_length=coords['end'], visual_token_count=len(visual),
                  feature_scope='Fixed layers28/29, all32 heads; current pre-layer residual vectors; current-query routing to the preceding16 reasoning-token keys; no selected-head search')
    report.update(score_preference_from_streaming_state(model=model, state=state,
                  original_suffix_ids=event['original_divergent_suffix_ids'],
                  counterfactual_suffix_ids=event['counterfactual_divergent_suffix_ids'], seed=1234))
    assert set(capture.telemetry) == set(capture.residual_vectors) == {'28', '29'}
    assert all(t['all_values_finite'] for t in capture.telemetry.values())
    return report, capture.residual_vectors
