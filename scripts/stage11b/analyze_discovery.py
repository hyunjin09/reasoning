"""Open discovery correctness only after eligibility and extraction seals."""
from collections import Counter
import pandas as pd
from scripts.stage11b.common import ROOT,load,save,sha,now
from scripts.stage11b.protocol import CANDIDATES,in_stratum,discovery_gate
from visual_reasoning.stage8b.v2_scoring import score_answer

def main():
    evidence=load(ROOT/'annotations/discovery_evidence_final.json');assert evidence['sealed']
    answers=load(ROOT/'annotations/discovery_answers_final.json');assert answers['sealed']
    source={r['item_id']:r for r in load(ROOT/'stage11b_discovery_manifest_v2.json')['rows']}
    gold={r['item_id']:r for r in evidence['rows']}
    keys={r['packet_id']:r for r in load(ROOT/'audit/discovery_answer_key.json')['rows']}
    results=[]
    for review in answers['rows']:
        key=keys[review['packet_id']];r=source[key['item_id']]
        text='' if review['answer'] is None else '\\boxed{'+review['answer']+'}'
        scored=score_answer(text,r);receipt=load(ROOT/'discovery/results'/key['task_id']/'result.json')
        results.append(dict(key,family_id=r['family_id'],correct=scored['correct'] is True,
            benchmark_label=scored['benchmark_label'],reviewed_answer=review['answer'],normal_eos=receipt['normal_eos'],
            at_length_cap=receipt['at_length_cap'],no_literal_final=review['answer'] is None,tokens=receipt['tokens'],
            e_star_eligible=gold[r['item_id']]['eligibility']=='E_STAR_ELIGIBLE'))
    assert len(results)==256 and len({r['task_id'] for r in results})==256
    by={(r['item_id'],r['arm']):r for r in results};strata=[]
    for rule in CANDIDATES:
        rows=[r for r in source.values() if in_stratum(r,rule)]
        eligible=[r for r in rows if gold[r['item_id']]['eligibility']=='E_STAR_ELIGIBLE']
        t=sum(by[r['item_id'],'thinking']['correct'] for r in eligible)
        c=sum(by[r['item_id'],'instruct_cot']['correct'] for r in eligible)
        forward=sum(by[r['item_id'],'thinking']['correct'] and not by[r['item_id'],'instruct_cot']['correct'] for r in eligible)
        reverse=sum(by[r['item_id'],'instruct_cot']['correct'] and not by[r['item_id'],'thinking']['correct'] for r in eligible)
        gate=discovery_gate(len(rows),len(eligible),t,c,forward)
        types=Counter(gold[r['item_id']]['facts'][0]['evidence_type'] for r in eligible)
        subjects=Counter(r['subject'] for r in eligible)
        depth=sum(gold[r['item_id']]['reasoning_depth_bin'] in ['2-3','4+'] for r in eligible)
        diversity=dict(two_evidence_types=sum(v>=3 for v in types.values())>=2,
            no_subject_dominates=bool(eligible) and max(subjects.values())/len(eligible)<=.6,
            nontrivial_depth=bool(eligible) and depth/len(eligible)>=.5)
        strata.append(dict(rule=rule,n=len(rows),eligible=len(eligible),t_correct=t,c_correct=c,forward=forward,reverse=reverse,
            eligibility_rate=len(eligible)/len(rows) if rows else None,
            forward_rate=forward/len(eligible) if eligible else None,
            thinking_accuracy=t/len(eligible) if eligible else None,cot_accuracy=c/len(eligible) if eligible else None,
            informative_yield=forward/len(rows) if rows else 0,
            plan_gate=gate,diversity=diversity,pass_all=gate['pass'] and all(diversity.values()),
            subject_counts=dict(subjects),evidence_type_counts=dict(types),depth_ge2=depth))
    passing=[(i,r) for i,r in enumerate(strata) if r['pass_all']]
    passing.sort(key=lambda ir:(-ir[1]['informative_yield'],-ir[1]['eligible'],ir[0]))
    selected=passing[0][1]['rule'] if passing else None
    fallback=passing[1][1]['rule'] if len(passing)>1 else None
    save(ROOT/'stage11b_selection_rule.json',dict(at=now(),frozen=True,status='GO' if selected else 'NO_GO',
        primary=selected,secondary_fallback=fallback,all_candidate_strata=strata,
        fallback_only_for_insufficient_untouched_family_count=True,heldout_outcomes_opened=False,
        evidence_sha256=sha(ROOT/'annotations/discovery_evidence_final.json'),
        answer_review_sha256=sha(ROOT/'annotations/discovery_answers_final.json')))
    pd.DataFrame(results).to_parquet(ROOT/'stage11b_discovery_mode_results.parquet',index=False)
    save(ROOT/'audit/discovery_scored.json',dict(at=now(),rows=results,all_denominators_preserved=True,
        unscorable_policy='No credit in binary endpoint, separately retained as unscorable; never renamed an observed wrong answer'))
    print('DISCOVERY_DECISION','GO' if selected else 'NO_GO')
    for r in strata:print(r['rule']['id'],r['n'],r['eligible'],r['forward'],r['pass_all'])

if __name__=='__main__':main()
