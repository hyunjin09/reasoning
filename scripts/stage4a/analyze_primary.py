"""Freeze primary causal evidence and evaluate the predeclared trigger gate."""
import argparse
from datetime import datetime, timezone
from scripts.stage4a.prepare_config import ROOT, OUT, read_json, read_jsonl, write_json, write_jsonl, sha
from scripts.stage4a.run_scores import verify_freeze
from visual_reasoning.stage4a.analysis import primary_contrasts, primary_family, failure_phenotypes, EVENTS


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run-id',required=True);args=parser.parse_args()
    if (OUT/'phase_b_source_switch/primary_freeze.json').exists():
        raise FileExistsError('Primary evidence is already frozen')
    verify_freeze()
    manifest=read_jsonl(OUT/'cohort/primary_manifest.jsonl')
    paths=sorted((OUT/'raw'/args.run_id).glob('shard_*/*/OO/*.json'))
    rows=[read_json(p) for p in paths]
    assert len(rows)==144 and {(r['base_problem_id'],r['event']) for r in rows}=={(r['base_problem_id'],e) for r in manifest for e in EVENTS}
    by={b['base_problem_id']:{r['event']:r for r in rows if r['base_problem_id']==b['base_problem_id']} for b in manifest}
    all_arms=[a for r in rows for a in r['arms'].values()]
    assert all(a['finite'] and all(s['finite'] for s in a['step_audits']) for a in all_arms)
    w2={b:primary_contrasts(rs,2) for b,rs in by.items()}
    w8={b:primary_contrasts(rs,8) for b,rs in by.items()}
    family=primary_family(w2)
    gate=family['Switch_AB']['robust_positive'] or family['Refresh_BA']['robust_positive']
    for w in (2,8):
        effects=w2 if w==2 else w8
        for x in ('A','B'):
            write_jsonl(OUT/f'phase_b_source_switch/w{w}_roi_{x.lower()}.jsonl',[
                {'base_problem_id':b,'event':e,'VSD':effects[b]['VSD'][e][x],
                 'native_D':by[b][e]['arms']['N']['D'],'suppressed_D':by[b][e]['arms'][f'{x}_W{w}']['D']} for b in by for e in EVENTS])
    write_jsonl(OUT/'phase_b_source_switch/joint_ab.jsonl',[{'base_problem_id':b,'event':e,'VSD_AB':r['joint_AB'][e],
        'single_A':r['VSD'][e]['A'],'single_B':r['VSD'][e]['B']} for b,r in w2.items() for e in EVENTS])
    write_jsonl(OUT/'phase_b_source_switch/irrelevant_controls.jsonl',[{'base_problem_id':b,'event':e,
        'VSD_I':r['irrelevant_VSD'][e],'demanded_VSD':r['VSD'][e]['B' if e=='B' else 'A']} for b,r in w2.items() if 'irrelevant_VSD' in r for e in EVENTS])
    write_json(OUT/'phase_b_source_switch/dynamic_selectivity.json',{'W2':w2,'W8':w8,'primary_family_at_gate':family})
    write_json(OUT/'analysis/base_level_dynamic_classes.json',{'floor':.05,'W2':{b:r['dynamic'] for b,r in w2.items()},'W8_sensitivity':{b:r['dynamic'] for b,r in w8.items()}})
    write_json(OUT/'analysis/native_failure_phenotypes.json',{'basis':'W2 causal scores only; descriptive labels can overlap',
        'floor':.05,'bases':{b:failure_phenotypes(r) for b,r in w2.items()}})
    telemetry=[];sink=[];entropy=[];residual=[];correct=[]
    for row in rows:
        key={k:row[k] for k in ('base_problem_id','event')};native=row['arms']['N']
        telemetry.append({**key,'layers':native['telemetry'],'group_aliases':native['passive_aliases']})
        for layer,roles in native['telemetry'].items():
            for role,r in roles.items():
                sink.append({**key,'layer':layer,'head_set':role,'mass':r['groups']['sink']['mean_attention_mass']})
                entropy.append({**key,'layer':layer,'head_set':role,'attention_entropy':r['mean_attention_entropy'],'predictive_entropy':native['predictive_entropy']})
        residual.append({**key,'layer_residual_norms':native['residual_norms']})
        correct.append({**key,'local_fact_reference_correct':True,'local_native_preferred':native['D']>0,'native_D':native['D'],
                        'final_correct':row['final_correct'],'VSD':w2[row['base_problem_id']]['VSD'][row['event']]})
    for file,data in [('attention_qk_alphav',telemetry),('sink_mass',sink),('entropy',entropy),('residual_norms',residual),('correctness',correct)]:
        write_jsonl(OUT/f'telemetry/{file}.jsonl',data)
    frozen={'frozen_at':datetime.now(timezone.utc).isoformat(),'run_id':args.run_id,'N_unique_bases':48,
        'raw_sha256':{str(p.relative_to(ROOT)):sha(p) for p in paths},'primary_family':family,
        'phase_c_gate_open':gate,'gate_rule':'robust Switch_AB OR Refresh_BA; nine-test Holm with unrun trigger slots p=1',
        'dynamic_W2_count':sum(r['dynamic'] for r in w2.values()),'dynamic_W8_count':sum(r['dynamic'] for r in w8.values())}
    write_json(OUT/'phase_b_source_switch/primary_freeze.json',frozen)
    print({k:v for k,v in frozen.items() if k!='raw_sha256'})


if __name__=='__main__':main()
