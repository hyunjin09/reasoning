"""Independent raw-manifest/count/hash checks for a technical STOP closure."""
from datetime import datetime
from pathlib import Path
import subprocess
import pandas as pd
from scripts.stage11cr.common import ROOT,OLD,load,save,sha,now,verify_frozen
from scripts.stage11cr.protocol import token_comparison,completion_gate


def main():
    cfg=verify_frozen()
    old_audit=load(OLD/'audit/closure_validation.json')
    for group in ['required_artifact_sha256','figure_sha256']:
        base=OLD/'figures' if group=='figure_sha256' else OLD
        for p,d in old_audit[group].items():assert sha(base/p)==d,p
    for p,d in load(OLD/'audit/final_state_check.json')['source_code_sha256'].items():assert sha(p)==d,p
    for p,d in load(ROOT/'audit/pre_execution_freeze.json')['files'].items():assert sha(p)==d,p
    for p,d in load(ROOT/'audit/analysis_code_freeze.json')['source_sha256'].items():assert sha(p)==d,p
    frozen=load(ROOT/'stage11cr_known_good_manifest.json')
    assert len(frozen['rows'])==12
    for r in frozen['rows']:
        old=load(Path(r['historical_dir'])/'generation.json')
        new=load(ROOT/'known_good/results'/r['task_id']/'generation.json')
        assert token_comparison(old['generated_token_ids'],new['generated_token_ids'])['exact_token_identity']
    required=['stage11cr_repair_spec.md','stage11cr_historical_runtime_comparison.json',
        'stage11cr_known_good_manifest.json','stage11cr_known_good_reproduction.parquet',
        'stage11cr_discrepancy_audit.json','stage11cr_repaired_protocol.json','stage11cr_nonprimary_validation.json',
        'stage11cr_native_td_results.parquet','stage11cr_native_validity_gate.json',
        'stage11cr_native_performance_gate.json','stage11cr_primary_inference.json',
        'stage11cr_resource_accounting.json','stage11cr_summary.md','stage11cr_cap_protocol_amendment_v1.md']
    for name in required:assert (ROOT/name).exists(),name
    assert load(ROOT/'stage11cr_repaired_protocol.json')['pass']
    r3=load(ROOT/'stage11cr_nonprimary_validation.json')
    assert completion_gate(r3['rows'],'nonprimary')['status']=='STOP'
    split=load(OLD/'stage11c_primary_split.json')
    assert len(split['primary'])==80 and len(split['reserve'])==40
    pool=load(ROOT/'nonprimary_cases.json')['rows']
    assert {r['family_id'] for r in pool}.isdisjoint(r['family_id'] for r in split['primary']+split['reserve'])
    for queue,manifest_name,n in [('known_good','run_known_good_tasks.json',12),('diagnostic','diagnostic_tasks.json',4),
                                  ('nonprimary40960','nonprimary40960_tasks.json',24)]:
        m=load(ROOT/manifest_name)
        tasks=[r for s in m['shards'] for r in s['rows']]
        assert len(tasks)==n and len({r['task_id'] for r in tasks})==n
        for task in tasks:
            dest=ROOT/queue/'results'/task['task_id'];rr=load(dest/'result.json')
            assert not rr['budget_interrupted']
            assert rr['manifest_sha256']==sha(ROOT/manifest_name)
            assert rr['input_sha256']==sha(dest/'input.json') and rr['generation_sha256']==sha(dest/'generation.json')
            assert rr['tokens']==len(load(dest/'generation.json')['generated_token_ids'])
            assert datetime.fromisoformat(m['at'])<datetime.fromisoformat(rr['at'])
        for p,d in m['source_sha256'].items():assert sha(p)==d,p
    assert datetime.fromisoformat(load(ROOT/'audit/cap_protocol_correction.json')['at'])<datetime.fromisoformat(load(ROOT/'nonprimary40960_tasks.json')['at'])
    assert datetime.fromisoformat(load(ROOT/'stage11cr_repaired_protocol.json')['at'])<datetime.fromisoformat(load(ROOT/'nonprimary40960_tasks.json')['at'])
    native=pd.read_parquet(ROOT/'stage11cr_native_td_results.parquet')
    assert len(native)==160 and native['correct'].isna().all() and native['committed_final'].isna().all()
    assert set(native['status'])=={'NOT_RUN'}
    assert not (ROOT/'native/results').exists() and not (ROOT/'oracle/results').exists()
    inference=load(ROOT/'stage11cr_primary_inference.json')
    assert inference['status']=='NOT_ESTIMATED' and all(inference[k] is None for k in ['P1','P2','P3'])
    resource=load(ROOT/'stage11cr_resource_accounting.json')
    assert resource['all_stage_allocations_released'] and resource['allocated_gpu_hours_observed']<=9
    live=subprocess.run(['squeue','-u','hyunjin','-h','-o','%i'],capture_output=True,text=True,check=True).stdout.split()
    assert set(live).isdisjoint(str(j['slurm_job_id']) for j in resource['jobs'])
    figures=list((ROOT/'figures').glob('*.png'))+list((ROOT/'figures').glob('*.pdf'));assert len(figures)==4
    save(ROOT/'audit/closure_validation.json',dict(at=now(),status='PASS',
        checks=['old_11c_artifacts_figures_source_code_unchanged','preexecution_freeze_preserved_with_versioned_cap_correction',
        '12_exact_historical_replays','4_fixed_completion_only_diagnostics','24_nonprimary_calls_on_original12_cases',
        'nonprimary_gate_recalculated_from_sealed_rows','no_primary_oracle_execution','unknowns_not_imputed_as_wrong',
        'all_task_and_source_hashes_match','repair_and_cap_correction_predate_R3','all_allocations_released_below9GPUh'],
        artifact_sha256={str(ROOT/n):sha(ROOT/n) for n in required},figure_sha256={str(p):sha(p) for p in figures},
        code_sha256={str(p):sha(p) for p in Path('scripts/stage11cr').glob('*.py')},no_next_action=True))
    print('CLOSURE_AUDIT_PASS')


if __name__=='__main__':main()
