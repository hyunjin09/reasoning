"""Stage7A named readouts on the unchanged Stage4A source-suppression path.

No attention, QK, residual or sink features are collected here. Output logits
are retained only for the predeclared distribution-similarity assay.
"""
import hashlib
import torch
from visual_reasoning.stage4a.runtime import MultiEvidenceStep, event_coordinates
from scripts.stage7a_bench.cache_residency_v12 import cache_prefix_audit, clone_streaming_state
from visual_reasoning.stage3c9.streaming import advance_streaming_state
from scripts.stage7a_bench.candidate_score_v12 import score_candidate_from_streaming_state


def first_difference(left, right):
    for i, (a, b) in enumerate(zip(left, right)):
        if a != b: return i
    return min(len(left),len(right)) if len(left)!=len(right) else None


@torch.inference_mode()
def score_bundle(model, root, event, groups, *, source=None, window=2, gain=0., validate=False, hooked=True):
    if window not in (2,8): raise ValueError('Only frozen W2/W8')
    coords=event_coordinates(event,root.prompt_length)
    assert root.generated_length==coords['window_start']
    if source: assert groups[source] and hooked
    state=clone_streaming_state(root)
    report=dict(roi=source,window=window,gain=gain,trigger=False,partition=coords['partition'],
        absolute_current_query=root.prompt_length+coords['current'],source_audits=[],step_audits=[],
        passive_features_collected=False,clone_no_alias=None)
    if validate:
        report['clone_no_alias']=all(a.keys.data_ptr()!=b.keys.data_ptr() and a.values.data_ptr()!=b.values.data_ptr() for a,b in zip(root.cache.layers,state.cache.layers))
        assert report['clone_no_alias']
    for i in range(coords['window_start'],coords['end']):
        active=source if i>=coords['end']-window else None
        if hooked:
            with MultiEvidenceStep(model,absolute_query=root.prompt_length+i,groups=groups,roi=active,gain=gain,validate=validate) as patch:
                advance_streaming_state(model=model,state=state,token_ids=[event['history_before_ed_token_ids'][i]],seed=1234,chunk_size=1,release_allocator_cache=True)
            assert patch.layer_calls==list(range(36)) and patch.finite
            report['source_audits'].extend(patch.audits)
            report['step_audits'].append(dict(generated_query=i,layers=patch.layer_calls,finite=patch.finite,active_roi=active))
        else:
            assert not source
            advance_streaming_state(model=model,state=state,token_ids=[event['history_before_ed_token_ids'][i]],seed=1234,chunk_size=1,release_allocator_cache=True)
    report['past_cache_audit']=cache_prefix_audit(root,state) if validate else None
    logits=state.last_logits.float();logp=torch.log_softmax(logits,dim=-1)
    report['current_logits_sha256']=hashlib.sha256(logits.cpu().numpy().tobytes()).hexdigest()
    report['predictive_entropy']=float(-(logp.exp()*logp).sum().item())
    named=event.get('candidate_ids',dict(correct=event['original_divergent_suffix_ids'],foil=event['counterfactual_divergent_suffix_ids'],native=event['native_claim_suffix_ids']))
    cache={};scores={}
    for name,ids in named.items():
        key=tuple(ids)
        if key not in cache: cache[key]=score_candidate_from_streaming_state(model=model,state=state,candidate_token_ids=ids,seed=1234)
        scores[name]=cache[key]
    correct,foil,actual=(scores[k]['mean_log_probability'] for k in ['correct','foil','native'])
    report.update(candidates=scores,L_o=correct,L_c=foil,D=correct-foil,
        original_candidate=scores['correct'],counterfactual_candidate=scores['foil'],
        observed_claim_log_probability=actual,observed_minus_correct=actual-correct,
        finite=all(s['finite'] for s in scores.values()))
    different=first_difference(named['native'],named['correct'])
    report['first_wrong_token_offset']=different
    report['first_wrong_token_log_probability']=(scores['native']['token_log_probabilities'][different] if different is not None and different<len(named['native']) else None)
    report['first_correct_token_log_probability']=(scores['correct']['token_log_probabilities'][different] if different is not None and different<len(named['correct']) else None)
    wrong_lp,correct_lp=report['first_wrong_token_log_probability'],report['first_correct_token_log_probability']
    report['wrong_minus_correct_token_margin']=(wrong_lp-correct_lp if wrong_lp is not None and correct_lp is not None else None)
    report['error_token_orientation']='First differing actual/correct token after their shared candidate prefix; full-claim mean margin is reported separately. A missing corresponding token is an unavailable token-margin readout.'
    assert report['finite']
    distribution=logp.cpu().numpy()
    del state
    return report,distribution
