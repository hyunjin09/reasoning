"""Immutable D1 packets and two-pass explicit source-semantic review receipts."""
import argparse
from scripts.stage14c.common import *
from scripts.stage14c.preflight import checked
from scripts.stage14c.oom_policy import missing_path
from scripts.stage14c.d1_scoring_v2 import validate_review,metrics
from scripts.stage14c.review_packets import response_view


def raw_freeze_instruct():
    assert (ROOT/'audit/primary_summary_seal.json').exists()
    selected=[t for t in all_tasks('D1') if t['model_key']=='I'];assert len(selected)==300
    files={};missing=[]
    for t in selected:
        c=checked(t)
        if c:p=c[0]
        else:
            p=missing_path(t);r=load(p)
            assert r['task_sha256']==fingerprint(t) and r['final_technical_failure']
            missing.append(t['task_id'])
        files[str(p)]=sha(p)
    save(ROOT/'audit/D1_I_raw_seal.json',dict(at=now(),files=files,expected=300,technical_missing=missing,
        scope='Completed Instruct D1 arm only; paired analysis still requires global raw and scoring seals.'))


def guard(model):
    assert model in {'I','T'}
    assert (ROOT/'audit/D1_raw_seal.json').exists() or (model=='I' and (ROOT/'audit/D1_I_raw_seal.json').exists())


def raw_freeze():
    assert (ROOT/'audit/primary_summary_seal.json').exists()
    files={};missing=[]
    for t in all_tasks('D1'):
        c=checked(t)
        if c:p=c[0]
        else:
            p=missing_path(t);r=load(p)
            assert r['task_sha256']==fingerprint(t) and r['final_technical_failure']
            missing.append(t['task_id'])
        files[str(p)]=sha(p)
    save(ROOT/'audit/D1_raw_seal.json',dict(at=now(),files=files,expected=600,technical_missing=missing))


def packet(model,review_pass,start,count):
    guard(model)
    targets={r['family_id']:r for r in rows(ROOT/'source/D1_review_schema_v1.jsonl')}
    tasks=[t for t in all_tasks('D1') if t['model_key']==model]
    tasks=[t for t in tasks if not (ROOT/f'scoring/D1_pass{review_pass}'/f"{t['task_id']}.json").exists()]
    out=[]
    for t in tasks[start:start+count]:
        c=checked(t);r=dict(task=t,source_target=targets[t['family_id']],
                           raw_generation_path=str(c[0].parent/'generation.json') if c else None)
        if c:r.update(response_view(c[2]['raw_decoded_response'],model),cap_hit=c[2]['cap_hit'],tokens=c[2]['tokens'])
        if review_pass==2:r['first_review']=load(ROOT/'scoring/D1_pass1'/f"{t['task_id']}.json")
        out.append(r)
    return dict(at=now(),model=model,review_pass=review_pass,remaining=len(tasks),rows=out)


def apply(path):
    batch=load(path);model=batch['model'];rp=batch['review_pass'];assert rp in {1,2}
    guard(model)
    targets={r['family_id']:r for r in rows(ROOT/'source/D1_review_schema_v1.jsonl')}
    tasks={t['task_id']:t for t in all_tasks('D1') if t['model_key']==model}
    assert len({r['task_id'] for r in batch['rows']})==len(batch['rows'])
    for r in batch['rows']:
        t=tasks[r['task_id']];target=targets[t['family_id']]
        assert r['source_semantic_reviewed'] is True and r['target_sha256']==fingerprint(target)
        validate_review(target,r['review'])
        c=checked(t)
        if c:
            assert r['generation_sha256']==sha(c[0].parent/'generation.json')
            raw=c[2]['raw_decoded_response'];body=raw.rsplit('</think>',1)[-1]
            assert r['review']['status']!='TECHNICAL_MISSING'
            if model=='T' and '</think>' not in raw:assert r['review']['status']=='UNRESOLVED'
            if r['review']['status']=='SCORED':
                assert all(q in body for a in r['review']['atoms'] for q in a['evidence_quotes'])
                assert all(q['text'] in body for q in r['review']['claims'])
        else:assert r['review']['status']=='TECHNICAL_MISSING' and missing_path(t).exists()
        if rp==2:
            first=load(ROOT/'scoring/D1_pass1'/f"{t['task_id']}.json")
            assert r['first_review_sha256']==fingerprint(first) and r['reread_response_and_source'] is True
        assert not (ROOT/f'scoring/D1_pass{rp}'/f"{t['task_id']}.json").exists()
    for r in batch['rows']:
        save(ROOT/f'scoring/D1_pass{rp}'/f"{r['task_id']}.json",dict(r,at=now(),review_pass=rp,
             reviewer='main_agent',independent_interrater_review=False,batch_sha256=sha(path)))


def close():
    assert (ROOT/'audit/D1_raw_seal.json').exists()
    targets={r['family_id']:r for r in rows(ROOT/'source/D1_review_schema_v1.jsonl')};out=[];files={}
    for t in all_tasks('D1'):
        ps=[ROOT/f'scoring/D1_pass{rp}'/f"{t['task_id']}.json" for rp in [1,2]]
        first,second=map(load,ps);assert second['first_review_sha256']==fingerprint(first)
        target=targets[t['family_id']]
        out.append(dict(task_id=t['task_id'],benchmark=t['benchmark'],family_id=t['family_id'],model=t['model_key'],
                   **metrics(target,second['review'])))
        files.update({str(p):sha(p) for p in ps})
    write_rows(ROOT/'scoring/D1_scored_outcomes.jsonl',out)
    files[str(ROOT/'scoring/D1_scored_outcomes.jsonl')]=sha(ROOT/'scoring/D1_scored_outcomes.jsonl')
    save(ROOT/'audit/D1_scoring_seal.json',dict(at=now(),files=files,same_agent_two_pass=True,independent_reliability=False))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['raw_freeze','packet','apply','close'])
    p.add_argument('--model',choices=['I','T']);p.add_argument('--review-pass',type=int,choices=[1,2],default=1)
    p.add_argument('--start',type=int,default=0);p.add_argument('--count',type=int,default=10);p.add_argument('--path')
    a=p.parse_args()
    if a.action=='raw_freeze':raw_freeze()
    elif a.action=='packet':
        value=packet(a.model,a.review_pass,a.start,a.count)
        if a.path:save(a.path,value)
        else:print(json.dumps(value,ensure_ascii=False,indent=2))
    elif a.action=='apply':apply(a.path)
    else:close()
