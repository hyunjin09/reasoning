"""Open original answer labels only after native and probe annotations are sealed."""
import os,json
from collections import Counter
import pandas as pd
from scripts.stage11a.common import ROOT,OLD,ARMS,load,save,sha,now
from scripts.stage11a.protocol import profile,probe_state,localization
from scripts.stage11a.review_validation import validate_native,validate_probe

def table(rows,path):
    assert not path.exists()
    pd.DataFrame([{k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in r.items()} for r in rows]).to_parquet(path,index=False)

assert os.environ.get('SLURM_JOB_ID')
native=load(ROOT/'annotations/native_final.json');probes=load(ROOT/'annotations/probe_final.json')
assert native['sealed'] and probes['sealed']
nrows={r['packet_id']:r for r in native['rows']};prows={r['packet_id']:r for r in probes['rows']}
nkey=load(ROOT/'audit/native_key.json');pkey=load(ROOT/'audit/probe_review_key.json')
assignment=load(ROOT/'audit/native_reviewer_assignment_v2.json');actual_owners={}
for who,path in assignment['assignments'].items():
    for r in load(path)['rows']:actual_owners.setdefault(r['packet_id'],[]).append(who)
assert set(nrows)=={r['packet_id'] for r in nkey['rows']}
assert set(prows)=={r['packet_id'] for r in pkey['rows']}
gold={r['item_id']:r for r in load(ROOT/'audit/e_star_gold.json')['rows']}
packet={r['packet_id']:r for r in load(ROOT/'packets/probe_review.json')['rows']}
joined_probes={};pr=[]
for key in pkey['rows']:
    r=prows[key['packet_id']];g=gold[key['item_id']]
    validate_probe(r,packet[key['packet_id']])
    assert {x['fact_id'] for x in r['facts']}=={f['fact_id'] for f in g['facts']}
    for x in r['facts']:
        assert x['reason']
        for q in x.get('quotes',[]):assert q in packet[key['packet_id']]['text'],key
    state=probe_state([x['label'] for x in r['facts']]);receipt=load(key['receipt_path'])
    assert sha(key['receipt_path'])==key['receipt_sha256']
    rr=dict(key,probe=state,facts=r['facts'],normal_eos=receipt['normal_eos'],at_length_cap=receipt['at_length_cap'],tokens=receipt['tokens'])
    pr.append(rr);joined_probes[key['task_id']]=rr
# This is the first correctness join. Source extraction/scoring remains unchanged.
answer_path=OLD/'stage9a_accuracy_secondary.json';answers={r['task_id']:r for r in load(answer_path)['rows']}
rows=[];nr=[]
for key in nkey['rows']:
    r=nrows[key['packet_id']];p=load(ROOT/'packets/native'/f"{key['packet_id']}.json")
    validate_native(r,p)
    assert r['coverage_complete'] and r['state'] in ['N0','N1','N2','N3','N4','N5'] and r['reason']
    for q in r.get('evidence_quotes',[]):assert q in p['reasoning_text'],key
    assert {x['fact_id'] for x in r['facts']}=={f['fact_id'] for f in gold[key['item_id']]['facts']}
    a=answers[key['task_id']]['reviewed']['benchmark_label']
    outcome={'correct':'FINAL_CORRECT','wrong':'FINAL_WRONG','unscorable':'NO_VALID_FINAL'}[a]
    ps=joined_probes.get(key['task_id'],{}).get('probe','PROBE_NOT_RUN')
    label,flags=profile(ps,r['state'],outcome)
    annotated_key=dict(key,owners_original=key['owners'],owners=actual_owners[key['packet_id']],
        assignment_sha256=sha(ROOT/'audit/native_reviewer_assignment_v2.json'))
    nr.append(dict(annotated_key,**{k:v for k,v in r.items() if k!='packet_id'}))
    rows.append(dict(item_id=key['item_id'],family_id=key['family_id'],arm=key['arm'],packet_id=key['packet_id'],
        native=r['state'],probe=ps,final=outcome,profile=label,profile_flags=flags,probed=ps!='PROBE_NOT_RUN',
        subject=gold[key['item_id']]['subject'],evidence_type=gold[key['item_id']]['facts'][0]['evidence_type'],
        n_facts=len(gold[key['item_id']]['facts']),reasoning_tokens=key['reasoning_tokens'],
        first_evidence_token=r.get('first_evidence_token'),first_sufficient_token=r.get('first_sufficient_token'),native_review=r,answer_source_sha256=sha(answer_path)))
assert len(rows)==3*len(gold)
paired={i:{r['arm']:r for r in rows if r['item_id']==i} for i in gold}
discordances=[]
for i,modes in paired.items():
    if not modes['thinking']['probed']:continue
    t,c=modes['thinking'],modes['instruct_cot'];forward=t['final']=='FINAL_CORRECT' and c['final']!='FINAL_CORRECT';reverse=c['final']=='FINAL_CORRECT' and t['final']!='FINAL_CORRECT'
    category,flags=localization(t,c) if forward else localization(c,t) if reverse else ('NOT_DISCORDANT',[])
    discordances.append(dict(item_id=i,family_id=t['family_id'],direction='THINKING_GAIN' if forward else 'COT_GAIN' if reverse else 'CONCORDANT',
        category=category,category_flags=flags,thinking={k:t[k] for k in ['probe','native','final']},cot={k:c[k] for k in ['probe','native','final']},
        subject=t['subject'],evidence_type=t['evidence_type'],n_facts=t['n_facts']))
table(nr,ROOT/'stage11a_native_evidence_states.parquet');table(pr,ROOT/'stage11a_probe_results.parquet');table(rows,ROOT/'stage11a_bottleneck_profiles.parquet')
save(ROOT/'audit/census_joined.json',dict(at=now(),sealed=True,rows=rows,discordances=discordances,
    sources_sha256={str(p):sha(p) for p in [ROOT/'annotations/native_final.json',ROOT/'annotations/probe_final.json',answer_path,ROOT/'audit/e_star_gold.json']}))
agreement=set(nkey['agreement_item_ids'])
save(ROOT/'packets/localization_agreement.json',dict(at=now(),rows=[dict(item_id=i,thinking={k:paired[i]['thinking'][k] for k in ['probe','native','final']},cot={k:paired[i]['instruct_cot'][k] for k in ['probe','native','final']}) for i in sorted(agreement)],
    instruction='Apply the frozen rule independently. THINKING_GAIN/COT_GAIN/CONCORDANT and A/B/C/D/NOT_DISCORDANT. PROBE_NOT_RUN is unavailable measurement, not probe failure. No aggregate or other annotation exposed.'))
print('SEALED_JOIN',len(rows),'mode-item profiles;',len(discordances),'probed matched families; localization agreement pending')
