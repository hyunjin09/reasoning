"""Fixed R scoring audit, displayed without model/condition labels."""
import argparse
from scripts.stage14cv.common import *
from scripts.stage14cv.r_scoring import cohort


def packet():
    selected={r['task_id'] for r in rows(ROOT/'scoring/fixed_hash_review_qc.jsonl') if r['task_id'].split('_')[1].startswith('R')}
    for t in tasks('R'):
        x=load(ROOT/'scoring/R_extraction'/f"{t['task_id']}.json")
        if x['cap_hit'] or x['extraction']['status']!='EXTRACTED' or x['extraction'].get('needs_review'):selected.add(t['task_id'])
    c=cohort();by={t['task_id']:t for t in tasks('R')};groups={}
    for tid in sorted(selected):
        s=load(ROOT/'scoring/R_scores'/f'{tid}.json');source=c[by[tid]['family_id']]['source']
        value=dict(answer=s['answer'],status=s['status'],gold=source['gold'],question=source['question'])
        key=fingerprint(value)
        if key not in groups:groups[key]=dict(review_id=key,**value,task_ids=[])
        groups[key]['task_ids'].append(tid)
    save(ROOT/'scoring/R_gold_QC_packet_v1.json',dict(at=now(),groups=list(groups.values()),tasks=len(selected)))


def apply(path):
    gs={g['review_id']:g for g in load(ROOT/'scoring/R_gold_QC_packet_v1.json')['groups']}
    decisions=load(path)['decisions'];assert {d['review_id'] for d in decisions}==set(gs)
    for d in decisions:
        assert d['confirmed'] is True and d['reason'].strip()
        g=gs[d['review_id']]
        for tid in g['task_ids']:
            s=ROOT/'scoring/R_scores'/f'{tid}.json'
            save(ROOT/'scoring/R_score_qc'/f'{tid}.json',dict(at=now(),review_id=d['review_id'],
                 score_sha256=sha(s),confirmed=True,reason=d['reason'],reviewer='main_agent'))
    files={}
    for t in tasks('R'):
        p=ROOT/'scoring/R_scores'/f"{t['task_id']}.json";files[str(p)]=sha(p)
    for directory in ['R_response_reviews','R_score_qc']:
        for p in (ROOT/'scoring'/directory).glob('*.json'):files[str(p)]=sha(p)
    save(ROOT/'audit/R_scoring_seal_v1.json',dict(at=now(),files=files,QC_tasks=sum(len(g['task_ids']) for g in gs.values()),
         same_agent_review=True,independent_interrater_reliability=False))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['packet','apply']);p.add_argument('--path');a=p.parse_args()
    if a.action=='packet':packet()
    else:apply(a.path)
