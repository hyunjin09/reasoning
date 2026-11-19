"""Closed-review phase transitions; no downstream launch without the plan gate."""
import argparse
from pathlib import Path
import pandas as pd
from scripts.stage12xs.execution_v2 import ROOT,load,save,sha,now,CAPS,validate_tasks,authorize
from scripts.stage12xs.review_v2 import tasks,technical
from scripts.stage12xs.scoring_v2 import final_score
from scripts.stage12bs.inference import proportion


def write_parquet(path,rows):
    assert not path.exists();pd.DataFrame(rows).to_parquet(path,index=False)

def result_rows(phase):
    assert (ROOT/'audit'/f'phase{phase}_scoring_review.json').exists()
    result=[]
    for t in tasks(phase):
        tid=t['task_id'];s=final_score(tid);a=technical(tid);g=load(ROOT/'generations'/tid/'generation.json')
        result.append(dict(task_id=tid,item_id=t['item_id'],family_id=t['family_id'],arm=t['arm'],replicate=t.get('replicate'),
            label=s['label'],correct=s['correct'],outcome=a['outcome'],**a['validity'],cap_hit=g['cap_hit'],tokens=g['tokens'],
            finish_reason=g['finish_reason'],latency_seconds=g['request_latency_seconds'],seed=t['seed'],
            generation_path=str(ROOT/'generations'/tid/'generation.json'),generation_sha256=sha(ROOT/'generations'/tid/'generation.json')))
    return result

def seal_execution(phase,selected,tasks_,shards):
    ids=[r['item_id'] for r in selected];validate_tasks(tasks_,ids,phase)
    execution=ROOT/'audit'/f'phase{phase}_execution.json'
    save(execution,dict(at=now(),frozen=True,phase=phase,ids=ids,tasks=tasks_,config_sha256=sha(ROOT/'config.json')))
    save(ROOT/'audit'/f'phase{phase}_authorization.json',dict(at=now(),authorized=True,execution_sha256=sha(execution),
        source_gate_sha256=sha(ROOT/('stage12xs_phaseB_b4_manifest.json' if phase=='B' else 'stage12xs_transfer_candidate_manifest.json'))))
    paths=[]
    for k,(model_key,rows) in enumerate(shards):
        m=dict(at=now(),frozen=True,phase=phase,model_key=model_key,rows=rows,config_sha256=sha(ROOT/'config.json'))
        authorize(m);path=ROOT/'audit'/f'phase{phase}_{k}.json';save(path,m);paths.append(str(path))
    return paths

def close_a():
    rows=result_rows('A');assert len(rows)==288
    write_parquet(ROOT/'stage12xs_phaseA_results.parquet',rows)
    cohort=load(ROOT/'stage12xs_fresh96_manifest.json');by={(r['item_id'],r['arm']):r for r in rows};profiles=[]
    for r in cohort['rows']:
        e,n,o=[by[r['item_id'],a]['correct'] for a in 'ENO'];complete=all(x is not None for x in [e,n,o])
        b=('B2' if e else 'B1') if o else ('B3' if e else 'B4')
        profiles.append(dict(item_id=r['item_id'],family_id=r['family_id'],e=e,n=n,o=o,complete=complete,
            profile='UNSCOREABLE_TECHNICAL' if not complete else 'NATIVE_SUCCESS' if n else b))
    write_parquet(ROOT/'stage12xs_fresh_failure_profiles.parquet',profiles)
    all_b4={r['item_id'] for r in profiles if r['profile']=='B4'};ids=[i for i in cohort['b4_order'] if i in all_b4][:24]
    selected=[next(r for r in cohort['rows'] if r['item_id']==i) for i in ids]
    failures=[r for r in profiles if r['complete'] and not r['n']]
    native_oracle=[r for r in profiles if r['n'] is False and r['o'] is not None]
    save(ROOT/'audit/phaseA_inference.json',dict(at=now(),n_families=96,independent_unit='family',
        per_arm={a:dict(n=96,scoreable=sum(x['correct'] is not None for x in rows if x['arm']==a),
            accuracy=proportion(sum(x['correct'] is True for x in rows if x['arm']==a),sum(x['correct'] is not None for x in rows if x['arm']==a)),
            cap_hits=sum(x['cap_hit'] for x in rows if x['arm']==a)) for a in 'ENO'},
        complete_scoreable_native_failures=len(failures),B_counts={b:sum(r['profile']==b for r in profiles) for b in ['B1','B2','B3','B4']},
        oracle_rescue_complete=proportion(sum(r['o'] for r in failures),len(failures)),
        oracle_rescue_all_scoreable_Nminus_O=proportion(sum(r['o'] for r in native_oracle),len(native_oracle)),
        technical_incomplete_ids=[r['item_id'] for r in profiles if not r['complete']]))
    save(ROOT/'stage12xs_phaseB_b4_manifest.json',dict(at=now(),frozen=True,all_b4_count=len(all_b4),all_b4_order=[i for i in cohort['b4_order'] if i in all_b4],
        selected_ids=ids,rows=selected,rule='First min(24,scoreable B4) in pre-PhaseA frozen hash order',phaseA_profiles_sha256=sha(ROOT/'stage12xs_fresh_failure_profiles.parquet')))
    if not selected:print('B4 zero; no PhaseB calls');return
    new=[]
    for r in selected:
        for a in 'CT':
            new.append(dict(task_id=f"{a}_{r['item_id']}_xs1",item_id=r['item_id'],family_id=r['family_id'],arm=a,model_key='T' if a=='T' else 'I',
                cap=CAPS[a],prompt=r['prompts'][a],prompt_version='stage12xs-source-seal-v2',image=r['image'],image_sha256=r['image_sha256'],seed=r['seed']))
    # One checkpoint per finite shard; two shards each when at least12 B4 families.
    shards=[]
    for a in 'CT':
        subset=[t for t in new if t['arm']==a];n=2 if len(subset)>=12 else 1
        shards.extend((subset[0]['model_key'],subset[k::n]) for k in range(n))
    print('PhaseB shards',seal_execution('B',selected,new,shards))

def close_b():
    rows=result_rows('B');cohort=load(ROOT/'stage12xs_fresh96_manifest.json');b=load(ROOT/'stage12xs_phaseB_b4_manifest.json')
    for a,name in [('C','cot'),('T','thinking')]:write_parquet(ROOT/f'stage12xs_{name}_results.parquet',[r for r in rows if r['arm']==a])
    by={(r['item_id'],r['arm']):r for r in rows};transitions=[]
    for i in b['selected_ids']:
        c,t=[by[i,a]['correct'] for a in 'CT']
        label='UNSCOREABLE_TECHNICAL' if c is None or t is None else 'BOTH_SUCCESS' if c and t else 'C_ONLY' if c else 'T_ONLY' if t else 'BOTH_FAIL'
        transitions.append(dict(item_id=i,c=c,t=t,transition=label))
    eligible={r['item_id'] for r in transitions if r['transition']=='T_ONLY'};allids=[i for i in cohort['transfer_order'] if i in eligible];ids=allids[:10]
    selected=[next(r for r in cohort['rows'] if r['item_id']==i) for i in ids]
    save(ROOT/'stage12xs_transfer_candidate_manifest.json',dict(at=now(),frozen=True,n_all_eligible=len(allids),n_selected=len(ids),
        all_eligible_ids=allids,selected_ids=ids,rows=selected,transitions=transitions,
        gate='HELDOUT_CANDIDATE_SPARSE' if len(ids)<3 else 'LOW_YIELD_PROCEED' if len(ids)<5 else 'PROCEED',
        rule='B4 C- T+ bothscoreable; first10 in pre-outcome transfer hash; denominator tested candidates, all yield separately'))
    print('PhaseB closed; transfer candidates',ids)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['A','B']);a=p.parse_args();close_a() if a.phase=='A' else close_b()
