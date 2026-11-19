#!/usr/bin/env python3
"""Freeze full primary results, evaluate prospective gates and parse follow-ups."""
import argparse
from scripts.stage3c10.freeze_inputs import ROOT,OUT,read_json,read_jsonl,write_json,write_jsonl,sha
from visual_reasoning.stage3c10.protocol import PRIMARY,paired_effects,vsd
from visual_reasoning.stage3c10.analysis import summarize_family,secondary,primary_gates,k80_window

TARGETS=['target_a','target_b']

def load_phase(phase):
    return [read_json(p) for p in (OUT/f'raw/{phase}').glob('shard_*/*/target_*/*.json')]

def primary():
    config=read_json(OUT/'config/stage3c10_config.json');rows=load_phase('primary')
    ids=set(config['cohort_ids']['primary']);expected={(b,t,s) for b in ids for t in TARGETS for s in ['M','T']}
    assert len(rows)==96 and {(r['base_problem_id'],r['target_id'],r['state']) for r in rows}==expected
    grouped={t:{b:{} for b in ids} for t in TARGETS}
    exports={name:[] for name in ['native_scores','r16_knockdown','e16_control','q_source_control','target_vsd','irrelevant_vsd']}
    for r in rows:
        base=r['base_problem_id'];tid=r['target_id'];s=r['state'];a=r['arms'];grouped[tid][base][s]=a
        for name,out in [('N','native_scores'),('R16','r16_knockdown'),('E16','e16_control'),('Q','q_source_control')]:
            if name in a:exports[out].append({'base_problem_id':base,'target_id':tid,'state':s,'arm':name,**a[name]['none']})
        for roi,out in [('T','target_vsd'),('I','irrelevant_vsd')]:
            exports[out].append({'base_problem_id':base,'target_id':tid,'state':s,
                'VSD':{name:vsd(a,name,roi) for name in a},
                'TE_VSD':{name:vsd(a,'N',roi)-vsd(a,name,roi) for name in a if name!='N'}})
    statistics={};gates={};effects={};temporal=[]
    for tid in TARGETS:
        effects[tid]={base:paired_effects(states) for base,states in grouped[tid].items()}
        values={k:{b:e[k] for b,e in effects[tid].items() if e.get(k) is not None} for k in PRIMARY}
        statistics[tid]=summarize_family(values);gates[tid]=primary_gates(statistics[tid])
        if gates[tid]['temporal_eligible']:temporal.append({'target_id':tid,'windows':[1,2,4,8,16]})
    for name,export in exports.items():write_jsonl(OUT/f'phase_b_primary/{name}.jsonl',export)
    output={'statistics':statistics,'gates':gates,'paired_effects_by_base':effects,
        'unit':'base_problem_id','M_T_are_paired':True,'Q_rescue_slots':'p=1 until mediation; B gates remain frozen'}
    write_json(OUT/'phase_b_primary/primary_statistics.json',output)
    freeze={'raw_sha256':{str(p.relative_to(ROOT)):sha(p) for p in (OUT/'raw/primary').glob('shard_*/*/target_*/*.json')},
        'statistics_sha256':sha(OUT/'phase_b_primary/primary_statistics.json'),'gates':gates,'complete_before_gates':True,
        'N_unique_bases':24,'state_files':96}
    p=OUT/'phase_b_primary/primary_freeze.json'
    if p.exists():assert read_json(p)==freeze
    else:write_json(p,freeze)
    write_json(OUT/'analysis/temporal_tasks.json',{'gate':'R16 routing OR VSD robust','tasks':temporal})
    print({'phase':'primary','gates':gates,'key_effects':{t:{k:statistics[t][k] for k in ['rds_T','vsd_T','did']} for t in TARGETS}})


def temporal():
    primary=read_json(OUT/'phase_b_primary/primary_statistics.json');tasks=read_json(OUT/'analysis/temporal_tasks.json')['tasks']
    eligible={x['target_id'] for x in tasks};rows=load_phase('temporal')
    assert len(rows)==24*len(eligible)
    output={};k80={};layers=[];family=read_json(OUT/'config/primary_family.json')
    for t in TARGETS:
        if t not in eligible:
            output[t]={'status':'NOT RUN — gate closed'};k80[t]={'k80':None,'reason':'temporal gate closed'};continue
        values={str(k):{} for k in [1,2,4,8,16]}
        for row in rows:
            if row['target_id']!=t:continue
            for k in [1,2,4,8,16]:values[str(k)][row['base_problem_id']]=vsd(row['arms'],'N')-vsd(row['arms'],f'R{k}')
        summaries=summarize_family(values,order=list(values));output[t]=summaries
        k80[t]=k80_window(primary['statistics'][t]['vsd_T'],summaries)
        if primary['gates'][t]['layers_eligible']:
            for name,scope in family['layer_bins'].items():
                if name=='L4A' and t=='target_b':continue
                layers.append({'target_id':t,'arm':name,'layers':scope,'k':k80[t]['k80'] or 16})
    for k in [1,2,4,8,16]:
        write_jsonl(OUT/f'phase_c_temporal/r{k}.jsonl',[{'base_problem_id':r['base_problem_id'],'target_id':r['target_id'],'arms':{'N':r['arms']['N'],f'R{k}':r['arms'][f'R{k}']}} for r in rows])
    write_json(OUT/'phase_c_temporal/temporal_profile.json',output);write_json(OUT/'phase_c_temporal/k80.json',k80)
    write_json(OUT/'analysis/layers_tasks.json',{'gate':'complete primary behavioral trigger gate','tasks':layers})
    print({'phase':'temporal','k80':k80,'layer_tasks':layers})


def layers():
    tasks=read_json(OUT/'analysis/layers_tasks.json')['tasks'];rows=load_phase('layers')
    assert len(rows)==24*len({x['target_id'] for x in tasks})
    out={}
    for t in TARGETS:
        names=[x['arm'] for x in tasks if x['target_id']==t]
        if not names:out[t]={'status':'NOT RUN — primary behavioral trigger gate closed'};continue
        values={n:{r['base_problem_id']:vsd(r['arms'],'N')-vsd(r['arms'],n) for r in rows if r['target_id']==t} for n in names}
        out[t]=summarize_family(values,order=names)
    write_jsonl(OUT/'phase_d_layers/layer_bin_results.jsonl',rows)
    write_json(OUT/'phase_d_layers/layer_profile.json',out)
    print({'phase':'layers','rows':len(rows)})


def mediation():
    primary=read_json(OUT/'phase_b_primary/primary_statistics.json');rows=load_phase('mediation')
    assert len(rows)==48 and {(r['base_problem_id'],r['target_id']) for r in rows}=={(b,t) for b in read_json(OUT/'config/stage3c10_config.json')['cohort_ids']['primary'] for t in TARGETS}
    output={};tasks=[]
    for t in TARGETS:
        baseline=primary['statistics'][t];values={k:baseline[k]['values_by_base'] for k in PRIMARY}
        values['q_rescue_rds']={r['base_problem_id']:r['arms']['Q_all']['none']['rds']-r['arms']['R16']['none']['rds'] for r in rows if r['target_id']==t}
        values['q_rescue_vsd']={r['base_problem_id']:vsd(r['arms'],'Q_all')-vsd(r['arms'],'R16') for r in rows if r['target_id']==t}
        final=summarize_family(values);selected={}
        for key in ['rds','vsd']:
            vals={r['base_problem_id']:(r['arms']['Q_selected']['none']['rds']-r['arms']['R16']['none']['rds'] if key=='rds' else vsd(r['arms'],'Q_selected')-vsd(r['arms'],'R16')) for r in rows if r['target_id']==t}
            selected[key]=secondary(vals,4)
        output[t]={'primary_family_with_rescue':final,'selected_head_secondary':selected,
            'primary_gate_unchanged':primary['gates'][t]}
        if baseline['vsd_T']['robust_positive'] and final['q_rescue_rds']['robust_positive'] and not final['q_rescue_vsd']['robust_positive']:
            tasks.append({'target_id':t,'arm':'hpre','label':'upper-bound secondary state rescue'})
    for name,arm in [('all_head_q_rescue','Q_all'),('selected_head_q_rescue','Q_selected')]:
        write_jsonl(OUT/f'phase_e_mediation/{name}.jsonl',[{'base_problem_id':r['base_problem_id'],'target_id':r['target_id'],'arms':{n:r['arms'][n] for n in ['N','R16',arm]}} for r in rows])
    write_json(OUT/'phase_e_mediation/mediation_statistics.json',output)
    write_json(OUT/'analysis/hpre_tasks.json',{'gate':'strong primary VSD plus robust Q routing rescue without robust Q VSD rescue','tasks':tasks})
    print({'phase':'mediation','hpre_tasks':tasks,'Q_rescue':{t:{k:output[t]['primary_family_with_rescue'][k] for k in PRIMARY[-2:]} for t in TARGETS}})


def hpre():
    tasks=read_json(OUT/'analysis/hpre_tasks.json')['tasks'];rows=load_phase('hpre');assert len(rows)==24*len(tasks)
    out={}
    for t in TARGETS:
        selected=[r for r in rows if r['target_id']==t]
        out[t]={key:secondary({r['base_problem_id']:(r['arms']['hpre']['none']['rds']-r['arms']['R16']['none']['rds'] if key=='rds' else vsd(r['arms'],'hpre')-vsd(r['arms'],'R16')) for r in selected},4) for key in ['rds','vsd']} if selected else {'status':'NOT RUN — optional gate closed'}
    write_jsonl(OUT/'phase_e_mediation/optional_hpre_rescue.jsonl',rows)
    write_json(OUT/'phase_e_mediation/hpre_statistics.json',{'label':'upper-bound secondary','targets':out})
    print({'phase':'hpre','rows':len(rows)})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--phase',choices=['primary','temporal','layers','mediation','hpre'],required=True)
    globals()[p.parse_args().phase]()
