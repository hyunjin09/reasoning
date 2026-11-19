"""Bounded presentation equivalence of sealed answers; never re-extract by gold."""
import argparse
import re
from scripts.stage14b.common import *
from scripts.stage14b.scoring import guard, metadata, final_extraction, final_score
from scripts.stage14b.protocol import grade


def plain(value):
    s=str(value).strip().strip('*`$ ').strip()
    s=re.sub(r'\s*✅\s*$', '', s).strip().strip('*`$ ').strip()
    return s


def normalized_grade(answer, options, gold):
    s=plain(answer)
    if options:
        m=re.fullmatch(r'\(?([A-Z])\)?\s*[.:]\s*(.+)',s,re.S)
        if m:
            k=ord(m[1])-65
            if not 0<=k<len(options) or plain(m[2]) != plain(options[k]):
                return None
            s=m[1]
        elif re.fullmatch(r'\(?([A-Z])\)?[.]?',s):
            s=re.fullmatch(r'\(?([A-Z])\)?[.]?',s)[1]
    result=grade(s,dict(options=options,gold_answer=gold))
    if result['status'] in ('CORRECT','WRONG'):
        return dict(result,normalized_answer=s)
    return None


def apply(mode,model):
    guard(mode,model)
    seal=ROOT/'audit/grade_presentation_v3a_seal.json'
    for path,expected in load(seal)['files'].items():assert sha(path)==expected
    done=[]
    for t in all_tasks(mode):
        if t['model_key']!=model:continue
        tid=t['task_id']; old=final_score(tid)
        if old['status']!='NEEDS_EQUIVALENCE_REVIEW':continue
        r=checked_result(t);g=load(r.parent/'generation.json')
        if g['finish_reason']!='stop':continue
        x=final_extraction(tid);row=metadata(t)
        result=normalized_grade(x['answer'],row['options'],row['gold_answer'])
        if result is None:continue
        save(ROOT/'scoring/score_reviews'/f'{tid}.json',dict(old,**dict(result,at=now(),
             grader='automatic_presentation_equivalence_v3',original_score_sha256=fingerprint(old),
             repair_seal_sha256=sha(seal),manual_review_claimed=False)))
        done.append(tid)
    save(ROOT/'audit'/f'{mode}_{model}_grade_presentation_v3a.json',dict(at=now(),task_ids=done,
         extraction_unchanged=True,manual_review_claimed=False))
    print('Presentation-equivalent grades',len(done))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode');p.add_argument('model');a=p.parse_args();apply(a.mode,a.model)
