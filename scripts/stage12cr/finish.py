"""Close the two authorized branches after their fixed gates and GPU release."""
from pathlib import Path
import subprocess
import numpy as np
import pandas as pd

from scripts.stage12cr.common import ROOT, load, save, sha, now
from scripts.stage12cr.resources_v2 import account
from scripts.stage12cr.seal import preservation
from scripts.stage12cr.review import checked_generation
from scripts.stage12cr.report import responses


def main():
    assert not (ROOT/'audit/final_verification.json').exists()
    p1 = load(ROOT/'stage12tr_same12_decision.json')
    phases = ['same12'] + (['fresh12'] if p1['pass'] else [])
    decision = load(ROOT/f'stage12tr_{phases[-1]}_decision.json')['decision']
    if decision == 'THINKING_REGIME_VALIDATED':
        assert Path('plan/stage12ts_thinking_scientific_rescue_plan.md').exists()
    tasks = load(ROOT/'stage12cr_cot_manifest.json')['tasks']
    tasks += [t for phase in phases for t in load(ROOT/f'stage12tr_{phase}_manifest.json')['rows']]
    for t in tasks:
        _, checks = checked_generation(t)
        assert all(checks.values()), t['task_id']
    assert len(list((ROOT/'generations').glob('C_*/result.json'))) == 49
    assert len(list((ROOT/'generations').glob('T_*/result.json'))) == 12*len(phases)
    assert not list((ROOT/'audit/first_scores').glob('T_*.json'))
    assert not list((ROOT/'audit/correctness_packets').glob('T*'))
    preserved = preservation()
    for name in ['denominator_seal','trace_seal','correctness_seal']:
        obj = load(ROOT/f'audit/{name}.json')
        for group in ['annotation_hashes','label_hashes','output_hashes']:
            for p, h in obj.get(group, {}).items():
                assert sha(p) == h, p
    ledger = account('closure')
    assert ledger['all_released']
    assert all(r['status']=='COMPLETED' and r['exit_code']=='0:0' for r in ledger['jobs'])
    assert all(r['allocated_gpu_hours']<=r['hard_limit_gpu_hours'] for r in ledger['phases'].values())
    ids = [r['slurm_job_id'] for r in ledger['jobs']]
    live = subprocess.run(['squeue','-h','-u','hyunjin','-o','%i'],capture_output=True,text=True,check=True).stdout.split()
    assert not set(ids)&set(live)
    for wanted, name in [(['cot'],'stage12cr_cot'), (['same12','fresh12'],'stage12tr')]:
        jobs = []
        for r in ledger['jobs']:
            if r['phase'] not in wanted:
                continue
            r = dict(r)
            w = ROOT/'workers'/r['slurm_job_id']
            env = load(w/'environment.json')
            engine = load(w/'engine_ready.json')
            end = load(w/'exit.json')
            assert end['complete']
            r.update(observed_gpu=env['gpu'], total_gpu_memory_bytes=env['total_gpu_memory'],
                     packages=env['packages'], dtype=engine['dtype'], runtime=engine['runtime'],
                     checkpoint_revision=env['model']['revision'],
                     worker_seconds=end['seconds'], calls=end['calls'],
                     peak_gpu_memory_bytes=None,
                     memory_note='Peak not instrumented; startup model/KV memory measurements retained in Slurm log.',
                     receipts={str(p):sha(p) for p in [w/'environment.json',w/'engine_ready.json',w/'exit.json']})
            jobs.append(r)
        generations = [load(p) for p in (ROOT/'generations').glob('*/generation.json')
                       if load(p)['arm']==('C' if wanted==['cot'] else 'T')]
        lengths = [g['tokens'] for g in generations]
        latencies = [g['request_latency_seconds'] for g in generations]
        save(ROOT/f'{name}_resource_accounting.json',dict(
            at=now(),jobs=jobs,phases={p:ledger['phases'][p] for p in wanted},
            all_allocations_released=True,includes_startup=True,
            allocated_gpu_hours=sum(r['allocated_gpu_hours'] for r in jobs),
            new_calls=len(generations),reused_calls=12 if wanted==['cot'] else 0,
            total_new_generated_tokens=sum(lengths),
            new_token_quantiles=dict(zip(['min','q25','median','q75','max'],np.percentile(lengths,[0,25,50,75,100]).tolist())),
            latency_seconds_median=float(np.median(latencies)),latency_seconds_max=max(latencies),
            latency_note='Per-request elapsed latency in concurrent batch; sums are not GPU time.',
            environments=['.venv (CPU)', '.venv/official_eval (GPU)'],
            downloads=0,retries=0,third_cap_attempted=False))
    responses()
    for stem in ['stage12cr_cot', 'stage12tr']:
        resource = load(ROOT/f'{stem}_resource_accounting.json')
        summary = ROOT/f'{stem}_summary.md'
        value = summary.read_text()
        marker = '[Full unabridged responses]' if stem=='stage12cr_cot' else '[Full responses]'
        note = (f"Final allocated compute: {resource['allocated_gpu_hours']:.6f} GPU-hours, "
                f"{resource['new_calls']} new calls, {resource['reused_calls']} reused calls. "
                "All allocations completed exit0 and were released. No retries or downloads.\n\n")
        if stem=='stage12tr':
            note += ('Fresh-job engine teardown emitted a client/NCCL warning after all12 output and '
                     'worker-exit receipts were saved; Slurm completed exit0. No generation was retried.\n\n')
            if decision=='THINKING_REGIME_VALIDATED':
                note += ('Section27 deliverable: [Stage12T-S draft](../../../plan/stage12ts_thinking_scientific_rescue_plan.md) '
                         'created for separate user authorization; not launched.\n\n')
        assert marker in value
        summary.write_text(value.replace(marker, note+marker, 1))
    required_a=['scientific_spec.md','manifest.json','integrity.parquet','results.parquet',
                'scoring_blind.parquet','second_review.json','trace_evidence_states.parquet',
                'pathology.parquet','primary_inference.json','decision.json',
                'resource_accounting.json','summary.md']
    required_b=['completion_spec.md','same12_manifest.json','fresh12_manifest.json',
                'same12_results.parquet','prefix_diagnostics.parquet','same12_decision.json',
                'pathology_labels.parquet','resource_accounting.json','summary.md']
    if p1['pass']:
        required_b += ['fresh12_results.parquet','fresh12_decision.json']
    paths=[ROOT/('stage12cr_cot_'+s) for s in required_a]+[ROOT/('stage12tr_'+s) for s in required_b]
    assert all(p.exists() and p.stat().st_size for p in paths)
    assert len(list((ROOT/'figures').glob('*.png')))==5
    assert len(list((ROOT/'figures').glob('*.pdf')))==5
    assert len(pd.read_parquet(ROOT/'stage12cr_cot_trace_evidence_states.parquet'))==26
    save(ROOT/'audit/final_verification.json',dict(at=now(),pass_all=True,preserved=preserved,
         input_receipts_verified=len(tasks),new_calls=49+12*len(phases),reused_c_calls=12,
         thinking_correctness_opened=False,thinking_phases_run=phases,
         required_A_artifacts=len(required_a),required_B_artifacts=len(required_b),
         required_artifact_hashes={str(p):sha(p) for p in paths},
         supporting_analysis_source_hashes={str(p):sha(p) for p in Path('scripts/stage12cr').glob('*.py')},
         total_allocated_gpu_hours=sum(r['allocated_gpu_hours'] for r in ledger['jobs']),
         all_allocations_released=True,next_experiment_launched=False))
    print('Both authorized branches closed:', decision)


if __name__=='__main__':
    main()
