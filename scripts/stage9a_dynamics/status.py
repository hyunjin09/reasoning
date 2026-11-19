"""Read-only execution accounting; no interim scientific outcome selection."""
import json
import argparse
import subprocess
from collections import Counter
from pathlib import Path
from scripts.stage9a.run_native import now

ROOT=Path('outputs/stage9a_dynamics/v1')


def read_complete(path):
    try:return json.loads(path.read_text())
    except (FileNotFoundError,json.JSONDecodeError):return None


def status():
    manifest=json.loads((ROOT/'audit/interventions.json').read_text())
    rows=[x for p in (ROOT/'rollouts/results').glob('*/result.json') if (x:=read_complete(p)) is not None]
    tasks=[x for p in (ROOT/'rollouts/tasks').glob('*/complete.json') if (x:=read_complete(p)) is not None]
    failures=[str(p) for p in (ROOT/'rollouts/workers').glob('*/failure.json')]
    cfg=json.loads((ROOT/'config.json').read_text());readout_root=Path(cfg.get('readout_root',str(ROOT)))
    failures += [str(p) for p in (readout_root/'readouts/workers').glob('*/failure.json')]
    resource=ROOT/'stage9a_amended_resource_estimate.json'
    if not resource.exists():resource=ROOT/'audit/resource_estimate.json'
    original=json.loads(resource.read_text())
    total_tasks=len(json.loads((ROOT/'audit/tasks.json').read_text())['rows'])
    counts=manifest.get('execution_counts',manifest.get('main_counts'))
    reused={r['result_key'] for r in cfg.get('reused_results',[])}
    out=dict(at=now(),unique_rollouts_complete=len(rows),unique_rollouts_total=counts['run'],reused_rollouts=len(reused),new_rollouts_complete=sum(r['result_key'] not in reused for r in rows),
        rollouts_by_arm=dict(Counter(r['arm'] for r in rows)),native_tasks_complete=len(tasks),native_tasks_total=total_tasks,
        local_readout_events_complete=len(list((readout_root/'readouts/events').glob('*/result.json'))),local_readout_events_total=50,
        measured_completed_suffix_gpu_hours=sum(r['runtime_seconds'] for r in rows)/3600,
        measured_completed_shared_prefix_gpu_hours=sum(r['shared_prefix_seconds'] for r in tasks)/3600,
        completed_peak_gpu_GiB=max((r['peak_gpu_allocated_bytes']/2**30 for r in rows),default=0),
        failures=failures,initial_resource_estimate=original,
        scientific_stage_complete=False,remaining_after_gpu='Masked extraction review, locked adapter scoring, family-clustered inference, deferred bounded redistribution controls, figures and required artifacts, one recommendation; then STOP. No automatic reserve or Stage9B.')
    out['live_slurm']=subprocess.run(['squeue','--me','-h','-o','%i %T %M %N %b'],text=True,capture_output=True,check=True).stdout.splitlines()
    out['coordinator']=read_complete(ROOT/'audit/dispatcher_status.json')
    return out


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root',default=str(ROOT));args=ap.parse_args();ROOT=Path(args.root)
    print(json.dumps(status(),indent=2))
