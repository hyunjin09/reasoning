"""Matched cached-query execution for the frozen multi-evidence assay."""
from contextlib import AbstractContextManager
from types import MethodType
import hashlib
import torch

from visual_reasoning.stage3b6.heads import _attention_module, _project_attention_output
from visual_reasoning.stage3c1.metrics import _repeat_kv
from visual_reasoning.stage3c3.runtime import _projection_parts, _run_attention
from visual_reasoning.stage3c3.metrics import summarize_routing_state
from visual_reasoning.stage3c10.runtime import delete_sources, cache_prefix_audit
from visual_reasoning.stage3c9.streaming import (
    advance_streaming_state, clone_streaming_state, fixed_chunk_ranges,
    score_preference_from_streaming_state,
)

HEADS = list(range(32))
TRIGGER_LAYERS = list(range(16, 24))
TELEMETRY_HEADS = {28: [16, 0, 3, 6], 29: [11, 6, 15, 12]}


def event_coordinates(event, prompt_length):
    end = int(event['candidate_start_token'])
    current = int(event['current_query_zero_based'])
    if end != current + 1 or end < 8 or len(event['history_before_ed_token_ids']) != end:
        raise ValueError('Invalid frozen event coordinates')
    start = current - 7
    partition = fixed_chunk_ranges(start=0, end=start, chunk_size=2048)
    partition += [(i, i + 1) for i in range(start, end)]
    return {'current': current, 'window_start': start, 'end': end,
            'partition': partition,
            'R16': [prompt_length+i for i in range(max(0, current-16), current)]}


def intervention_sources(groups, roi, trigger_positions=()):
    """A+B is one union reduction; R16 and ROI are separate native terms."""
    parts, names = [], []
    if trigger_positions:
        parts.append(list(trigger_positions)); names.append('R16')
    if roi:
        positions = sorted(set(groups['A']) | set(groups['B'])) if roi == 'AB' else list(groups[roi])
        parts.append(positions); names.append(roi)
    if any(set(a) & set(b) for i, a in enumerate(parts) for b in parts[i+1:]):
        raise ValueError('Trigger and visual sources overlap')
    return parts, names


def passive_groups(meta, event, r16):
    fact = event['fact']
    # An unmatched I is only a passive reference, never a scored matched control.
    available = [x for x in (fact, 'A', 'B')
                 if not meta['irrelevant_mapping'][x].get('unavailable')
                 and meta['irrelevant_mapping'][x].get('manual_review', '').startswith('pass')]
    if not available:
        raise ValueError('No validated passive reference region')
    ref = 'I_' + available[0]
    g = meta['source_groups']
    return {'T': g['A'], 'M': g['B'], 'I': g[ref], 'sink': [0], 'R16': r16}, ref


class MultiEvidenceStep(AbstractContextManager):
    def __init__(self, model, *, absolute_query, groups, roi=None,
                 trigger_positions=(), gain=0., telemetry_groups=None, validate=False):
        self.model = model
        self.absolute_query = absolute_query
        self.groups = groups
        self.roi = roi
        self.trigger = list(trigger_positions)
        self.gain = gain
        self.telemetry_groups = telemetry_groups
        self.validate = validate
        self.originals, self.handles, self.audits = [], [], []
        self.telemetry, self.residual_norms = {}, {}
        self.layer_calls, self.finite = [], True

    def _run(self, module, hidden_states, position_embeddings, attention_mask,
             past_key_values=None, **kwargs):
        if hidden_states.shape[1] != 1:
            raise RuntimeError('Intervention escaped the fixed single-query barrier')
        layer = int(module.layer_idx)
        _, _, q, k, v = _projection_parts(module, hidden_states, position_embeddings)
        if past_key_values is not None:
            k, v = past_key_values.update(k, v, layer)
        offset = int(k.shape[2]) - 1
        if offset != self.absolute_query:
            raise RuntimeError('Absolute query coordinate mismatch')
        native, alpha = _run_attention(module, q, k, v, attention_mask, kwargs)
        parts, names = intervention_sources(self.groups, self.roi,
                         self.trigger if layer in TRIGGER_LAYERS else ())
        snapshots = [x.clone() for x in (q, k, v, alpha)] if self.validate and parts else None
        patched, audits = delete_sources(native, alpha, _repeat_kv(v, int(module.num_key_value_groups)),
                                        parts, offset=offset, gain=self.gain)
        for name, audit in zip(names, audits):
            row = {**audit, 'source_kind': name, 'layer_index': layer}
            if snapshots is not None:
                row.update({key: torch.equal(x, before) for key, x, before in
                            zip(('query_exact', 'key_exact', 'value_exact', 'attention_exact'),
                                (q, k, v, alpha), snapshots)})
            self.audits.append(row)
        if self.validate and parts:
            # Independently reconstruct the declared reductions, including joint AB.
            values = _repeat_kv(v, int(module.num_key_value_groups))
            expected = native[:, 0].float()
            for positions in parts:
                term = (alpha[:, :, 0, positions, None].to(values.dtype) * values[:, :, positions]).sum(2).float()
                expected = expected - (1. - self.gain) * term
            expected = native[:, 0] if self.gain == 1. else expected.to(native.dtype)
            if not torch.equal(patched[:, 0], expected):
                raise RuntimeError('Source union/component arithmetic differs from explicit reference')
            for row in self.audits[-len(parts):]:
                row['explicit_source_reference_exact'] = True
        if self.telemetry_groups is not None and layer in TELEMETRY_HEADS:
            state = {'post_rope_query': q[:, :, 0].detach(), 'key': k.detach(), 'value': v.detach(),
                     'attention': alpha[:, :, 0].detach(), 'wo_weight': module.o_proj.weight.detach(),
                     'scaling': float(module.scaling), 'num_key_value_groups': int(module.num_key_value_groups)}
            self.telemetry[str(layer)] = {
                role: summarize_routing_state(state, groups=self.telemetry_groups, selected_heads=heads)
                for role, heads in [('selected', TELEMETRY_HEADS[layer]), ('all', HEADS)]}
        output = _project_attention_output(module, patched, hidden_states)
        self.finite &= bool(torch.isfinite(output).all().item())
        self.layer_calls.append(layer)
        return output, alpha

    def __enter__(self):
        for layer in range(36):
            module = _attention_module(self.model, layer)
            self.originals.append((module, module.forward))
            def forward(module, hidden_states, position_embeddings, attention_mask, past_key_values=None, **kwargs):
                return self._run(module, hidden_states, position_embeddings, attention_mask, past_key_values, **kwargs)
            module.forward = MethodType(forward, module)
        if self.telemetry_groups is not None:
            for layer in TELEMETRY_HEADS:
                def capture(module, args, index=layer):
                    self.residual_norms[str(index)] = float(args[0].detach().float().norm().item())
                self.handles.append(self.model.model.language_model.layers[layer].register_forward_pre_hook(capture))
        return self

    def __exit__(self, *args):
        for module, original in self.originals:
            module.forward = original
        for handle in self.handles:
            handle.remove()


@torch.inference_mode()
def make_event_root(model, prefill, event):
    coords = event_coordinates(event, prefill.prompt_length)
    root = clone_streaming_state(prefill)
    context = event['history_before_ed_token_ids']
    for left, right in coords['partition']:
        if right > coords['window_start']:
            break
        if root.generated_length != left:
            raise RuntimeError('Prefix left the canonical event partition')
        advance_streaming_state(model=model, state=root, token_ids=context[left:right], seed=1234,
                                chunk_size=2048, release_allocator_cache=True)
    return root


@torch.inference_mode()
def score_event_arm(model, root, meta, event, *, roi=None, window=2, trigger=False,
                    gain=0., telemetry=False, validate=False, hooked=True):
    if window not in (2, 8):
        raise ValueError('Only predeclared W2 and W8 are authorized')
    coords = event_coordinates(event, root.prompt_length)
    if root.generated_length != coords['window_start']:
        raise ValueError('Root is not immediately before W8')
    if roi and roi.startswith('I_') and not meta.get('irrelevant_controls_validated'):
        raise ValueError('Matched irrelevant-control eligibility was not validated')
    state = clone_streaming_state(root)
    clone_no_alias = all(a.keys.data_ptr() != b.keys.data_ptr() and a.values.data_ptr() != b.values.data_ptr()
                         for a, b in zip(root.cache.layers, state.cache.layers)) if validate else None
    aliases, reference = passive_groups(meta, event, coords['R16']) if telemetry else (None, None)
    public = {'roi': roi, 'window': window, 'trigger': trigger, 'gain': gain,
              'partition': coords['partition'], 'absolute_current_query': root.prompt_length+coords['current'],
              'trigger_positions': coords['R16'] if trigger else [], 'trigger_layers': TRIGGER_LAYERS if trigger else [],
              'source_audits': [], 'step_audits': [], 'telemetry': {}, 'residual_norms': {},
              'clone_no_alias': clone_no_alias,
              'passive_aliases': {'T': 'A', 'M': 'B', 'I': reference, 'sink': 'prompt_position_0', 'R16': 'strictly_preceding_reasoning'} if telemetry else None}
    for i in range(coords['window_start'], coords['end']):
        active_roi = roi if i >= coords['end']-window else None
        active_trigger = coords['R16'] if trigger and i == coords['current'] else []
        patch = MultiEvidenceStep(model, absolute_query=root.prompt_length+i, groups=meta['source_groups'],
                     roi=active_roi, trigger_positions=active_trigger, gain=gain,
                     telemetry_groups=aliases if i == coords['current'] else None, validate=validate)
        if hooked:
            with patch:
                advance_streaming_state(model=model, state=state, token_ids=[event['history_before_ed_token_ids'][i]],
                                        seed=1234, chunk_size=1, release_allocator_cache=True)
            if patch.layer_calls != list(range(36)):
                raise RuntimeError('Not all36 layers executed exactly once')
            public['source_audits'].extend(patch.audits)
            public['step_audits'].append({'generated_query': i, 'layers': patch.layer_calls, 'finite': patch.finite,
                                         'active_roi': active_roi, 'active_trigger': bool(active_trigger)})
            if patch.telemetry:
                public['telemetry'] = patch.telemetry
                public['residual_norms'] = patch.residual_norms
        else:
            if roi or trigger:
                raise ValueError('Unhooked run must be an unchanged native control')
            advance_streaming_state(model=model, state=state, token_ids=[event['history_before_ed_token_ids'][i]],
                                    seed=1234, chunk_size=1, release_allocator_cache=True)
    public['past_cache_audit'] = cache_prefix_audit(root, state) if validate else None
    logits = state.last_logits.float()
    lp = torch.log_softmax(logits, dim=-1)
    public['predictive_entropy'] = float(-(lp.exp()*lp).sum().item())
    public['current_logits_sha256'] = hashlib.sha256(logits.cpu().numpy().tobytes()).hexdigest()
    public.update(score_preference_from_streaming_state(model=model, state=state,
                  original_suffix_ids=event['original_divergent_suffix_ids'],
                  counterfactual_suffix_ids=event['counterfactual_divergent_suffix_ids'], seed=1234))
    public['local_native_preferred'] = public['D'] > 0
    return public
