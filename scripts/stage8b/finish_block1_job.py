import argparse
import os
from datetime import datetime,timezone
from pathlib import Path
from harness_state import mutate_gpu_queue
from visual_reasoning.stage8b.block1_data import ROOT,save

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--exit-code',type=int,required=True);rc=ap.parse_args().exit_code
    complete=rc==0 and (ROOT/'audit'/'analysis_result_freeze.json').exists()
    result=dict(at=datetime.now(timezone.utc).isoformat(),completed=complete,exit_code=rc,
        slurm_job_id=os.environ['SLURM_JOB_ID'],gpu_work_complete=complete,scientific_summary_pending=True,
        release='Batch exits immediately; no keepalive or follow-up job')
    save(ROOT/'wrapper.json',result)
    def update(queue):
        job=next(j for j in queue['jobs'] if j['id']=='stage8b_block1_node06_v1')
        job.update(status='succeeded' if complete else 'failed',finished_at=result['at'],result_path=str(ROOT/'wrapper.json'))
    mutate_gpu_queue(Path.cwd(),update)
    print(result,flush=True)
    if not complete:raise SystemExit(rc or 1)
