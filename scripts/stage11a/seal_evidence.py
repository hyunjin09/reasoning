"""Seal adjudicated image evidence before any native correctness or probe outcomes."""
import os,json
from pathlib import Path
import pandas as pd
from scripts.stage11a.common import ROOT,OLD,ARMS,load,save,sha,now
from scripts.stage11a.protocol import order,select_probes
from visual_reasoning.stage9a.protocol import prompt

assert os.environ.get('SLURM_JOB_ID')
proposal=ROOT/'audit/e_star_proposal.json';draft=load(proposal)
final=load(ROOT/'audit/e_star_adjudication.json');assert final['sealed'] and final['model_outcomes_opened'] is False
assert len(final['rows'])==len({r['item_id'] for r in final['rows']})==128
reviews={who:load(ROOT/'annotations'/f'sufficiency_{who}.json') for who in ['a','b']}
for v in reviews.values():assert v['sealed'] and v['proposal_sha256']==sha(proposal)
repair_path=ROOT/'audit/e_star_repair_proposal_v1.json';repairs=load(repair_path)
repair_reviews={who:load(ROOT/'annotations'/f'repair_sufficiency_{who}.json') for who in ['a','b']}
for v in repair_reviews.values():assert v['sealed'] and v['proposal_sha256']==sha(repair_path) and v['model_outcomes_opened'] is False
repaired={r['item_id']:r for r in repairs['rows']}
repair2_path=ROOT/'audit/e_star_repair_proposal_v2.json';repairs2=load(repair2_path)
repair2_reviews={who:load(ROOT/'annotations'/f'repair2_sufficiency_{who}.json') for who in ['a','b']}
for v in repair2_reviews.values():assert v['sealed'] and v['proposal_sha256']==sha(repair2_path) and v['model_outcomes_opened'] is False
repaired2={r['item_id']:r for r in repairs2['rows']}
source={r['item_id']:r for r in load(ROOT/'packets/evidence_construction.json')['rows']}
eligible=[]
for r in final['rows']:
    assert r['item_id'] in source and r['image_inspected']
    if r['eligibility']!='E_STAR_ELIGIBLE':continue
    assert r['sufficiency']=='SUFFICIENT' and 1<=len(r['facts'])<=4
    assert len({f['fact_id'] for f in r['facts']})==len(r['facts'])
    for who in ['a','b']:
        v=repair2_reviews[who] if r['item_id'] in repaired2 else repair_reviews[who] if r['item_id'] in repaired else reviews[who]
        checked=next(x for x in v['rows'] if x['item_id']==r['item_id'])
        assert checked['sufficiency']=='SUFFICIENT' and checked['proposed_eligibility_supported'] and checked['gold_truth_ok'] and checked['probe_no_leak'],(who,r['item_id'])
    checked_row=repaired2.get(r['item_id'],repaired.get(r['item_id'],next(x for x in draft['rows'] if x['item_id']==r['item_id'])))
    assert r['facts']==checked_row['facts'],'No unreviewed fact edits after the independent checks'
    for f in r['facts']:
        assert all(k in f for k in ['fact_id','evidence_type','source_ref','roi_normalized','gold_value','accepted_paraphrases','exact_lexical_required','visibility','probe_request'])
        assert f['probe_request'] and f['source_ref']
    eligible.append(dict(r,subject=source[r['item_id']]['subject']))
save(ROOT/'stage11a_e_star_eligibility.json',dict(at=now(),sealed=True,rows=final['rows'],model_outcomes_opened=False,
    construction_review_sha256={w:sha(ROOT/'annotations'/f'e_star_{w}.json') for w in ['a','b']},adjudication_sha256=sha(ROOT/'audit/e_star_adjudication.json')))
save(ROOT/'audit/e_star_gold.json',dict(at=now(),sealed=True,rows=eligible,model_outcomes_opened=False))
save(ROOT/'stage11a_e_star_sufficiency_review.json',dict(at=now(),reviews=reviews,proposal_sha256=sha(proposal),repair_reviews=repair_reviews,
    repair_proposal_sha256=sha(repair_path),repair2_reviews=repair2_reviews,repair2_proposal_sha256=sha(repair2_path),adjudication=final,
    independent_review='Two model-agent passes; no human-reliability claim.',model_outcomes_opened=False))
flat=[dict(item_id=r['item_id'],family_id=r['family_id'],subject=r['subject'],**f) for r in eligible for f in r['facts']]
pd.DataFrame([{k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in r.items()} for r in flat]).to_parquet(ROOT/'stage11a_e_star_gold.parquet',index=False)
chosen=select_probes([dict(item_id=r['item_id'],subject=r['subject'],evidence_type=r['facts'][0]['evidence_type']) for r in eligible])
by={r['item_id']:r for r in eligible};original={r['item_id']:r for r in load(OLD/'stage9a_cohort_manifest.json')['rows']}
tasks=[]
for ident in chosen:
    r=by[ident];s=source[ident]
    request='Inspect the image and report only the following task-relevant visual facts. Do not solve the original problem. Report each requested fact by its number.\n\nProblem context:\n'+s['question']+'\n\nRequested visual facts:\n'+'\n'.join(f"{i+1}. {f['probe_request']}" for i,f in enumerate(r['facts']))
    for arm in ARMS:
        tasks.append(dict(item_id=ident,family_id=s['family_id'],arm=arm,model_key='thinking' if arm=='thinking' else 'instruct',task_id=f'{arm}_{ident}',
            image=s['image'],image_sha256=s['image_sha256'],question=request,generation_query=prompt(request,arm),seed=original[ident]['seed']))
save(ROOT/'stage11a_probe_manifest.json',dict(at=now(),frozen=True,eligible_item_ids=[r['item_id'] for r in eligible],selected_item_ids=chosen,rows=tasks,
    selection='All eligible if<=64; otherwise fixed-seed largest-remainder subject/primary-evidence-type strata.',
    gold_sha256=sha(ROOT/'audit/e_star_gold.json'),model_outcomes_used=False,max_new_tokens=512))
old=load(OLD/'stage9a_generation_config.json')
frozen=[ROOT/'stage11a_probe_manifest.json',ROOT/'audit/e_star_gold.json',ROOT/'stage11a_e_star_eligibility.json',ROOT/'stage11a_e_star_sufficiency_review.json',ROOT/'stage11a_bottleneck_census_spec.md']
code=['scripts/stage11a/probe_worker.py','scripts/stage11a/protocol.py','scripts/stage11a/run.sh','code/visual_reasoning/stage0/modeling.py','code/visual_reasoning/stage8b/v2_protocol.py','code/visual_reasoning/stage9a/protocol.py']
save(ROOT/'probe_config.json',dict(at=now(),models=old['models'],generation_parameters=old['generation_parameters'],max_new_tokens=512,
    manifest_sha256=sha(ROOT/'stage11a_probe_manifest.json'),frozen_artifact_sha256={str(p):sha(p) for p in frozen},source_sha256={p:sha(p) for p in code},
    primary_target_gpu_hours=1.5,total_hard_gpu_hours=2.5,optional_target_gpu_hours=.5,authorized_max_gpus=8))
(ROOT/'probes/claims').mkdir(parents=True,exist_ok=True)
print('SEALED',len(eligible),'eligible;',len(chosen),'probed;',len(tasks),'runs; no model outcomes opened')
