"""Bounded presentation equivalence of sealed answers; never re-extract by gold."""
import argparse
import re
from scripts.stage14b.common import *
from scripts.stage14b.scoring import guard, metadata, final_extraction, final_score
from scripts.stage14b.protocol import grade


def plain(value):
    s=str(value).strip().strip('*` ').strip()
    s=re.sub(r'\s*✅\s*$', '', s).strip().strip('*` ').strip()
    s=s.replace('$','').replace('−','-')
    # Presentation commands only: retain units, signs and grouped mathematics.
    for _ in range(4):
        changed=re.sub(r'\\(?:text|mathrm|mathbf|mathit|operatorname)\{([^{}]*)\}',r'\1',s)
        if changed==s:break
        s=changed
    s=re.sub(r'\\(?:left|right)(?![A-Za-z])','',s)
    s=re.sub(r'\\[,;! ]|~','',s)
    s=re.sub(r'\s+','',s)
    s=re.sub(r'\^\{([0-9])\}',r'^\1',s)
    s=s.replace(r'^{\circ}','°').replace(r'^\circ','°')
    return s


def normalized_grade(answer, options, gold):
    if re.search(r'\d\s+\d',str(answer)):return None
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
    result=grade(s,dict(options=[plain(v) for v in options],gold_answer=plain(gold)))
    if result['status'] in ('CORRECT','WRONG'):
        return dict(result,normalized_answer=s)
    return None


def apply(mode,model):
    guard(mode,model)
    seal=ROOT/'audit/grade_presentation_v4_seal.json'
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
             grader='automatic_presentation_equivalence_v4',original_score_sha256=fingerprint(old),
             repair_seal_sha256=sha(seal),manual_review_claimed=False)))
        done.append(tid)
    save(ROOT/'audit'/f'{mode}_{model}_grade_presentation_v4.json',dict(at=now(),task_ids=done,
         extraction_unchanged=True,manual_review_claimed=False))
    print('Presentation-equivalent grades',len(done))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode');p.add_argument('model');a=p.parse_args();apply(a.mode,a.model)
