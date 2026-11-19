#!/usr/bin/env python3
"""Reuse attention-blind labels; freeze positions before distance-first summaries."""
import argparse
import statistics
from collections import defaultdict
from scripts.stage3c10.freeze_inputs import ROOT,OUT,read_json,read_jsonl,write_json,write_jsonl,sha
from visual_reasoning.stage3c10.protocol import vsd
from visual_reasoning.stage3c8.analysis import summarize_effect


def annotations():
    read_json(OUT/'phase_b_primary/primary_freeze.json')
    p=OUT/'annotations/optional_recent_token_annotations.jsonl'
    if p.exists():raise FileExistsError(p)
    assets={r['base_problem_id']:r for r in read_jsonl(OUT/'config/assets.jsonl') if r['cohort_role']=='primary'}
    source=ROOT/'outputs/stage3c8/annotations/per_token_annotations.jsonl'
    inherited={}
    for line in source.open():
        import json
        r=json.loads(line)
        if r['base_problem_id'] in assets and r['stream']=='PREVIOUS_REASONING':
            inherited[(r['base_problem_id'],r['coordinate'],int(r['token_position']))]=r
    rows=[]
    for base,item in assets.items():
        for target,states in item['states'].items():
            for state,coord in states.items():
                for i in coord['source_windows_generated_zero_based']['R16']:
                    r=inherited[(base,target,i)]
                    assert r['token_id']==item['context'][i] and r['absolute_sequence_position']==item['prompt_length']+i
                    label='TARGET_ALIGNED' if r['visual_alignment']=='TARGET_ALIGNED' else r['lexical_semantic_class']
                    rows.append({**r,'target_id':target,'state':state,'generated_zero_based_position':i,
                        'distance':coord['current_zero_based_index']-i,'token_class':label,
                        'stage3c10_position_scores_available':False,'annotation_source':str(source.relative_to(ROOT))})
    write_jsonl(p,rows)
    write_json(OUT/'annotations/annotation_freeze.json',{'annotation_sha256':sha(p),'source_sha256':sha(source),
        'rows':len(rows),'selection_used_attention':False,'position_scores_available':False,
        'effect_bearing_definition':'TE_VSD>0 (descriptive only)',
        'type_analysis':'center effects and positive indicators within exact target/state/distance before averaging by base and type'})
    print({'annotations':len(rows),'N_unique_bases':len(assets)})


def analyze():
    freeze=read_json(OUT/'annotations/annotation_freeze.json')
    p=OUT/'annotations/optional_recent_token_annotations.jsonl';assert sha(p)==freeze['annotation_sha256']
    annotations={(r['base_problem_id'],r['target_id'],r['state'],r['distance']):r for r in read_jsonl(p)}
    files=list((OUT/'raw/positions').glob('shard_*/*/target_*/*.json'));assert len(files)==96
    rows=[]
    for path in files:
        r=read_json(path);arms=r['arms'];base=r['base_problem_id'];t=r['target_id'];s=r['state']
        for name in arms:
            if not name.startswith('P'):continue
            d=int(name[1:]);a=annotations[(base,t,s,d)]
            rows.append({'base_problem_id':base,'target_id':t,'state':s,'distance':d,
                'generated_position':a['generated_zero_based_position'],'decoded_text':a['decoded_text'],
                'token_class':a['token_class'],'reasoning_role':a['reasoning_role'],
                'TE_VSD':vsd(arms,'N')-vsd(arms,name),
                'rds_drop':arms['N']['none']['rds']-arms[name]['none']['rds'],
                'alphaV_drop':arms['N']['none']['routing']['causal']['groups']['T']['mean_alpha_v_norm']-arms[name]['none']['routing']['causal']['groups']['T']['mean_alpha_v_norm']})
    # Freeze position effects before looking at category aggregations.
    pospath=OUT/'phase_f_secondary/recent_position_scan.jsonl';write_jsonl(pospath,rows)
    write_json(OUT/'phase_f_secondary/position_effect_freeze.json',{'position_sha256':sha(pospath),
        'raw_sha256':{str(p.relative_to(ROOT)):sha(p) for p in files},'rows':len(rows),'type_comparison_started':False})
    strata=defaultdict(list)
    for r in rows:strata[(r['target_id'],r['state'],r['distance'])].append(r)
    profile={};types=defaultdict(lambda:defaultdict(list));positive=defaultdict(lambda:defaultdict(list))
    for (t,s,d),rs in strata.items():
        avg=statistics.mean(r['TE_VSD'] for r in rs);positive_rate=statistics.mean(r['TE_VSD']>0 for r in rs)
        profile[f'{t}/{s}/{d}']=summarize_effect({r['base_problem_id']:r['TE_VSD'] for r in rs})
        for r in rs:
            key=f"{t}/{s}/{r['token_class']}"
            types[key][r['base_problem_id']].append(r['TE_VSD']-avg)
            positive[key][r['base_problem_id']].append(float(r['TE_VSD']>0)-positive_rate)
    summaries={key:{'distance_centered_effect':summarize_effect({b:statistics.mean(v) for b,v in bybase.items()}),
        'distance_centered_effect_bearing_fraction':summarize_effect({b:statistics.mean(v) for b,v in positive[key].items()}),
        'token_count':sum(len(v) for v in bybase.values())} for key,bybase in types.items()}
    write_json(OUT/'phase_f_secondary/token_type_analysis.json',{'descriptive_only':True,'position_profile':profile,
        'type_results':summaries,'distance_control':'exact target/state/distance centering; then one mean per base/type',
        'universal_trigger_type_claim':False,'annotation_used_attention':False})
    sink=[]
    # The historical source path is frozen Stage3C3 primary native M/R routing.
    for path in (ROOT/'outputs/stage3c3').glob('phase_a_query/**/result.json'):
        r=read_json(path)
        for t,conditions in r.get('target_results',{}).items():
            native=conditions['O']['native']
            sink.append({'base_problem_id':r['base_problem_id'],'target_id':t,
                'historical_sink_M':native['M']['routing']['causal']['groups']['sink']['mean_attention_mass'],
                'historical_sink_T':native['R']['routing']['causal']['groups']['sink']['mean_attention_mass'],
                'source':str(path.relative_to(ROOT))})
    write_json(OUT/'phase_f_secondary/sink_overlay_descriptive.json',{'descriptive_only':True,'sink_manipulated':False,'rows':sink,
        'interpretation':'historical observational overlay only; no sink-causality inference'})
    print({'position_rows':len(rows),'type_cells':len(summaries),'historical_sink_rows':len(sink)})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--phase',choices=['annotations','analyze'],required=True);globals()[p.parse_args().phase]()
