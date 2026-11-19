"""Materialize only the next approved phase from sealed per-call scoring."""
import argparse
from pathlib import Path
from scripts.stage12ws.common import ROOT,load,save,sha,now
from scripts.stage12ws.protocol import seed,paired,gate

def families():return load(ROOT/'stage12ws_primary_manifest.json')['families']

def scored(phase):
    assert load(ROOT/'audit'/f'{phase}_scoring_closed.json')['pass_all']
    ex=load(ROOT/'audit'/f'{phase}_execution.json');rows=[]
    for task in ex.get('logical_tasks',ex['tasks']):
        tid=task.get('canonical_task_id',task['task_id'])
        r=load(ROOT/'audit/first_scores'/f'{tid}.json')
        rows.append(dict(**task,correct=r['correct'],outcome=r['outcome'],label=r['label']))
    return rows

def vector(rows,item,condition):
    selected=sorted([r for r in rows if r['item_id']==item and r['condition']==condition],key=lambda r:r['replicate'])
    assert [r['replicate'] for r in selected]==list(range(7))
    return [r['correct'] for r in selected]

def replication():
    rows=scored('phaseA');ff=[]
    for f in families():
        item=f['item_id'];a=vector(rows,item,'FULL');b=vector(rows,item,'Q');x=paired(a,b)
        ff.append(dict(item_id=item,family_id=f['family_id'],full=a,question=b,effect=x,eligible=x['at_least_3']))
    g=gate([f['eligible'] for f in ff])
    out=dict(at=now(),families=ff,status=g,**{'continue':g=='CONTINUE'},eligible=[f['item_id'] for f in ff if f['eligible'] is True])
    save(ROOT/'audit/replication_gate.json',out);print(out)
    import pandas as pd
    pd.DataFrame(rows).to_parquet(ROOT/'stage12ws_full_state_results.parquet',index=False)

def identity(task):return task['family_id'],task['question'],task['prefix_sha256'],task['seed'],task['target']

def queue(phase,conditions,shards):
    assert load(ROOT/'audit/replication_gate.json')['continue']
    old={identity(t):t['task_id'] for p in sorted((ROOT/'audit').glob('*_execution.json')) for t in load(p)['tasks']}
    tasks=[];logical=[]
    for f,cond,material in conditions:
        for rep in range(7):
            t=dict(task_id=f"{phase}_{f['item_id']}_{cond}_r{rep}",phase=phase,cohort='primary',item_id=f['item_id'],family_id=f['family_id'],
                   target='I',condition=cond,replicate=rep,seed=seed(f['family_id'],rep),**material)
            key=identity(t)
            if key in old:logical.append(dict(t,canonical_task_id=old[key]))
            else:tasks.append(t);logical.append(dict(t,canonical_task_id=t['task_id']));old[key]=t['task_id']
    save(ROOT/'audit'/f'{phase}_execution.json',dict(at=now(),tasks=tasks,logical_tasks=logical))
    if not tasks:
        save(ROOT/'audit'/f'{phase}_scoring_closed.json',dict(at=now(),n=0,reviews=[],pass_all=True,all_reused=True));return []
    count=min(shards,(len(tasks)+17)//18);paths=[]
    ordered=sorted(tasks,key=lambda t:(-t['prefix_tokens'],t['task_id']))
    for i in range(count):
        p=ROOT/'queues'/f'{phase}_{i}.json'
        save(p,dict(frozen=True,phase=phase,target='I',config_sha256=sha(ROOT/'config.json'),rows=ordered[i::count]));paths.append(str(p))
    print(phase,'unique calls',len(tasks),'logical',len(logical),'queues',paths);return paths

def materialize(phase,shards):
    ff=families();g=load(ROOT/'audit/replication_gate.json');assert g['continue']
    if phase=='phaseB':
        assert load(ROOT/'audit/phaseA_scoring_closed.json')['pass_all']
        conds=[(f,f"MINUS_B{b['block_id']}",f['conditions'][f"MINUS_B{b['block_id']}"]) for f in ff if f['item_id'] in g['eligible'] for b in f['blocks']]
    elif phase=='phaseC':
        assert load(ROOT/'audit/phaseB_scoring_closed.json')['pass_all']
        conds=[(f,c,f['conditions'][c]) for f in ff for c in ['ESTAR','ESTAR_D','FULL','MINUS_D']]
    elif phase=='phaseE':
        assert load(ROOT/'audit/phaseD_closed.json')['complete']
        conds=[(f,'ORDER',f['conditions']['ORDER']) for f in ff]
    elif phase=='phaseF':
        assert load(ROOT/'audit/phaseE_scoring_closed.json')['pass_all']
        f=next(f for f in ff if f['item_id']=='750')
        conds=[(f,c,f['conditions'][c]) for c in ['P299','P448','P598']]
    else:raise ValueError(phase)
    queue(phase,conds,shards)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase');p.add_argument('--shards',type=int,default=4);a=p.parse_args()
    replication() if a.phase=='gate' else materialize(a.phase,a.shards)
