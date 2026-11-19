"""Freeze continuation-level scores, then own-response QC before family joins."""
import argparse
import hashlib
import json
import math
import re
from scripts.stage12us.common import ROOT,load,save,sha,now
from scripts.stage12us.review import tasks
from visual_reasoning.stage8b.v2_scoring import equivalent


def first():
    rows=tasks('science')
    golds={p['item_id']:p for p in [json.loads(x) for x in
           __import__('pathlib').Path('outputs/stage12ts/v1/audit/correctness_packets/T.jsonl').read_text().splitlines()]}
    pending=[]
    for t in rows:
        tid=t['task_id'];dest=ROOT/'audit/first_scores'/f'{tid}.json'
        if dest.exists():continue
        a=load(ROOT/'audit/technical_decisions'/f'{tid}.json');p=load(ROOT/'audit/review_packets'/f'{tid}.json')
        assert a['packet_sha256']==sha(ROOT/'audit/review_packets'/f'{tid}.json')
        row=golds[t['item_id']];value=a['outcome'];flags=[]
        if a['ambiguous']:flags.append('manual_extraction_ambiguity')
        if p['cap_hit']:flags.append('cap_hit')
        if not a['scoreable']:label='UNSCOREABLE_TECHNICAL';correct=None
        elif value=='__COMPLETED_NO_ANSWER__':
            assert p['finish_reason']=='stop'
            label='COMPLETED_NO_ANSWER';correct=False;flags.append('completed_no_answer')
        else:
            if row['options']:
                assert value in [chr(65+i) for i in range(len(row['options']))],(tid,value)
                correct=value==row['gold']
            else:correct=equivalent(value,row['gold'])
            if correct is None:pending.append((tid,value,row['gold']));continue
            label='CORRECT' if correct else 'INCORRECT'
            if not row['options'] and not re.fullmatch(r'-?\d+(?:\.\d+)?',value):flags.append('math_expression')
        save(dest,dict(at=now(),task_id=tid,item_id=t['item_id'],correct=correct,label=label,
             outcome=value,gold=row['gold'],flags=flags,technical_decision_sha256=sha(ROOT/'audit/technical_decisions'/f'{tid}.json')))
    print('Unresolved equivalence:',pending)


def freeze():
    paths=[ROOT/'audit/first_scores'/f"{t['task_id']}.json" for t in tasks('science')]
    rows=[load(p) for p in paths]
    mandatory=[r['task_id'] for r in rows if r['flags']]
    candidates=[r['task_id'] for r in rows if not r['flags']]
    random=sorted(candidates,key=lambda t:hashlib.sha256(('stage12us-review-v1|'+t).encode()).hexdigest())[:math.ceil(.2*len(candidates))]
    save(ROOT/'audit/first_score_seal.json',dict(at=now(),hashes={str(p):sha(p) for p in paths},
        mandatory=mandatory,random=random,second_tasks=mandatory+random,paired_aggregation_not_opened=True))
    print('Second-pass QC:',len(mandatory)+len(random))


def show_second(tail):
    seal=load(ROOT/'audit/first_score_seal.json')
    for tid in seal['second_tasks']:
        if (ROOT/'audit/second_scores'/f'{tid}.json').exists():continue
        p=load(ROOT/'audit/review_packets'/f'{tid}.json')
        print('\nTASK',tid,'STOP',p['finish_reason'],'QUESTION',p['task']['question'])
        print(p['raw'][-tail:])


def second(tid,scoreable,outcome,reason):
    assert tid in load(ROOT/'audit/first_score_seal.json')['second_tasks']
    save(ROOT/'audit/second_scores'/f'{tid}.json',dict(at=now(),task_id=tid,scoreable=scoreable,outcome=outcome,reason=reason,
        procedure='Separate own-response pass without paired condition outcomes or first extraction displayed; same agent QC.'))


def close():
    seal=load(ROOT/'audit/first_score_seal.json');reviews=[]
    for p,h in seal['hashes'].items():assert sha(p)==h
    for tid in seal['second_tasks']:
        first=load(ROOT/'audit/technical_decisions'/f'{tid}.json');second=load(ROOT/'audit/second_scores'/f'{tid}.json')
        same=first['scoreable']==second['scoreable'] and first['outcome']==second['outcome']
        assert same, ('Preserve disagreement and adjudicate before aggregation',tid)
        reviews.append(dict(task_id=tid,agreement=same,second_sha256=sha(ROOT/'audit/second_scores'/f'{tid}.json')))
    save(ROOT/'stage12us_scoring_review.json',dict(at=now(),n_first=156,n_second=len(reviews),reviews=reviews,
        first_score_seal_sha256=sha(ROOT/'audit/first_score_seal.json'),all_agree=all(r['agreement'] for r in reviews),
        independence='Same-agent separate-pass QC, not independent human reliability.',
        scope='Continuation terminal commitments and ambiguity context; full raw outputs preserved. No prefix answer credit.'))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['first','freeze','show_second','close']);p.add_argument('--tail',type=int,default=800)
    a=p.parse_args();show_second(a.tail) if a.action=='show_second' else globals()[a.action]()
