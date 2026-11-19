"""Record an independent shard or dependent CPU assembly, releasing its allocation."""
import argparse
import json
import os
from datetime import datetime,timezone
from pathlib import Path
from harness_state import mutate_gpu_queue
from visual_reasoning.stage8b.block1_data import ROOT,save,digest

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--part',choices=['0','assemble'],required=True)
    ap.add_argument('--exit-code',type=int,required=True);args=ap.parse_args()
    assembly=args.part=='assemble'
    marker=ROOT/'audit'/'analysis_result_freeze.json' if assembly else ROOT/'workers'/f'rank{args.part}'/'complete.json'
    completed=args.exit_code==0 and marker.exists()
    scheduler_id='stage8b_block1_assemble_node06_v3' if assembly else 'stage8b_block1_rank0_node06_v3'
    result=dict(at=datetime.now(timezone.utc).isoformat(),completed=completed,exit_code=args.exit_code,
        part=args.part,slurm_job_id=os.environ['SLURM_JOB_ID'],scheduler_id=scheduler_id,
        split_execution_sha256=digest(ROOT/'audit'/'execution_freeze_node06_v3.json'),
        gpu_work_complete=completed if not assembly else all((ROOT/'workers'/f'rank{i}'/'complete.json').exists() for i in range(2)),
        scientific_summary_pending=True,release='This allocation exits now; no GPU waits for its peer')
    destination=ROOT/'wrapper.json' if assembly else ROOT/'workers'/f'rank{args.part}'/'slurm_wrapper_v3.json'
    save(destination,result)
    if completed and assembly:
        save(ROOT/'audit'/'node06_result_provenance_v3.json',dict(
            at=result['at'],original_execution_sha256=digest(ROOT/'audit'/'execution_freeze.json'),
            split_execution_sha256=result['split_execution_sha256'],
            analysis_result_freeze_sha256=digest(marker),
            worker_receipts=[json.loads((ROOT/'workers'/f'rank{i}'/('slurm_wrapper_v3.json' if i==0 else 'slurm_wrapper_v2.json')).read_text()) for i in range(2)],
            scientific_definitions_unchanged=True,assembly_gpu_count=0))
    def update(queue):
        job=next(j for j in queue['jobs'] if j['id']==scheduler_id)
        job.update(status='succeeded' if completed else 'failed',finished_at=result['at'],result_path=str(destination))
    mutate_gpu_queue(Path.cwd(),update)
    print(json.dumps(result),flush=True)
    if not completed:raise SystemExit(args.exit_code or 1)
