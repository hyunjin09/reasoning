"""Actual allocation accounting, including preserved failed technical startup."""
from datetime import datetime
from scripts.stage10a.common import ROOT,load,save,now
from scripts.stage9a5.account import seconds


def main():
    best={}
    for path in sorted((ROOT/'audit').glob('resource_snapshot_*.json')):
        for r in load(path)['jobs']:
            name=r['queue']['id']; f=r['slurm_fields']; old=best.get(name)
            terminal=f.get('JobState') in ('COMPLETED','FAILED','CANCELLED','TIMEOUT','OUT_OF_MEMORY')
            if f.get('RunTime') and (old is None or seconds(f['RunTime'])>seconds(old['slurm_fields']['RunTime']) or
                (seconds(f['RunTime'])==seconds(old['slurm_fields']['RunTime']) and terminal)):
                best[name]=dict(r,snapshot=str(path))
    jobs=[];gpu_seconds=0;events=[]
    expected={r['id'] for r in load('state/gpu_experiment_queue.json')['jobs'] if r['id'].startswith('stage10a_') and r['gpus']}
    for name,r in sorted(best.items()):
        q=r['queue'];f=r['slurm_fields'];g=q['gpus'];elapsed=seconds(f['RunTime'])
        jobs.append(dict(id=name,slurm_job_id=q['slurm_job_id'],gpus=g,runtime_seconds=elapsed,state=f['JobState'],
            exit_code=f.get('ExitCode'),node=f.get('NodeList'),start=f.get('StartTime'),end=f.get('EndTime'),
            command=q.get('command'),snapshot=r['snapshot']))
        if g:
            if name=='stage10a_validate':assert f['JobState']=='FAILED' and f['ExitCode']!='0:0'
            else:assert f['JobState']=='COMPLETED' and f['ExitCode']=='0:0',(name,f)
            gpu_seconds+=g*elapsed
            events.extend([(datetime.fromisoformat(f['StartTime']),g),(datetime.fromisoformat(f['EndTime']),-g)])
    assert expected=={r['id'] for r in jobs if r['gpus']},'Missing allocation records'
    active=peak=0
    for _,change in sorted(events):active+=change;peak=max(peak,active)
    assert peak<=8 and active==0
    generations=[(p,load(p)) for p in ROOT.glob('*/results/*/generation.json')]
    receipts=[load(p) for p in ROOT.glob('*/results/*/result.json')]
    counts={}
    for p,g in generations:stage=p.parts[-4];counts[stage]=counts.get(stage,0)+1
    bundles=[load(p) for p in (ROOT/'gate_a/bundles').glob('*.json')]
    save(ROOT/'stage10a_resource_accounting.json',dict(at=now(),jobs=jobs,allocated_gpu_hours=gpu_seconds/3600,
        counts=counts,scientific_generations=len(generations),generation_gpu_hours=sum(g['runtime_seconds'] for _,g in generations)/3600,
        actual_continuation_tokens=sum(g['continuation_tokens'] for _,g in generations),
        native_prefix_replay_seconds=sum(b['native_prefix_seconds'] for b in bundles),
        peak_allocated_bytes=max(r['peak_allocated_bytes'] for r in receipts),peak_reserved_bytes=max(r['peak_reserved_bytes'] for r in receipts),
        max_authorized_concurrent_gpus=8,observed_peak_gpus=peak,all_gpu_jobs_terminal=True,
        known_resolved_failure='stage10a_validate: text-only processor returned all-zero mm_token_type_ids; one diagnostic, regression test and eight successful retry validations.',
        budget=dict(primary_target_gpu_hours=7,hard_projected_limit_gpu_hours=10),
        note='Allocation hours include hashing, model loading, technical validation, failed startup and workers that found no unclaimed bundles. Reused outputs do not count as new generations.'))
    print('ALLOCATED_GPU_HOURS',gpu_seconds/3600,'GENERATIONS',len(generations),'PEAK_GPUS',peak,flush=True)


if __name__=='__main__':main()
