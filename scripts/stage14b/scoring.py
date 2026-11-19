"""Versioned raw freeze, response-only extraction, arm-separated score review."""
import argparse
from functools import lru_cache
from collections import Counter
from scripts.stage14b.common import *
from scripts.stage14b.protocol import extract,grade
from scripts.stage14b.validate import checked


@lru_cache(maxsize=3)
def metadata_index(name):
    return {r['identity']:r for r in rows(ROOT/'manifests'/f'{name}.jsonl')}

def metadata(task):
    name='mathverse_788_eval_manifest' if task['identity'].startswith('verse:') else 'mathvision_e1000_eval_manifest' if task['condition']=='evidence' else 'mathvision_3040_eval_manifest'
    return metadata_index(name)[task['identity']]

def guard(mode,model):
    assert mode in ('main','confirmatory') and model in 'IT'
    assert (ROOT/'audit'/f'{mode}_raw_seal.json').exists()
    if model=='T':assert (ROOT/'audit'/f'{mode}_I_scoring_seal.json').exists(),'Close Instruct scoring/QC before paired-model scoring'

def raw_freeze(mode):
    tasks=all_tasks(mode);receipts={};missing=[]
    for t in tasks:
        p=checked_result(t)
        if p:
            checked(t);receipts[str(p)]=sha(p)
        else:
            p=ROOT/'scoring/technical_missingness'/f"{t['task_id']}.json"
            assert p.exists(),('unfinished authorized call',t['task_id'])
            r=load(p);assert r['task_sha256']==fingerprint(t) and r['final_technical_failure']
            receipts[str(p)]=sha(p);missing.append(t['task_id'])
    save(ROOT/'audit'/f'{mode}_raw_seal.json',dict(at=now(),expected=len(tasks),files=receipts,technical_missing=missing))

def extract_arm(mode,model):
    guard(mode,model);count=Counter()
    cache={name:{r['identity']:r for r in rows(ROOT/'manifests'/f'{name}.jsonl')} for name in ['mathvision_3040_eval_manifest','mathvision_e1000_eval_manifest','mathverse_788_eval_manifest']}
    for t in all_tasks(mode):
        if t['model_key']!=model:continue
        p=ROOT/'scoring/extraction'/f"{t['task_id']}.json"
        if p.exists():continue
        result=checked(t)
        if result is None:x=dict(answer=None,status='TECHNICAL_MISSING',method=None)
        else:
            name='mathverse_788_eval_manifest' if t['identity'].startswith('verse:') else 'mathvision_e1000_eval_manifest' if t['condition']=='evidence' else 'mathvision_3040_eval_manifest'
            row=cache[name][t['identity']];g=result['generation']
            x=extract(g['raw_decoded_response'],row['options'],model,g['finish_reason'])
        save(p,dict(at=now(),task_id=t['task_id'],task_sha256=fingerprint(t),**x,correctness_used=False,
            generation_sha256=sha(Path(result['receipt']).parent/'generation.json') if result else None))
        count[x['status']]+=1
    print(dict(count))

def final_extraction(tid):
    p=ROOT/'scoring/extraction_reviews'/f'{tid}.json'
    return load(p if p.exists() else ROOT/'scoring/extraction'/f'{tid}.json')

def extraction_review(tid,answer,status,reason):
    old=load(ROOT/'scoring/extraction'/f'{tid}.json')
    assert status in ('EXTRACTED','UNSCORABLE','NO_ANSWER')
    assert (answer is None)==(status=='UNSCORABLE')
    assert bool(reason.strip())
    save(ROOT/'scoring/extraction_reviews'/f'{tid}.json',dict(old,at=now(),answer=answer,status=status,method='same_agent_response_only_review',reason=reason,
        original_extraction_sha256=sha(ROOT/'scoring/extraction'/f'{tid}.json'),correctness_used=False))

def score_arm(mode,model):
    guard(mode,model);selected=[t for t in all_tasks(mode) if t['model_key']==model]
    for t in selected:
        x=final_extraction(t['task_id'])
        assert not x['status'].startswith('NEEDS_'),('response-only review pending',t['task_id'])
    seal=ROOT/'audit'/f'{mode}_{model}_extraction_seal.json'
    if not seal.exists():save(seal,dict(at=now(),tasks={t['task_id']:fingerprint(final_extraction(t['task_id'])) for t in selected},correctness_used=False))
    count=Counter()
    for t in selected:
        p=ROOT/'scoring/first_scores'/f"{t['task_id']}.json"
        if p.exists():continue
        x=final_extraction(t['task_id']);r=metadata(t)
        if x['status']=='TECHNICAL_MISSING':s=dict(correct=None,status='TECHNICAL_MISSING')
        elif x['answer'] is None:s=dict(correct=None,status='UNSCORABLE')
        else:s=grade(x['answer'],r)
        save(p,dict(at=now(),task_id=t['task_id'],model=model,**s,extraction_sha256=fingerprint(x)))
        count[s['status']]+=1
    print(dict(count))

def final_score(tid):
    p=ROOT/'scoring/score_reviews'/f'{tid}.json'
    return load(p if p.exists() else ROOT/'scoring/first_scores'/f'{tid}.json')

def audit_selection(mode,model):
    selected=[t for t in all_tasks(mode) if t['model_key']==model];groups={}
    for t in selected:groups.setdefault((t['identity'].split(':')[0],t['condition']),[]).append(t)
    audit=[]
    for group in groups.values():
        ordered=sorted(group,key=lambda t:fingerprint(['stage14b-v1-score-audit',t['task_id']]))
        audit.extend(t['task_id'] for t in ordered[:max(1,(len(group)+9)//10)])
    for t in selected:
        x=final_extraction(t['task_id']);s=final_score(t['task_id'])
        if x['method']=='same_agent_response_only_review' or s['status']=='NEEDS_EQUIVALENCE_REVIEW':audit.append(t['task_id'])
    return sorted(set(audit))

def close_arm(mode,model):
    guard(mode,model);selected=[t for t in all_tasks(mode) if t['model_key']==model];files={}
    for t in selected:
        s=final_score(t['task_id']);assert s['status'] in ('CORRECT','WRONG','UNSCORABLE','TECHNICAL_MISSING')
        assert (s['correct'] is None)==(s['status'] in ('UNSCORABLE','TECHNICAL_MISSING'))
        files[t['task_id']]=fingerprint(s)
    for tid in audit_selection(mode,model):
        p=ROOT/'scoring/qc'/f'{tid}.json';r=load(p)
        assert r['resolved'] and r['final_score_sha256']==fingerprint(final_score(tid)),tid
    save(ROOT/'audit'/f'{mode}_{model}_scoring_seal.json',dict(at=now(),n=len(selected),scores=files,audit_task_ids=audit_selection(mode,model),
        qc_scope='Same-agent arm-separated review, not independent human reliability'))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['raw_freeze','extract','score','close']);p.add_argument('mode');p.add_argument('--model',default='I')
    a=p.parse_args()
    if a.action=='raw_freeze':raw_freeze(a.mode)
    elif a.action=='extract':extract_arm(a.mode,a.model)
    elif a.action=='score':score_arm(a.mode,a.model)
    else:close_arm(a.mode,a.model)
