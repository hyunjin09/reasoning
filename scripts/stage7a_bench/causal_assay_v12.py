"""Run the frozen source windows with the unchanged Stage7A scoring operation.

This helper needs a caller-verified frozen entry and prepared native root. It
does not load models, admit candidates, run source edits or classify results.
"""
import torch

from scripts.stage7a_bench.causal_prefix_v12 import require_canonical_assay_attention
from scripts.stage7a_bench.score_bundle_v12 import score_bundle
from scripts.stage7a_bench.cache_residency_v12 import clone_streaming_state
from visual_reasoning.stage4a.runtime import score_event_arm as original_score_event_arm
from visual_reasoning.stage6b.runtime import score_equal


@torch.inference_mode()
def score_frozen_sources(model, root, entry, *, mechanics=False):
    if (entry.get('causal_pilot_frozen') is not True or
            entry.get('selection_used_causal_or_passive_scores') is not False):
        raise ValueError('Source scoring requires a pilot frozen without causal/passive selection')
    groups = entry['source_groups']
    if (not groups or not set(groups) <= {'T', 'X', 'X2', 'I', 'G'} or
            not groups.get('G') or any(not positions or len(set(positions)) != len(positions) or
            any(type(p) is not int or not 0 <= p < root.prompt_length for p in positions)
            for positions in groups.values()) or
            any(not set(v) <= set(groups['G']) for v in groups.values())):
        raise ValueError('Frozen source groups must contain real visual prompt positions')
    if (entry['w2_sources'] != [s for s in ('T', 'X', 'X2', 'I', 'G') if s in groups] or
            entry['w8_sources'] != [s for s in ('T', 'X') if s in groups]):
        raise ValueError('All sources require W2; all available T/X require W8')
    require_canonical_assay_attention()
    if model.training or len(model.model.language_model.layers) != 36:
        raise ValueError('Inherited source assay requires an evaluation model with36 layers')
    event = entry['event']
    arms, distributions, checks = {}, {}, {}
    arms['N'], distributions['N'] = score_bundle(model, root, event, groups, validate=mechanics)
    settings = dict(source_groups=groups, irrelevant_controls_validated=False)
    if mechanics:
        canonical = score_event_arm(model, root, settings, event, validate=True)
        unhooked, _ = score_bundle(model, root, event, groups, hooked=False)
        checks.update(canonical_native_exact=score_equal(arms['N'], canonical),
            unhooked_exact=score_equal(arms['N'], unhooked))
    for window, sources in ((2, entry['w2_sources']), (8, entry['w8_sources'])):
        for source in sources:
            key = f'{source}_W{window}'
            arms[key], _ = score_bundle(model, root, event, groups,
                source=source, window=window, validate=mechanics)
            if mechanics:
                canonical = score_event_arm(model, root, settings, event,
                    roi=source, window=window, validate=True)
                checks[key+'_canonical_exact'] = score_equal(arms[key], canonical)
    if mechanics:
        source = entry['w2_sources'][0]
        noop, _ = score_bundle(model, root, event, groups, source=source, window=8, gain=1., validate=True)
        repeated, _ = score_bundle(model, root, event, groups, source=source, validate=True)
        checks.update(noop_exact=score_equal(arms['N'], noop),
            suppression_repeat_exact=repeated == arms[source+'_W2'])
    checks['all_finite'] = all(a['finite'] for a in arms.values())
    if not all(checks.values()):
        raise RuntimeError('Inherited source-assay mechanics failed: ' + str(checks))
    return dict(arms=arms, distributions=distributions, checks=checks,
        passive_features_collected=False, semantic_controls_scored=False)


@torch.inference_mode()
def score_event_arm(model, root, *args, **kwargs):
    # Independent unchanged canonical scorer runs only on the minimum-cost
    # mechanics entry, where its multiple resident caches fit comfortably.
    resident = clone_streaming_state(root)
    try:
        return original_score_event_arm(model, resident, *args, **kwargs)
    finally:
        del resident
        if root.last_logits.device.type == 'cuda':
            torch.cuda.empty_cache()
