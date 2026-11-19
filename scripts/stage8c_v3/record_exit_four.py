"""Record finite allocation exit, preserving errors without precision fallback."""
import argparse
import json
import os
import subprocess
from datetime import datetime,timezone
from pathlib import Path
from harness_state import mutate_run_state,append_run_history
from workflow_hooks import refresh_report_index
from scripts.stage8c.prepare import save
from scripts.stage8c_v3.prepare import ROOT


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--exit-code',type=int,required=True);args=ap.parse_args()
    jid=os.environ['SLURM_JOB_ID'];at=datetime.now(timezone.utc).isoformat()
    receipt=subprocess.run(['scontrol','show','job',jid,'-o'],capture_output=True,text=True)
    (ROOT/'audit'/f'slurm_{jid}_exit.txt').write_text(receipt.stdout+receipt.stderr)
    completed=list((ROOT/'dev_four_v1/examples').glob('*/result.json'))
    status='succeeded' if args.exit_code==0 else 'failed'
    save(ROOT/'audit'/f'exit_{jid}.json',dict(at=at,slurm_job_id=jid,exit_code=args.exit_code,
        completed_trajectories=len(completed),precision='float32',precision_fallback=False,
        allocation_releases_at_batch_exit=True,scientific_plan_complete=False))
    subprocess.run(['.venv/bin/python','infra/gpu_scheduler.py','update','--project','.',
        '--id','stage8c_v3_dev_four_v1','--status',status,'--note',
        f'Slurm{jid} exiting {args.exit_code}; {len(completed)}/512 FP32 trajectories. No precision fallback.'],check=True)
    def update(d):
        d.update(status='completed' if args.exit_code==0 else 'failed',finished_at=at,
            current_step='FP32 development generation complete; scoring/conditional continuation pending' if args.exit_code==0 else 'FP32 execution failed; inspect preserved logs before continuation')
        append_run_history(d,'batch_exit',f'exit={args.exit_code}; complete={len(completed)}/512')
    mutate_run_state(Path('.'),'stage8c_v3_dev_four_v1',update)
    refresh_report_index(Path('.'))


if __name__=='__main__':main()
