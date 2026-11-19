"""Close completed, reviewed science only; never fabricate pending results."""
import subprocess
from pathlib import Path
import pandas as pd
from scripts.stage12us.common import ROOT,load,save,sha,now
from scripts.stage12us.launch import account
from scripts.stage12us.review import tasks,checked

REQUIRED=['reasoning_state_transfer_spec.md','primary_b4_manifest.json','secondary_b1_manifest.json',
 'source_prefixes.json','prefix_content_audit.json','canonical_trace_hashes.json','technical_validation.json',
 'transfer_results.parquet','question_only_controls.parquet','shuffled_trace_controls.parquet',
 'scoring_review.json','item_interpretations.parquet','primary_inference.json','decision.json',
 'resource_accounting.json','summary.md']


def main():
    assert load(ROOT/'stage12us_decision.json')['stage_complete']
    assert load(ROOT/'stage12us_scoring_review.json')['all_agree']
    all_tasks=tasks('technical')+tasks('science');assert len(all_tasks)==168
    for t in all_tasks:checked(t)
    assert len(list((ROOT/'generations').glob('*/result.json')))==168
    for name,n in [('transfer_results',84),('question_only_controls',42),('shuffled_trace_controls',30),('item_interpretations',7)]:
        assert len(pd.read_parquet(ROOT/f'stage12us_{name}.parquet'))==n
    ledger=account('final_closure');assert ledger['all_released'] and len(ledger['jobs'])==8
    assert ledger['allocated_gpu_hours']<=7
    assert all(r['status']=='COMPLETED' and r['exit_code']=='0:0' for r in ledger['jobs'])
    live=subprocess.run(['squeue','-h','-u','hyunjin','-o','%i'],capture_output=True,text=True,check=True).stdout.split()
    assert not {r['slurm_job_id'] for r in ledger['jobs']}.intersection(live)
    for r in ledger['jobs']:
        w=ROOT/'workers'/r['slurm_job_id'];env=load(w/'environment.json');engine=load(w/'engine_ready.json');end=load(w/'exit.json')
        assert end['complete']
        r.update(environment=env,dtype=engine['dtype'],runtime=engine['runtime'],worker_calls=end['calls'],
                 worker_seconds=end['seconds'],peak_gpu_memory_bytes=None,
                 memory_note='Startup model/KV memory in preserved Slurm log; peak allocator value not instrumented.')
    save(ROOT/'stage12us_resource_accounting.json',dict(**ledger,includes_startup=True,technical_calls=12,scientific_calls=156,
         retries=0,downloads=0,all_allocations_released=True,observer_gpu_count=0,
         observer_receipt='audit/observer_launch.json',
         latency_note='Per-request times overlap within batches and must not be summed as GPU time.'))
    from scripts.stage12us.report import figures,reading_copies,summary
    figures();reading_copies();summary()
    history=load(ROOT/'audit/preserved_history.json')['files']
    for p,h in history.items():assert sha(p)==h,p
    for p,h in load(ROOT/'audit/source_prefix_seal.json')['hashes'].items():assert sha(p)==h,p
    artifacts=[ROOT/f'stage12us_{name}' for name in REQUIRED]
    assert all(p.exists() and p.stat().st_size for p in artifacts)
    assert len(list((ROOT/'figures').glob('U*.png')))==len(list((ROOT/'figures').glob('U*.pdf')))==4
    assert len(list(Path('reports/stage12us/v1').glob('*_r*.md')))==156
    save(ROOT/'audit/final_verification.json',dict(at=now(),pass_all=True,prior_files_unchanged=len(history),
         calls_verified=168,required_artifacts=16,artifact_hashes={str(p):sha(p) for p in artifacts},
         all_gpu_allocations_released=True,next_experiment_launched=False))
    print('Closed',load(ROOT/'stage12us_decision.json')['decision'],ledger['allocated_gpu_hours'],'GPUh')


if __name__=='__main__':main()
