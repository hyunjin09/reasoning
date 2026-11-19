"""Per-wave answer extraction QC before adaptive family decisions."""
import argparse
import hashlib
import json
import math
import re
from pathlib import Path
from scripts.stage12ws.common import ROOT,load,save,sha,now
from scripts.stage12ws.review import tasks
from visual_reasoning.stage8b.v2_scoring import equivalent


def first(phase):
    golds={r['item_id']:r for r in map(json.loads,Path('outputs/stage12ts/v1/audit/correctness_packets/T.jsonl').read_text().splitlines())}
    for t in tasks(phase):
        tid=t['task_id'];dest=ROOT/'audit/first_scores'/f'{tid}.json'
        if dest.exists():continue
        a=load(ROOT/'audit/technical_decisions'/f'{tid}.json');p=load(ROOT/'audit/review_packets'/f'{tid}.json')
        assert a['packet_sha256']==sha(ROOT/'audit/review_packets'/f'{tid}.json')
        row=golds[t['item_id']];value=a['outcome'];flags=[]
        if a['ambiguous']:flags.append('ambiguous')
        if p['cap_hit']:flags.append('cap_hit')
        if not a['scoreable']:correct=None;label='UNSCOREABLE_TECHNICAL'
        elif value=='__COMPLETED_NO_ANSWER__':
            assert p['finish_reason']=='stop'
            correct=False;label='COMPLETED_NO_ANSWER';flags.append('no_answer')
        else:
            if row['options']:
                assert value in [chr(65+i) for i in range(len(row['options']))]
                correct=value==row['gold']
            else:correct=equivalent(value,row['gold'])
            assert correct is not None,('Unresolved equivalence',tid,value,row['gold'])
            label='CORRECT' if correct else 'INCORRECT'
            if not row['options'] and not re.fullmatch(r'-?\d+(?:\.\d+)?',value):flags.append('math_expression')
        save(dest,dict(at=now(),task_id=tid,item_id=t['item_id'],correct=correct,label=label,outcome=value,gold=row['gold'],flags=flags,
                       technical_decision_sha256=sha(ROOT/'audit/technical_decisions'/f'{tid}.json')))


def freeze(phase):
    paths=[ROOT/'audit/first_scores'/f"{t['task_id']}.json" for t in tasks(phase)];rows=[load(p) for p in paths]
    mandatory=[r['task_id'] for r in rows if r['flags']];eligible=[r['task_id'] for r in rows if not r['flags']]
    sampled=sorted(eligible,key=lambda x:hashlib.sha256(('stage12ws-qc-v1|'+x).encode()).hexdigest())[:math.ceil(.2*len(eligible))]
    save(ROOT/'audit'/f'{phase}_score_seal.json',dict(at=now(),hashes={str(p):sha(p) for p in paths},second_tasks=mandatory+sampled))
    print('QC tasks',mandatory+sampled)


def show_second(phase,tail):
    for tid in load(ROOT/'audit'/f'{phase}_score_seal.json')['second_tasks']:
        if (ROOT/'audit/second_scores'/f'{tid}.json').exists():continue
        p=load(ROOT/'audit/review_packets'/f'{tid}.json');print('\nTASK',tid,'STOP',p['finish_reason'])
        print(p['task']['question']);print(p['raw'][-tail:])


def second(phase,tid,scoreable,outcome,reason):
    assert tid in load(ROOT/'audit'/f'{phase}_score_seal.json')['second_tasks']
    save(ROOT/'audit/second_scores'/f'{tid}.json',dict(at=now(),task_id=tid,scoreable=scoreable,outcome=outcome,reason=reason,
         procedure='Same-agent separate displayed-own-response pass without first extraction/gold/paired outcomes shown.'))


def close(phase):
    seal=load(ROOT/'audit'/f'{phase}_score_seal.json');reviews=[]
    for p,h in seal['hashes'].items():assert sha(p)==h,p
    for tid in seal['second_tasks']:
        a=load(ROOT/'audit/technical_decisions'/f'{tid}.json');b=load(ROOT/'audit/second_scores'/f'{tid}.json')
        assert a['scoreable']==b['scoreable'] and a['outcome']==b['outcome'],('Preserve and adjudicate mismatch',tid)
        reviews.append(dict(task_id=tid,agreement=True,second_sha256=sha(ROOT/'audit/second_scores'/f'{tid}.json')))
    save(ROOT/'audit'/f'{phase}_scoring_closed.json',dict(at=now(),n=len(tasks(phase)),reviews=reviews,pass_all=True))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['first','freeze','show_second','close']);p.add_argument('phase');p.add_argument('--tail',type=int,default=650)
    a=p.parse_args();show_second(a.phase,a.tail) if a.action=='show_second' else globals()[a.action](a.phase)
