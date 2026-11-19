"""Join sealed labels, never regenerate or choose outcomes during analysis."""
import json
from collections import Counter
import pandas as pd
from scripts.stage12bs.common import ROOT, load, save, sha, now
from scripts.stage12bs.inference import infer, proportion
from scripts.stage12bs.protocol import failure_type, persistence
from scripts.stage12b.protocol import profile


def main():
    seal=load(ROOT/'audit/correctness_seal.json')
    assert all(sha(p)==h for p,h in {**seal['label_hashes'],**seal['output_hashes']}.items())
    ds=load(ROOT/'audit/denominator_seal.json')
    full=load(ROOT/'stage12bs_full_manifest.json')
    integrity={r['task_id']:r for r in pd.read_parquet(ROOT/'stage12bs_integrity_results.parquet').to_dict('records')}
    scores={}
    for name in ['evidence','native','oracle']:
        scores.update({r['task_id']:r for r in pd.read_parquet(ROOT/f'stage12bs_{name}_scoring_blind.parquet').to_dict('records')})
    rows=[]; pathrows=[]
    for r in full['rows']:
        i=r['item_id']; ts={a:integrity[f'{a}_{i}_v1'] for a in 'ENO'}
        ss={a:scores[f'{a}_{i}_v1'] for a in 'ENO'}
        rr=dict(item_id=i,family_id=r['family_id'],subject=r['subject'],level=r['level'],answer_type=r['answer_type'],
                reused=i not in full['remaining_ids'],development=i in full['development_ids'],validation=i in full['validation_ids'])
        for a in 'ENO':
            valid=bool(ts[a]['INPUT_VALID'] and ts[a]['SCOREABLE'])
            v=ss[a]['correct'];assert valid==(v is not None)
            rr[a.lower()]=bool(v) if valid else None
            rr[f'{a}_outcome']=ts[a]['extracted_outcome']
            rr[f'{a}_tokens']=ts[a]['tokens']
            rr[f'{a}_cap']=ts[a]['cap_hit']
            if a!='E':
                rr.update({f'{a}_{k}':bool(ts[a][k]) for k in ['R1','R2','R3','R4','R5']})
        rr['complete_profile']=all(rr[k] is not None for k in ['e','n','o'])
        rr['complete_native_failure']=rr['complete_profile'] and not rr['n']
        rr['bottleneck']=profile(rr['e'],rr['n'],rr['o']) or ('NATIVE_SUCCESS' if rr['complete_profile'] else 'TECHNICAL_UNRESOLVED')
        atoms=list(ss['E']['atoms']); rr['e_atom_labels_json']=json.dumps(atoms)
        rr['e_has_incorrect_atom']='INCORRECT' in atoms
        rr['e_has_unresolved_atom']='UNRESOLVED' in atoms
        pr=dict(item_id=i,family_id=r['family_id'],bottleneck=rr['bottleneck'])
        for a in 'NO':
            labs={k:bool(ts[a][k]) for k in ['R1','R2','R3','R4','R5']}
            pr.update({f'{a}_{k}':v for k,v in labs.items()})
            pr[f'{a}_valid']=ts[a]['TECHNICALLY_VALID']
            pr[f'{a}_correct']=rr[a.lower()]
            pr[f'{a}_failure_type']=failure_type(labs) if rr[a.lower()] is False else None
        nt={k for k in ['R1','R2','R3'] if pr[f'N_{k}']}
        ot={k for k in ['R1','R2','R3'] if pr[f'O_{k}']}
        pr['native_pathology_types']=sorted(nt);pr['oracle_pathology_types']=sorted(ot)
        pr['oracle_persistence']=persistence(nt,ot,pr['O_valid']) if nt else None
        pr['evidence_resolved_pathological_oracle_failure']=rr['e'] is True and rr['o'] is False and bool(ot)
        pr['rescued_pathologies']=[k for k in ['R1','R2','R3'] if rr['n'] is False and rr['o'] is True and pr[f'N_{k}'] and not pr[f'O_{k}']]
        rows.append(rr);pathrows.append(pr)
    assert sorted(r['family_id'] for r in rows if r['n'] is not None)==ds['native_scoreable_families']
    assert sorted(r['family_id'] for r in rows if r['complete_profile'])==ds['complete_profile_families']
    result=infer(rows)
    result.update(at=now(),n_families=61,native_accuracy=proportion(sum(r['n'] is True for r in rows),sum(r['n'] is not None for r in rows)),
                  oracle_accuracy=proportion(sum(r['o'] is True for r in rows),sum(r['o'] is not None for r in rows)),
                  evidence_all_correct=proportion(sum(r['e'] is True for r in rows),sum(r['e'] is not None for r in rows)),
                  complete_profile_failures=sum(r['complete_native_failure'] for r in rows))
    result['evidence_minus_composition']={b:dict(any_incorrect_atom=sum(r['e_has_incorrect_atom'] for r in rows if r['bottleneck']==b),
        unresolved_without_incorrect=sum(r['e_has_unresolved_atom'] and not r['e_has_incorrect_atom'] for r in rows if r['bottleneck']==b)) for b in ['B1','B4']}
    result['pathology']=dict(persistence_counts=dict(Counter(p['oracle_persistence'] for p in pathrows if p['oracle_persistence'])),
        evidence_resolved_pathological_oracle_failure_ids=[p['item_id'] for p in pathrows if p['evidence_resolved_pathological_oracle_failure']],
        rescued_pathology_ids={k:[p['item_id'] for p in pathrows if k in p['rescued_pathologies']] for k in ['R1','R2','R3']},
        failure_types={a:dict(Counter(p[f'{a}_failure_type'] for p in pathrows if p[f'{a}_failure_type'])) for a in 'NO'})
    sensitivity={name:infer([r for r in rows if r['item_id'] not in excluded]) for name,excluded in
        [('S1_exclude_development',full['development_ids']),('S2_exclude_all_technical',full['development_ids']+full['validation_ids'])]}
    oracle=load('outputs/stage12b/v1/stage12b_oracle_integrity_review.json')
    decision=result['decision'] if ds['full_gate']['pass'] and oracle['pass'] else 'TECHNICAL_BREAKDOWN'
    recommendations={
      'PROFILE_INFORMATIVE':'Freeze the Stage 12B-S bottleneck labels and run prompted CoT plus native Thinking on the same families to test selective rescue by failure type.',
      'PROFILE_SPARSE':'Build a fresh harder E*-annotated cohort before testing selective CoT/Thinking rescue.',
      'TECHNICAL_BREAKDOWN':'Diagnose the specific full-cohort scoreability/integrity failure without changing scientific bottleneck definitions.'}
    result['decision']=decision
    dec=dict(at=now(),decision=decision,scientifically_scored_native_failures=result['endpoints']['P1']['numerator'],
        complete_profile_native_failures=result['complete_profile_failures'],classes=result['classes'],
        full_validity_gate=ds['full_gate'],oracle_integrity_pass=oracle['pass'],recommendation=recommendations[decision],
        follow_on_launched=False,labels_frozen_before_pairing=True)
    for name,data in [('primary_inference',result),('sensitivity_results',sensitivity),('profile_decision',dec)]:save(ROOT/f'stage12bs_{name}.json',data)
    pd.DataFrame(rows).to_parquet(ROOT/'stage12bs_failure_profiles.parquet',index=False)
    pd.DataFrame(pathrows).to_parquet(ROOT/'stage12bs_pathology_analysis.parquet',index=False)
    save(ROOT/'audit/paired_analysis_opened.json',dict(at=now(),correctness_seal_sha256=sha(ROOT/'audit/correctness_seal.json')))
    print(json.dumps(dict(decision=decision,classes=result['classes'],endpoints=result['endpoints'],pathology=result['pathology'],sensitivity={k:v['classes'] for k,v in sensitivity.items()}),indent=2))


if __name__=='__main__':main()
