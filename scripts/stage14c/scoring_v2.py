"""Immutable response extraction, explicit semantic reviews, and strict source scoring."""
import argparse
from functools import lru_cache
from scripts.stage14c.common import *
from scripts.stage14c.preflight import checked
from scripts.stage14c.response_protocol_v2 import extract,repetition
from scripts.stage14c.design_core import score_final
from scripts.stage14c.oom_policy import missing_path

@lru_cache(maxsize=1)
def source():return {r['family_id']:r for r in rows(ROOT/'source/cohort_manifest.jsonl')}
@lru_cache(maxsize=1)
def eligibility():return {r['family_id']:r for r in rows(ROOT/'source/estar_eligibility_manifest.jsonl')}

def raw_freeze():
    files={};missing=[]
    for t in all_tasks('main'):
        c=checked(t)
        if c:p=c[0]
        else:
            p=missing_path(t);r=load(p)
            assert r['task_sha256']==fingerprint(t) and r['final_technical_failure'];missing.append(t['task_id'])
        files[str(p)]=sha(p)
    save(ROOT/'audit/main_raw_seal.json',dict(at=now(),files=files,expected=4588,technical_missing=missing))

def guard(model):
    assert (ROOT/'audit/main_raw_seal.json').exists()
    if model=='T':assert (ROOT/'audit/main_I_scoring_seal.json').exists()

def extract_arm(model):
    guard(model)
    for t in all_tasks('main'):
        if t['model_key']!=model:continue
        p=ROOT/'scoring/extraction'/f"{t['task_id']}.json"
        if p.exists():continue
        c=checked(t)
        x=extract(c[2]['raw_decoded_response'],model,t['answer_kind'],c[2]['finish_reason'],source()[t['family_id']]['question']) if c else dict(answer=None,status='TECHNICAL_MISSING',committed=False,needs_review=False)
        save(p,dict(at=now(),task_id=t['task_id'],task_sha256=fingerprint(t),extraction=x,
                    repetition=repetition(c[2]['generated_token_ids']) if c else None,
                    generation_sha256=sha(c[0].parent/'generation.json') if c else None,correctness_used=False))

def final_extraction(tid):
    p=ROOT/'scoring/extraction_reviews'/f'{tid}.json'
    return load(p) if p.exists() else load(ROOT/'scoring/extraction'/f'{tid}.json')

def extraction_review(tid,answer,status,reason):
    assert status in ['EXTRACTED','UNSCORABLE','NO_ANSWER'] and reason.strip()
    assert (answer is not None)==(status=='EXTRACTED')
    p=ROOT/'scoring/extraction'/f'{tid}.json';original=load(p)
    save(ROOT/'scoring/extraction_reviews'/f'{tid}.json',dict(original,at=now(),
        extraction=dict(answer=answer,status=status,committed=status=='EXTRACTED',needs_review=False),
        reason=reason,original_sha256=sha(p),reviewer='main_agent',correctness_used=False))

def score_arm(model):
    guard(model)
    selected=[t for t in all_tasks('main') if t['model_key']==model]
    for t in selected:
        x=final_extraction(t['task_id'])['extraction']
        assert not x.get('needs_review'),t['task_id']
    for t in selected:
        p=ROOT/'scoring/first_scores'/f"{t['task_id']}.json"
        if p.exists():continue
        x=final_extraction(t['task_id'])['extraction'];c=source()[t['family_id']]
        if x['status']=='TECHNICAL_MISSING':status='TECHNICAL_MISSING'
        elif x['status']=='NO_ANSWER':status='WRONG'
        else:status=score_final(x['answer'],c['gold'],t['answer_kind'],['A','B','C','D'])
        save(p,dict(at=now(),task_id=t['task_id'],model=model,status=status,answer=x['answer'],
                    extraction_sha256=fingerprint(final_extraction(t['task_id'])),native_gold_unchanged=True))

def final_score(tid):
    p=ROOT/'scoring/score_reviews'/f'{tid}.json'
    return load(p) if p.exists() else load(ROOT/'scoring/first_scores'/f'{tid}.json')

def audit_selection(model):
    selected=[t for t in all_tasks('main') if t['model_key']==model];groups={};chosen=set()
    for t in selected:groups.setdefault((t['benchmark'],t['condition']),[]).append(t)
    for group in groups.values():
        ranked=sorted(group,key=lambda t:fingerprint(['stage14c-v1-score-audit',t['task_id']]))
        chosen.update(t['task_id'] for t in ranked[:(len(group)+9)//10])
    for t in selected:
        x=load(ROOT/'scoring/extraction'/f"{t['task_id']}.json");c=checked(t)
        if (x['extraction']['status'] not in ['EXTRACTED','TECHNICAL_MISSING'] or x['extraction'].get('needs_review')
            or (c and c[2]['cap_hit']) or eligibility()[t['family_id']]['source_validity_flags']
            or final_score(t['task_id'])['status'] in ['REVIEW','SOURCE_REVIEW']):chosen.add(t['task_id'])
    return sorted(chosen)

def close(model):
    guard(model);files={}
    for t in all_tasks('main'):
        if t['model_key']!=model:continue
        s=final_score(t['task_id']);assert s['status'] in ['CORRECT','WRONG','UNSCORABLE','TECHNICAL_MISSING']
        files[t['task_id']]=fingerprint(s)
    audit=audit_selection(model)
    for tid in audit:
        q=load(ROOT/'scoring/qc'/f'{tid}.json')
        assert q['resolved'] and q['score_sha256']==fingerprint(final_score(tid))
    save(ROOT/'audit'/f'main_{model}_scoring_seal.json',dict(at=now(),scores=files,audit_task_ids=audit,same_agent_review=True))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['raw_freeze','extract','score','close']);p.add_argument('--model',choices=['I','T']);a=p.parse_args()
    if a.action=='raw_freeze':raw_freeze()
    elif a.action=='extract':extract_arm(a.model)
    elif a.action=='score':score_arm(a.model)
    else:close(a.model)
