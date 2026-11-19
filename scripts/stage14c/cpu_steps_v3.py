"""Finite CPU-only stage steps; semantic grading is never automated here."""
import argparse
import time
import traceback
from scripts.stage14c.common import *


def main(action):
    job=os.environ['SLURM_JOB_ID'];start=time.monotonic()
    root=ROOT/'audit/workers'/job
    save(root/'cpu_started.json',dict(at=now(),job=job,action=action,gpus=0))
    try:
        if action=='I_arm':
            from scripts.stage14c.scoring_v5 import raw_freeze_instruct,extract_arm
            raw_freeze_instruct();extract_arm('I')
        elif action=='raw_global':
            from scripts.stage14c.scoring_v5 import raw_freeze
            raw_freeze()
        elif action=='raw_I':
            from scripts.stage14c.scoring_v4 import raw_freeze,extract_arm
            raw_freeze();extract_arm('I')
        elif action=='primary':
            from scripts.stage14c.analyze import main as analyze
            from scripts.stage14c.primary_report import main as report
            analyze();report()
        elif action=='secondary':
            from scripts.stage14c.secondary import main as analyze
            from scripts.stage14c.figures import main as figures
            analyze();figures()
        elif action=='technical':
            from scripts.stage14c.technical_summary import main as technical
            technical()
        else:raise ValueError(action)
        save(root/'exit.json',dict(at=now(),job=job,action=action,complete=True,gpus=0,seconds=time.monotonic()-start))
        print('CPU STEP COMPLETE',action,flush=True)
    except BaseException as exc:
        save(root/'failure.json',dict(at=now(),job=job,action=action,error=repr(exc),traceback=traceback.format_exc(),gpus=0,seconds=time.monotonic()-start))
        raise


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['I_arm','raw_global','raw_I','primary','secondary','technical']);main(p.parse_args().action)
