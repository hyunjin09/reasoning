"""Stage6B telemetry on the unchanged Stage4A canonical event partition."""
import hashlib
import torch

from visual_reasoning.stage3c9.streaming import clone_streaming_state, advance_streaming_state, score_preference_from_streaming_state, score_candidate_from_streaming_state
from visual_reasoning.stage4a.runtime import event_coordinates, TELEMETRY_HEADS
from visual_reasoning.stage5a.passive import PassiveStep


def score_equal(left, right):
    return all(left[key] == right[key] for key in
               ('D', 'L_o', 'L_c', 'current_logits_sha256', 'original_candidate', 'counterfactual_candidate'))


class Stage6BPassiveStep(PassiveStep):
    def __init__(self, model, absolute_query, groups, grid):
        super().__init__(model, absolute_query, groups)
        self.grid = grid

    def _run(self, module, hidden_states, position_embeddings, attention_mask,
             past_key_values=None, **kwargs):
        output, alpha = super()._run(module, hidden_states, position_embeddings,
                                    attention_mask, past_key_values, **kwargs)
        result = self.telemetry[str(module.layer_idx)]
        visual = self.groups.get('visual', [])
        for head in result['per_head']:
            for group in head['groups'].values():
                group.pop('alpha_v_vector', None)  # Norms are the declared features.
        if visual:
            a = alpha[0, :, 0].float()
            visual_mass = a[:, visual].sum(-1).clamp_min(1e-30)
            positions = {position:i for i, position in enumerate(visual)}
            for name, group in self.groups.items():
                if name in ('visual', 'sink', 'prompt_text', 'reasoning'):
                    continue
                if not set(group) <= set(visual):
                    continue
                shares = a[:, group].sum(-1) / visual_mass
                result['groups'][name]['mean_visual_attention_share'] = shares.mean().item()
                for i, head in enumerate(result['per_head']):
                    head['groups'][name]['visual_attention_share'] = shares[i].item()
                # Same-size translated rectangle reference for rectangular C2 ROIs.
                if self.grid:
                    height, width = self.grid
                    local = [positions[x] for x in group]
                    ys, xs = [x//width for x in local], [x%width for x in local]
                    box_h, box_w = max(ys)-min(ys)+1, max(xs)-min(xs)+1
                    if len(local) == box_h*box_w:
                        pooled = torch.nn.functional.avg_pool2d(
                            a[:, visual].reshape(32, 1, height, width), (box_h, box_w), stride=1).flatten(1)
                        density = a[:, group].mean(-1)
                        percentiles = (pooled <= density[:, None]).float().mean(-1)
                        result['groups'][name]['matched_rectangle_attention_percentile'] = percentiles.mean().item()
                        result['groups'][name]['percentile_reference_windows'] = pooled.shape[1]
        result['historical_selected_heads'] = TELEMETRY_HEADS[int(module.layer_idx)]
        return output, alpha


@torch.inference_mode()
def collect_passive(model, root, entry, input_meta):
    event = entry['event']; coords = event_coordinates(event, root.prompt_length)
    state = clone_streaming_state(root)
    for i in range(coords['window_start'], coords['current']):
        advance_streaming_state(model=model, state=state,
            token_ids=[event['history_before_ed_token_ids'][i]], seed=1234,
            chunk_size=1, release_allocator_cache=True)
    groups = {k:v for k,v in entry['source_groups'].items() if v}
    visual = input_meta['visual_token_indices']
    if visual:
        groups['visual'] = visual
    groups['sink'] = [0]
    text = [i for i in range(1, root.prompt_length) if i not in set(visual)]
    if text:
        groups['prompt_text'] = text
    groups['reasoning'] = list(range(root.prompt_length, root.prompt_length+coords['end']))
    grid = (input_meta['image_grid_thw'][1]//2, input_meta['image_grid_thw'][2]//2) if visual else None
    with Stage6BPassiveStep(model, root.prompt_length+coords['current'], groups, grid) as capture:
        advance_streaming_state(model=model, state=state,
            token_ids=[event['history_before_ed_token_ids'][coords['current']]],
            seed=1234, chunk_size=1, release_allocator_cache=True)
    logits = state.last_logits.float()
    logp = torch.log_softmax(logits, dim=-1)
    top = torch.topk(logp, k=50)
    report = {'current_logits_sha256': hashlib.sha256(logits.cpu().numpy().tobytes()).hexdigest(),
        'telemetry': capture.telemetry, 'residual_norms': capture.residual,
        'attention_output_norms': capture.output_norms,
        'predictive_entropy': -(logp.exp()*logp).sum().item(),
        'top50_token_ids': top.indices.cpu().tolist(), 'top50_log_probabilities': top.values.cpu().tolist(),
        'feature_scope': 'layers28-29 all32 heads; matched rectangle references are descriptive, not causal controls'}
    report.update(score_preference_from_streaming_state(model=model, state=state,
        original_suffix_ids=event['original_divergent_suffix_ids'],
        counterfactual_suffix_ids=event['counterfactual_divergent_suffix_ids'], seed=1234))
    if event.get('native_claim_suffix_ids'):
        report['observed_claim_candidate'] = score_candidate_from_streaming_state(
            model=model, state=state, candidate_token_ids=event['native_claim_suffix_ids'], seed=1234)
    assert set(capture.telemetry)=={'28','29'}
    assert all(r['all_values_finite'] for r in capture.telemetry.values())
    return report, logp.cpu().numpy()
