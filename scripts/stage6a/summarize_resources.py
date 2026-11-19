"""Summarize measured native compute, counting physical replays/reuses once."""
import argparse
import json
import statistics
from collections import Counter
from datetime import datetime,timezone
from scripts.stage6a.inventory import OUT,ROOT


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--final',action='store_true');args=parser.parse_args()
    if args.final:assert (OUT/'cohort/primary_release_manifest.json').exists(),'Complete primary acquisition/export first'
    records=[];environments=[];runs=[]
    for folder in sorted((OUT/'native').iterdir()):
        if not folder.is_dir():continue
        results=[json.loads(p.read_text()) for p in sorted(folder.glob('shard_*/examples/*/result.json'))]
        runtimes=[];replay_count=0
        for row in results:
            runtimes.append(row['runtime'])
            if row.get('native_replay'):
                replay_count+=1;runtimes.append(row['native_replay']['runtime'])
        env=[]
        for path in sorted(folder.glob('shard_*/environment.json')):
            value=json.loads(path.read_text());env.append(dict(artifact=str(path.relative_to(ROOT)),
                parameter_dtype=value['parameter_dtype'],observed_node=value['observed_node'],local_rank=value['local_rank']))
        environments+=env;records+=results
        run=dict(run=folder.name,terminal_records=len(results),complete_native=sum(r['complete'] for r in results),
            capped_incomplete=sum(r['truncated'] for r in results),physical_repeat_generations=replay_count,
            total_generated_tokens=sum(r['token_count'] for r in results),
            median_generated_tokens=statistics.median([r['token_count'] for r in results]) if results else None,
            measured_generation_device_seconds_including_replays=sum(r['elapsed_seconds'] for r in runtimes),
            max_gpu_allocated_bytes=max((r['peak_gpu_allocated_bytes'] for r in runtimes),default=0),
            max_gpu_reserved_bytes=max((r['peak_gpu_reserved_bytes'] for r in runtimes),default=0),
            max_process_cpu_rss_kb=max((r['peak_cpu_rss_kb'] for r in runtimes),default=0),
            environment_artifacts=env)
        runs.append(run)
    assert all(r['parameter_dtype']=='torch.bfloat16' and r['observed_node']=='node03' for r in environments)
    queue=json.loads((ROOT/'state/gpu_experiment_queue.json').read_text())
    jobs=[{key:r.get(key) for key in ['id','status','slurm_job_id','gpu_type','gpus','node','mem','cpus','tmux_session','command','log_path','result_path','notes']}
        for r in queue['jobs'] if r['id'].startswith('stage6a_')]
    assert all(str(r['slurm_job_id'])=='109385' for r in jobs)
    device_seconds=sum(r['measured_generation_device_seconds_including_replays'] for r in runs)
    report=dict(status='COMPLETE_MEASURED_NATIVE_RESOURCE_SUMMARY' if args.final else 'RESOURCE_SNAPSHOT',
        created_at=datetime.now(timezone.utc).isoformat(),slurm_allocation='109385',node='node03',tmux_session='9',
        physical_gpus=4,gpu_model='NVIDIA RTX A6000',parameter_dtype='torch.bfloat16',
        project_environment='.venv',environment_state='workspace/env_state.md',new_allocations_requested_by_agent=0,
        user_allocation_request='240G host memory /48CPUs; created by user before Stage6A',
        experiment_bookkeeping_request='120G host memory /32CPUs for GPU jobs; CPU annotation records separate',
        measured_native_device_hours=device_seconds/3600,
        ideal_four_gpu_generation_time_hours=device_seconds/(4*3600),
        ideal_time_caveat='Arithmetic device-time/4 only; not observed elapsed wall time or a utilization estimate. Long native traces, serial reviews, model loading and per-rank dependencies affect elapsed time.',
        native_terminal_records=len(records),native_completeness=dict(Counter('EOS_COMPLETE' if r['complete'] else 'INCOMPLETE' for r in records)),
        total_tokens_excluding_replay_repetitions=sum(r['token_count'] for r in records),
        physical_repeat_generations=sum(r['physical_repeat_generations'] for r in runs),
        reused_mechanics_v1_records_not_recounted=59,
        resource_scope='All physical Stage6A native acquisition, including invalid mechanics-v1 and cap-incomplete traces. Copied/referenced mechanics-v2 reuses add no compute. CPU inventory/annotation time and model load are not in generation timers.',
        peaks_are_per_process='RSS is a per-process high-water mark; neither sum of peaks nor one process peak establishes simultaneous allocation-wide host use.',
        runs=runs,scheduler_jobs=jobs)
    (OUT/'audit/resource_summary.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['status','native_terminal_records','native_completeness','measured_native_device_hours','physical_repeat_generations']},indent=2))


if __name__=='__main__':main()
