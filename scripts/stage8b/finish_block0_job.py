"""Release the preprocessing allocation regardless of later CPU answer review."""
import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from harness_state import mutate_gpu_queue
from prepare_block0 import ROOT, save

if __name__ == '__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--exit-code',type=int,required=True)
    rc=ap.parse_args().exit_code
    complete=rc == 0 and (ROOT/'audit'/'preprocessing_integrity.json').exists()
    result=dict(at=datetime.now(timezone.utc).isoformat(), completed=complete, exit_code=rc,
        slurm_job_id=os.environ['SLURM_JOB_ID'], preprocessing_complete=complete,
        block0_final_freeze_complete=(ROOT/'stage8b_block0_freeze.json').exists(),
        release='Slurm batch exits now; no keepalive or follow-up GPU job')
    save(ROOT/'wrapper.json',result)
    def update(queue):
        job=next(j for j in queue['jobs'] if j['id']=='stage8b_block0_node02_v1')
        job.update(status='succeeded' if complete else 'failed',finished_at=result['at'],result_path=str(ROOT/'wrapper.json'))
    mutate_gpu_queue(Path.cwd(),update)
    print(json.dumps(result),flush=True)
    if not complete:raise SystemExit(rc or 1)
