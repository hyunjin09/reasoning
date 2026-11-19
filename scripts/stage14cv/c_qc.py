"""Explicit fixed-sample and flagged-response QC; no automatic confirmations."""
import argparse
from scripts.stage14cv.common import *
from scripts.stage14cv.c_review import targets, validate_decision
from scripts.stage14c.d1_scoring_v2 import metrics


def packet():
    for name in ['C_raw_seal_v1.json','C_contract_modes_seal_v1.json','C_fidelity_scoring_seal_v1.json']:
        for p,h in load(ROOT/'audit'/name)['files'].items():assert sha(p)==h,p
    by={t['task_id']:t for t in tasks('C')};target=targets()
    selected={r['task_id'] for r in rows(ROOT/'scoring/fixed_hash_review_qc.jsonl') if r['task_id'] in by}
    assert len(selected)==80
    index=rows(ROOT/'scoring/C_response_index_v1.jsonl');out=[]
    for r in index:
        tid=r['task_id'];t=by[tid]
        first=load(ROOT/'scoring/C_fidelity_pass1'/f'{tid}.json')
        second=load(ROOT/'scoring/C_fidelity_pass2'/f'{tid}.json')
        mode=load(ROOT/'scoring/C_contract_modes'/f'{tid}.json')
        fixed=tid in selected
        flagged=r['cap_hit'] or not r['closed'] or second['review']['status']!='SCORED' or mode['mode']=='UNRESOLVED'
        disagreement=first['review']!=second['review']
        if not (fixed or flagged or disagreement):continue
        out.append(dict(r,source_target=target[t['family_id']],image_reference=t['image_reference'],
            image_sha256=t['image_sha256'],mode=mode,review=second,
            first_review=first if disagreement else None,
            fixed_hash_selected=fixed,flagged=flagged,pass_disagreement=disagreement))
    save(ROOT/'scoring/C_QC_packet_v1.json',dict(at=now(),rows=out,fixed_tasks=80,
         model_and_condition_hidden_in_display=True,same_agent_review=True))
    print('C QC records',len(out))


def apply(path):
    packet_path=ROOT/'scoring/C_QC_packet_v1.json'
    groups={r['review_id']:r for r in load(packet_path)['rows']}
    batch=load(path);assert batch['packet_sha256']==sha(packet_path)
    assert len(batch['decisions'])==len(groups)
    assert {d['review_id'] for d in batch['decisions']}==set(groups)
    scored={r['task_id']:r for r in rows(ROOT/'scoring/C_scored_outcomes.jsonl')};files={}
    for d in batch['decisions']:
        assert d['confirmed'] is True and d['reread_response_and_source'] is True and d['reason'].strip()
        r=groups[d['review_id']];tid=r['task_id'];rv=r['review']['review']
        validate_decision(r['source_target'],rv,r['body'])
        expected=metrics(r['source_target'],rv)
        assert all(scored[tid][k]==v for k,v in expected.items())
        p=ROOT/'scoring/C_fixed_QC'/f'{tid}.json'
        save(p,dict(d,at=now(),task_id=tid,packet_sha256=sha(packet_path),
             mode_sha256=fingerprint(r['mode']),fidelity_review_sha256=fingerprint(r['review']),
             reviewer='main_agent',independent_interrater_reliability=False))
        files[str(p)]=sha(p)
    files[str(packet_path)]=sha(packet_path);files[str(path)]=sha(path)
    save(ROOT/'audit/C_fixed_QC_seal_v1.json',dict(at=now(),files=files,fixed_tasks=80,
         reviewed_tasks=len(groups),same_agent_QC=True,independent_interrater_reliability=False))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['packet','apply']);p.add_argument('--path');a=p.parse_args()
    if a.action=='packet':packet()
    else:apply(a.path)
