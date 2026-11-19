"""Finite CPU-only observation of existing main jobs; no launches or scoring."""
import os,time
from scripts.stage14b.common import *
from scripts.stage14b.status import status


def classify(jobs):
    failed=[];started=[]
    for j in jobs:
        if (j.get('exit') or {}).get('complete'):started.append(j['job_id']);continue
        heartbeat=j.get('heartbeat') or {}
        if j['closed'] and j['state']!='COMPLETED':failed.append(j['job_id'])
        elif heartbeat.get('completed',0)>=3:started.append(j['job_id'])
    return failed,started


def main():
    job=os.environ['SLURM_JOB_ID'];dest=ROOT/'audit/main_monitor'/job;start=time.monotonic()
    save(dest/'started.json',dict(at=now(),job=job,gpus=0,hours=72,launch_authority=False,scientific_scoring=False))
    while time.monotonic()-start<72*3600:
        s=status();jobs=[j for j in s['jobs'] if j['mode']=='main'];assert len(jobs)==8
        bad,started=classify(jobs)
        print(now(),'started_with_three_or_more',len(started),'/8','failed',bad,flush=True)
        if bad:
            save(dest/'hold.json',dict(at=now(),failed_jobs=bad,action='No automatic retry, tuning or extra allocation. Agent diagnosis required; unaffected finite workers continue.'))
            return
        if len(started)==8:
            save(dest/'exit.json',dict(at=now(),status='FIRST_SAMPLES_VERIFIED',job_ids=started,
                next='Finite main workers continue. No confirmation launch until scoring and primary/secondary analysis seals.'))
            return
        time.sleep(60)
    save(dest/'exit.json',dict(at=now(),status='MONITOR_TIME_BOUND',main_jobs_preserved=True))

if __name__=='__main__':main()
