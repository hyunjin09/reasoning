"""Count Stage10B allocations, including preparation and any passive repair."""
from datetime import datetime
from scripts.stage10b.common import ROOT,load,save,now
from scripts.stage9a5.account import seconds


def main():
    best={};terminal={'COMPLETED','FAILED','CANCELLED','TIMEOUT','OUT_OF_MEMORY'}
    for path in sorted((ROOT/'audit').glob('resource_snapshot_*.json')):
        for r in load(path)['jobs']:
            name=r['queue']['id'];f=r['slurm_fields'];old=best.get(name)
            if not f.get('RunTime'):continue
            elapsed=seconds(f['RunTime'])
            if old is None or elapsed>seconds(old['slurm_fields']['RunTime']) or (
                elapsed==seconds(old['slurm_fields']['RunTime']) and f.get('JobState') in terminal):
                best[name]=dict(r,snapshot=str(path))
    expected={j['id'] for j in load('state/gpu_experiment_queue.json')['jobs'] if j['id'].startswith('stage10b_') and j['gpus']}
    jobs=[];timeline=[];gpu_seconds=0
    for name,r in sorted(best.items()):
        q=r['queue'];f=r['slurm_fields'];g=q['gpus'];elapsed=seconds(f['RunTime'])
        jobs.append(dict(id=name,slurm_job_id=q['slurm_job_id'],gpus=g,runtime_seconds=elapsed,state=f['JobState'],
            exit_code=f.get('ExitCode'),node=f.get('NodeList'),start=f.get('StartTime'),end=f.get('EndTime'),
            command=q.get('command'),snapshot=r['snapshot']))
        if g:
            assert f['JobState'] in terminal,(name,f)
            gpu_seconds+=g*elapsed
            timeline.extend([(datetime.fromisoformat(f['StartTime']),g),(datetime.fromisoformat(f['EndTime']),-g)])
    assert expected=={r['id'] for r in jobs if r['gpus']},'Missing GPU allocation records'
    active=peak=0
    for _,change in sorted(timeline):active+=change;peak=max(peak,active)
    assert active==0 and peak<=8 and gpu_seconds<3600
    repair=[load(p) for p in (ROOT/'repair').glob('*/complete.json')]
    assert len(repair)<=32 and all(r['new_generated_tokens']==0 for r in repair)
    independent=load(ROOT/'audit/semantic_independent_passes_frozen.json')
    save(ROOT/'stage10b_resource_accounting.json',dict(at=now(),jobs=jobs,allocated_gpu_hours=gpu_seconds/3600,
        new_generations=0,causal_interventions=0,passive_repaired_trajectories=len(repair),
        passive_worker_seconds=sum(r['seconds'] for r in repair),
        maximum_cuda_memory_bytes=max([r['max_cuda_memory_bytes'] for r in repair],default=0),
        observed_peak_gpus=peak,authorized_gpu_ceiling=8,all_gpu_jobs_terminal=True,
        annotation=dict(independent_agent_passes=2,reviewer_trajectory_judgments=sum(len(v) for v in independent['reviews'].values()),
                        manual_main_adjudication=True,independent_human_review=False,
                        corpus_frozen_at=load(ROOT/'stage10b_corpus_manifest.json')['at'],semantic_passes_sealed_at=independent['at'],
                        human_labor_hours=None),
        budget=dict(primary_gpu_target=0,passive_repair_hard_gpu_hours_less_than=1,maximum_repair_trajectories=32),
        note='GPU allocation time includes startup/hash checks/validation and any failed attempts. CPU receipts record latest available snapshots; final CPU reporting job may still be active at snapshot. Agent annotation effort is not a measured human-hour cost.'))
    print('NEW_GPU_HOURS',gpu_seconds/3600,'PASSIVE_REPAIRED',len(repair),flush=True)


if __name__=='__main__':main()
