"""Frozen paired-seed estimands and exact block operations."""
import hashlib
from scripts.stage12ws.common import ROOT,load,sha
from scripts.stage12us.protocol import render
DERIVED={'DERIVED_RELATIONS','INTERMEDIATE_COMPUTATION','SUBGOAL_CONCLUSION','REPAIR_OR_RESOLUTION'}

def seed(family,replicate):
    assert replicate in range(7)
    return int(hashlib.sha256(f'stage12ws-v1|{family}|{replicate}'.encode()).hexdigest(),16)%(2**31)

def paired(a,b,identical=False):
    assert len(a)==len(b)==7 and all(x is None or type(x) is bool for x in a+b)
    lo=hi=0;diffs=[]
    for x,y in zip(a,b):
        if identical:
            assert x==y;delta=0;low=high=0
        elif x is not None and y is not None:delta=int(x)-int(y);low=high=delta
        else:
            delta=None;low=int(x is True)-int(y is not False);high=int(x is not False)-int(y is True)
        diffs.append(delta);lo+=low;hi+=high
    return dict(seed_differences=diffs,net_successes=lo if lo==hi else None,net_bounds=[lo,hi],
                difference=lo/7 if lo==hi else None,difference_bounds=[lo/7,hi/7],
                at_least_3=True if lo>=3 else False if hi<3 else None,
                at_least_4=True if lo>=4 else False if hi<4 else None)

def gate(status):
    return 'CONTINUE' if status.count(True)>=3 else 'STOP_WEAK' if status.count(True)+status.count(None)<3 else 'STOP_UNRESOLVED'

def partition(steps,ends):
    assert ends==sorted(set(ends)) and ends[-1]==len(steps) and ends[0]>=1
    blocks=[];start=0
    for i,end in enumerate(ends,1):
        blocks.append(dict(block_id=i,start_step=start+1,end_step=end,text=''.join(steps[start:end])))
        start=end
    assert ''.join(b['text'] for b in blocks)==''.join(steps)
    return blocks

def retain(blocks,ids):return ''.join(b['text'] for b in blocks if b['block_id'] in ids)

def order_blocks(blocks):
    assert blocks[0]['role']=='RAW_EVIDENCE_AND_BINDING'
    eligible=sorted([b for b in blocks if b['role'] in DERIVED],key=lambda b:(-b['token_count'],b['block_id']))
    assert len(eligible)>=2
    a,b=[x['block_id'] for x in eligible[:2]];ids=[x['block_id'] for x in blocks]
    ia,ib=ids.index(a),ids.index(b);ids[ia],ids[ib]=ids[ib],ids[ia]
    return ids

def authorize(manifest):
    expected={t['task_id']:t for t in load(ROOT/'audit'/f"{manifest['phase']}_execution.json")['tasks']}
    assert manifest['frozen'] and manifest['config_sha256']==sha(ROOT/'config.json')
    assert manifest['target']=='I' and len({t['task_id'] for t in manifest['rows']})==len(manifest['rows'])
    assert all(t==expected.get(t['task_id']) and t['seed']==seed(t['family_id'],t['replicate']) for t in manifest['rows'])
    for p,h in load(ROOT/'audit/source_seal.json')['hashes'].items():assert sha(p)==h,p
    if manifest['phase']!='phaseA':assert load(ROOT/'audit/replication_gate.json')['continue']
