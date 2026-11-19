"""Materialize only the next plan-prescribed wave after sealed scoring."""
import argparse
from pathlib import Path
import pandas as pd
from scripts.stage12vs.common import ROOT,load,save,sha,now
from scripts.stage12vs.protocol import seed,majority,localization
from scripts.stage12vs.review import tasks,checked


def scored(phase):
    assert load(ROOT/'audit'/f'{phase}_scoring_closed.json')['pass_all']
    for p,h in load(ROOT/'audit'/f'{phase}_score_seal.json')['hashes'].items():assert sha(p)==h,p
    out=[]
    for t in tasks(phase):
        g,c=checked(t);s=load(ROOT/'audit/first_scores'/f"{t['task_id']}.json")
        assert s['technical_decision_sha256']==sha(ROOT/'audit/technical_decisions'/f"{t['task_id']}.json")
        out.append(dict(**t,correct=s['correct'],outcome=s['outcome'],label=s['label'],input_valid=all(c.values()),
            cap_hit=g['cap_hit'],tokens=g['tokens'],latency_seconds=g['request_latency_seconds'],job=g['job'],node=g['node']))
    return out


def families():return load(ROOT/'stage12vs_coarse_prefix_manifest.json')['families']


def curves():
    rows=scored('phaseA')
    for p in sorted((ROOT/'audit').glob('phaseB*_scoring_closed.json')):
        rows+=scored(p.name.removesuffix('_scoring_closed.json'))
    result={}
    for f in families():
        selected=[r for r in rows if r['item_id']==f['item_id']]
        points={}
        for k in sorted({r['step_index'] for r in selected}):
            vals=[r['correct'] for r in sorted(selected,key=lambda r:r['replicate']) if r['step_index']==k]
            assert len(vals)==3,('Boundary must never be rerun',f['item_id'],k)
            points[k]=dict(majority=majority(vals),outcomes=vals)
        result[f['item_id']]=points
    return result


def gate():
    rows=scored('phaseA');pd.DataFrame(rows).to_parquet(ROOT/'stage12vs_coarse_results.parquet',index=False)
    cc=curves();out=[]
    for f in families():
        pp=cc[f['item_id']];zero=pp[0]['majority'];full=pp[f['m']]['majority']
        out.append(dict(item_id=f['item_id'],P0=zero,Pm=full,eligible=zero is False and full is True))
    failures=sum(r['Pm'] is False for r in out);unknown=sum(r['Pm'] is None for r in out)
    proceed=failures+unknown<=1 and any(r['eligible'] for r in out)
    save(ROOT/'audit/replication_gate.json',dict(at=now(),rows=out,full_failures=failures,full_unknown=unknown,
         **{'continue':proceed},decision='PORTABILITY_UNSTABLE' if failures>1 else 'CONTINUE' if proceed else 'UNRESOLVED'))
    print(out,'CONTINUE',proceed)


def prefix_task(item,k,phase,condition,target,rep):
    f=next(x for x in families() if x['item_id']==item)
    ss=[s for s in load(ROOT/'stage12vs_semantic_steps.json')['rows'] if s['item_id']==item]
    text=''.join(s['text'] for s in ss[:k]);path=ROOT/'prefixes'/f'{item}_P{k}.txt'
    if path.exists():assert path.read_text()==text
    else:
        with path.open('x') as h:h.write(text)
    namespace='phaseB' if phase.startswith('phaseB') else phase
    return dict(task_id=f'{condition}_{item}_k{k}_r{rep}',phase=phase,cohort='primary',item_id=item,family_id=f['family_id'],
         question=f['question'],target=target,condition=condition,step_index=k,replicate=rep,
         seed=seed(f['family_id'],namespace,k,rep),prefix_path=str(path),prefix_sha256=sha(path))


def freeze_wave(phase,rows,shards=1):
    assert rows and len({r['target'] for r in rows})==1
    save(ROOT/'audit'/f'{phase}_execution.json',dict(at=now(),tasks=rows))
    for i in range(shards):
        save(ROOT/'queues'/f'{phase}_{i}.json',dict(frozen=True,phase=phase,target=rows[0]['target'],config_sha256=sha(ROOT/'config.json'),rows=rows[i::shards]))


def fine(phase):
    assert phase.startswith('phaseB') and load(ROOT/'audit/replication_gate.json')['continue']
    eligible={r['item_id'] for r in load(ROOT/'audit/replication_gate.json')['rows'] if r['eligible']}
    cc=curves();states=[];rows=[]
    for f in families():
        item=f['item_id'];state=localization({k:v['majority'] for k,v in cc[item].items()}) if item in eligible else dict(status='REPLICATION_INELIGIBLE')
        states.append(dict(item_id=item,family_id=f['family_id'],**state,points=cc[item]))
        if state['status']=='BISECT':rows.extend(prefix_task(item,state['next'],phase,'B','I',r) for r in range(3))
    save(ROOT/'audit'/f'{phase}_planning.json',dict(at=now(),families=states,new_calls=len(rows),rules_frozen_before_phaseA=True))
    if rows:
        done=sum(len(tasks(p.name.removesuffix('_execution.json'))) for p in (ROOT/'audit').glob('phaseB*_execution.json'))
        assert done+len(rows)<=load(ROOT/'audit/resource_estimate.json')['fine_max_calls']
        freeze_wave(phase,rows)
    else:
        save(ROOT/'stage12vs_fine_localization.json',dict(at=now(),families=states))
        print('FINE_COMPLETE',[(s['item_id'],s['status']) for s in states])
    print('Next calls',len(rows))


def adjacent():
    rows=[]
    for f in load(ROOT/'stage12vs_fine_localization.json')['families']:
        if f['status']!='STABLE':continue
        for k in [f['a'],f['b']]:rows.extend(prefix_task(f['item_id'],k,'adjacentT','T_ADJ','T',r) for r in range(3))
    if rows:freeze_wave('adjacentT',rows,shards=min(2,len(rows)//6))
    print('Adjacent Thinking calls',len(rows))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['gate','fine','adjacent']);p.add_argument('--phase')
    a=p.parse_args();fine(a.phase) if a.action=='fine' else globals()[a.action]()
