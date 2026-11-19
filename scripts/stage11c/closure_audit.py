"""Verify the Stage11C early-STOP evidence chain and actual resource release."""
from datetime import datetime
from pathlib import Path
import subprocess
import pyarrow.parquet as pq
from scripts.stage11c.common import ROOT, ARMS, load, save, sha, now
from scripts.stage11c.calibration_attempts import collect


def stamp(s):
    return datetime.fromisoformat(s)


def main():
    freeze = load(ROOT/'audit/spec_freeze.json')
    names = {'spec_sha256':'stage11c_thinking_vs_instruct_spec.md',
        'rule_sha256':'stage11c_development_selection_rule.json',
        'source_manifest_sha256':'stage11c_heldout_source_manifest.json'}
    for key,name in names.items():
        assert sha(ROOT/name) == freeze[key]
    assert sha(ROOT/'audit/cap_cases.json') == freeze['cap_cases_sha256']
    cfg=load(ROOT/'config.json')
    for path,digest in cfg['source_sha256'].items():
        assert sha(path)==digest,path
    review=load(ROOT/'stage11c_e_star_sufficiency_review.json')
    split=load(ROOT/'stage11c_primary_split.json')
    manifest=load(ROOT/'native_early_tasks.json')
    assert len({r['family_id'] for r in split['primary']+split['reserve']}) == split['eligible']
    assert stamp(review['at']) <= stamp(split['at']) <= stamp(manifest['at'])
    assert len(review['rows']) == review['reviewed']
    assert sum(r['eligible'] for r in review['rows']) == split['eligible']
    assert split['e_star_sha256'] == sha(ROOT/'stage11c_e_star_gold.parquet')
    assert split['review_sha256'] == sha(ROOT/'stage11c_e_star_sufficiency_review.json')
    for path,digest in review['round_sha256'].items():
        assert sha(path)==digest
        aggregate=load(path)
        assert stamp(aggregate['at']) <= stamp(review['at'])
        round_id=Path(path).stem.replace('evidence_round','')
        proposal_path=ROOT/'packets'/f'review_round{round_id}.json'
        assert sha(proposal_path)==aggregate['proposal_sha256']
        for reviewer,digest in aggregate['reviews_sha256'].items():
            annotation=ROOT/'annotations'/f'review_round{round_id}_{reviewer}.json'
            assert sha(annotation)==digest and load(annotation)['sealed']
            assert load(annotation)['model_outcomes_opened'] is False
    first_claims=[]
    for shard in manifest['shards']:
        for row in shard['rows']:
            assert sha(row['image']) == row['image_sha256']
            claim=load(ROOT/'native_early/claims'/row['task_id']/'owner.json')
            assert stamp(manifest['at']) < stamp(claim['at'])
            first_claims.append(claim['at'])
    native=pq.read_table(ROOT/'stage11c_native_td_results.parquet').to_pylist()
    oracle=pq.read_table(ROOT/'stage11c_oracle_td_results.parquet').to_pylist()
    assert len(native)==len(oracle)==2*split['primary_n']
    assert sum(r['status']=='COMPLETE' for r in native)==32
    assert all(r['correct'] is None for r in native if r['status']=='NOT_RUN')
    assert all(r['status']=='NOT_RUN' and r['correct'] is None for r in oracle)
    gate=load(ROOT/'stage11c_native_gate.json')
    assert gate['status']=='STOP_COMPLETION' and gate['performance_gate']=='NOT_EVALUATED'
    infer=load(ROOT/'stage11c_primary_inference.json')
    assert infer['status']=='NOT_ESTIMATED' and all(infer[k] is None for k in ['P1','P2','P3'])
    _,tasks,_,valid,_=collect()
    assert len(tasks)==len(valid)==48
    resource=load(ROOT/'stage11c_resource_accounting.json')
    assert resource['all_stage_allocations_released'] and resource['allocated_gpu_hours_observed']<=8
    active=subprocess.run(['squeue','-h','-u','hyunjin','-o','%A'],capture_output=True,text=True,check=True)
    active_ids=set(active.stdout.split())
    assert not active_ids.intersection(j['slurm_job_id'] for j in resource['jobs'])
    required=[*names.values(),'stage11c_e_star_gold.parquet','stage11c_e_star_sufficiency_review.json',
        'stage11c_primary_split.json','stage11c_cap_validation.json','stage11c_native_td_results.parquet',
        'stage11c_native_gate.json','stage11c_oracle_td_results.parquet','stage11c_oracle_validity.json',
        'stage11c_primary_inference.json','stage11c_neutral_control.json','stage11c_resource_accounting.json',
        'stage11c_summary.md']
    assert all((ROOT/name).exists() for name in required)
    save(ROOT/'audit/closure_validation.json',dict(at=now(),status='PASS',
        checks=['original_spec_rule_manifest_preserved','all_pinned_generation_sources_unchanged',
                'source_review_and_splits_frozen_before_first_primary_call','source_review_hashes_valid',
                'source_families_unique','native_image_hashes_match','48_unique_valid_calibration_calls',
                '32_valid_early_native_calls','unknowns_not_imputed','oracle_not_run',
                'primary_endpoints_not_estimated','all_allocations_released','hard8GPUh_respected'],
        first_primary_claim=min(first_claims),source_freeze_at=split['at'],
        required_artifact_sha256={name:sha(ROOT/name) for name in required},
        figure_sha256={p.name:sha(p) for p in (ROOT/'figures').glob('*')},
        no_next_research_action=True))
    print('CLOSURE_VALIDATION_PASS')


if __name__=='__main__':
    main()
