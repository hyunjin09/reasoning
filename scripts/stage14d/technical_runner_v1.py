"""Two fresh engines per checkpoint, inside one <=1h Slurm allocation."""
import argparse
import os
import subprocess
import sys
import time
from scripts.stage14d.prepare_technical_v1 import ROOT,save


def run(model):
    job=os.environ['SLURM_JOB_ID'];started=time.time();deadline=started+3420
    for engine in [0,1]:
        if deadline-time.time()<300:raise TimeoutError('Do not start another engine near deadline')
        code=subprocess.run([sys.executable,'-m','scripts.stage14d.technical_worker_v1',model,str(engine),
                             '--deadline',str(deadline)],timeout=deadline-time.time()).returncode
        if code:
            save(ROOT/'audit/technical_workers_v1'/job/'runner_exit.json',dict(complete=False,exit_code=code,
                 engine=engine,seconds=time.time()-started,scientific_jobs_launched=False))
            raise SystemExit(code)
    save(ROOT/'audit/technical_workers_v1'/job/'runner_exit.json',dict(complete=True,seconds=time.time()-started,
         scientific_jobs_launched=False))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('model',choices=['I','T']);run(p.parse_args().model)
