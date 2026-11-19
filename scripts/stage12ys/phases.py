"""Close scored phases and freeze only the next plan-authorized finite panel."""
import argparse
from collections import Counter
import pandas as pd
from scripts.stage12ys.execution import ROOT,OLD,load,save,sha,now,cohort,task,validate_tasks,shards
from scripts.stage12ys.review import tasks,technical
from scripts.stage12ys.scoring import final_score
from scripts.stage12ys.protocol import ARMS,screen,select_candidates,order
from scripts.stage12ys.inference import descriptive,confirm_families

def write_parquet(path,rows):
    assert not path.exists()
    if rows:pd.DataFrame(rows).to_parquet(path,index=False)
    else:pd.DataFrame({k:pd.Series(dtype=t) for k,t in {'task_id':'str','item_id':'str','family_id':'str','arm':'str','replicate':'int64','correct':'boolean','label':'str'}.items()}).to_parquet(path,index=False)

def results(phase):
    assert (ROOT/'audit'/f'phase{phase}_scoring_review.json').exists()
    rows=[]
    for t in tasks(phase):
        tid=t['task_id'];s=final_score(tid);a=technical(tid);p=ROOT/'generations'/tid/'generation.json';g=load(p)
        rows.append(dict(task_id=tid,item_id=t['item_id'],family_id=t['family_id'],arm=t['arm'],replicate=t['replicate'],
            label=s['label'],correct=s['correct'],outcome=a['outcome'],**a['validity'],cap_hit=g['cap_hit'],tokens=g['tokens'],
            finish_reason=g['finish_reason'],latency_seconds=g['request_latency_seconds'],seed=t['seed'],
            generation_path=str(p),generation_sha256=sha(p)))
    return rows

def seal_execution(phase,new,gate,n_shards):
    ids=sorted({t['item_id'] for t in new});validate_tasks(new,ids,phase)
    p=ROOT/'audit'/f'phase{phase}_execution.json'
    save(p,dict(at=now(),phase=phase,ids=ids,tasks=new,config_sha256=sha(ROOT/'config.json')))
    save(ROOT/'audit'/f'phase{phase}_authorization.json',dict(at=now(),authorized=True,execution_sha256=sha(p),source_gate_sha256=sha(gate)))
    return shards(phase,new,n_shards)

def close_a():
    rows=results('A');assert len(rows)==288
    for a,name in [('E_T','evidence'),('T_img','image'),('T_E','equal_evidence')]:
        write_parquet(ROOT/f'stage12ys_phaseA_thinking_{name}_results.parquet',[r for r in rows if r['arm']==a])
    old=pd.read_parquet(OLD/'stage12xs_phaseA_results.parquet').to_dict('records')
    historical={(r['item_id'],{'E':'E_I','N':'I_img','O':'I_E'}[r['arm']]):r['correct'] for r in old}
    new={(r['item_id'],r['arm']):r['correct'] for r in rows};paired=[]
    for source in cohort():
        i=source['item_id'];r=dict(item_id=i,family_id=source['family_id'],subject=source['subject'],level=source['level'])
        for a in ARMS:
            v=(historical if a in ['E_I','I_img','I_E'] else new)[i,a]
            r[a]=None if pd.isna(v) else bool(v)
        r.update(screen(r));paired.append(r)
    write_parquet(ROOT/'stage12ys_phaseA_role_screen.parquet',paired)
    d=descriptive(paired)
    d['native_thinking_only_transitions']=dict(Counter(r['transition'] for r in paired if r['transition']))
    d['per_arm']={a:dict(correct=sum(r[a] is True for r in paired),scoreable=sum(r[a] is not None for r in paired),missing=sum(r[a] is None for r in paired)) for a in ARMS}
    d['new_arm_technical']={a:dict(cap_hits=sum(r['cap_hit'] for r in rows if r['arm']==a),n=96) for a in ['E_T','T_img','T_E']}
    save(ROOT/'audit/phaseA_inference.json',dict(at=now(),**d))
    access,downstream=select_candidates(paired)
    ids=sorted({r['item_id'] for r in access+downstream});source={r['item_id']:r for r in cohort()}
    m=dict(at=now(),frozen=True,access=access,downstream=downstream,selected_ids=ids,
        counts=dict(access_strong=sum(r['access_strong'] for r in paired),access_weak_inclusive=sum(r['access_weak'] for r in paired),
            downstream=sum(r['downstream'] for r in paired),selected_access=len(access),selected_downstream=len(downstream)),
        phaseA_screen_sha256=sha(ROOT/'stage12ys_phaseA_role_screen.parquet'),
        rule='Prospective spec: strong16; supplement only when strong<8; downstream native-linked preferred then hash; cap16.')
    gate=ROOT/'stage12ys_phaseB_candidate_manifest.json';save(gate,m)
    required={}
    for r in access:required.setdefault(r['item_id'],set()).update(ARMS)
    for r in downstream:
        arms=['I_E','T_E']+(['I_img','T_img'] if r['native_linked'] else [])
        required.setdefault(r['item_id'],set()).update(arms)
    new=[task(source[i],a,'B',k) for i in ids for a in sorted(required[i]) for k in range(3)]
    save(ROOT/'stage12ys_phaseB_seed_manifest.json',dict(at=now(),frozen=True,tasks=new,n_calls=len(new),candidate_sha256=sha(gate)))
    paths=seal_execution('B',new,gate,4) if new else []
    save(ROOT/'audit/phaseA_closed.json',dict(at=now(),new_calls=288,confirmation_calls=len(new),manifests=paths))
    print('A CLOSED',m['counts'],'B unique calls',len(new),'shards',paths)

def close_b():
    b=load(ROOT/'stage12ys_phaseB_candidate_manifest.json');rows=results('B') if b['selected_ids'] else []
    write_parquet(ROOT/'stage12ys_phaseB_confirmation_results.parquet',rows)
    labels=confirm_families(b['selected_ids'],rows)
    source={r['item_id']:r for r in cohort()}
    aid={r['item_id'] for r in b['access']};did={r['item_id'] for r in b['downstream']}
    for r in labels:
        r['family_id']=source[r['item_id']]['family_id'];r['in_access_panel']=r['item_id'] in aid;r['in_downstream_panel']=r['item_id'] in did
    write_parquet(ROOT/'stage12ys_phaseB_role_labels.parquet',labels)
    eligible=[r for r in labels if r['in_downstream_panel'] and r['downstream'] is True]
    eligible.sort(key=lambda r:order('STATE_TRANSFER',r['family_id']));chosen=eligible[:10]
    c=[]
    for r in chosen:
        successes=sorted([x for x in rows if x['item_id']==r['item_id'] and x['arm']=='T_E' and x['correct'] is True],key=lambda x:x['replicate'])
        assert len(successes)>=2
        c.append(dict(item_id=r['item_id'],family_id=r['family_id'],source_task_id=successes[0]['task_id'],source_generation=successes[0]['generation_path'],
            source_generation_sha256=successes[0]['generation_sha256'],source_replicate=successes[0]['replicate']))
    save(ROOT/'stage12ys_phaseC_candidate_manifest.json',dict(at=now(),frozen=True,n_eligible=len(eligible),n_selected=len(c),rows=c,
        eligible_ids=[r['item_id'] for r in eligible],selected_ids=[r['item_id'] for r in c],
        status='PREFIX_REVIEW' if len(c)>=2 else 'NOT_RUN_NO_CONFIRMED_DOWNSTREAM' if not c else 'NOT_RUN_NO_LEGAL_SHUFFLE',
        order='SHA256(stage12ys-v1|STATE_TRANSFER|family_id); first10; source first successful replicate ascending0..2'))
    save(ROOT/'audit/phaseB_inference.json',dict(at=now(),families=labels,
        access=dict(n=len(aid),support=sum(r['access'] is True for r in labels if r['in_access_panel']),unknown=sum(r['access'] is None for r in labels if r['in_access_panel'])),
        downstream=dict(n=len(did),support=sum(r['downstream'] is True for r in labels if r['in_downstream_panel']),unknown=sum(r['downstream'] is None for r in labels if r['in_downstream_panel']))))
    print('B CLOSED; confirmed downstream',len(eligible),'C selected',[r['item_id'] for r in c])

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['A','B']);a=p.parse_args();close_a() if a.phase=='A' else close_b()
