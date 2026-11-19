"""Fresh engines for technical repeats and bounded OOM recovery; finite queues."""
import argparse
import os
import subprocess
import sys
import time
from scripts.stage14cv.common import *
from scripts.stage14cv.control import oom_action
from scripts.stage14c.oom_runner import stop_group


def run(path,expected):
    assert sha(path)==expected
    m=load(path);authorize(m);job=os.environ['SLURM_JOB_ID'];dest=ROOT/'audit/workers'/job;start=time.monotonic()
    partitions=[[t for t in m['rows'] if t['engine_repeat']==r] for r in [0,1]] if m['panel']=='technical' else [m['rows']]
    engine_index=0;recovery_used=False
    save(dest/'started.json',dict(at=now(),manifest=str(path),manifest_sha256=expected,panel=m['panel'],model=m['model_key']))
    try:
        for partition in partitions:
            while True:
                pending=[];attempts={}
                for t in partition:
                    if checked(t) or missing_path(t).exists():continue
                    previous=list((ROOT/'raw'/t['collection']/t['task_id']).glob('attempt_*'))
                    if len(previous)>1:
                        mark_missing(t,'INFRASTRUCTURE_RETRY_EXHAUSTED',dict(job=job));continue
                    attempts[t['task_id']]=int(bool(previous));pending.append(t)
                if not pending:break
                if m['panel']=='technical':
                    count=sum(1 for _ in (ROOT/'raw/technical_preflight').glob('*/attempt_*/input.json'))
                    assert count+len(pending)<=24,'Technical24-call hard ceiling'
                eid=f'{engine_index:04d}';engine_index+=1
                em=dict(m,rows=pending,engine_id=eid,attempts=attempts,singleton=m['panel']=='technical' or recovery_used)
                ep=dest/f'engine_{eid}.json';save(ep,em);engine_dir=dest/'engines'/eid;engine_dir.mkdir(parents=True,exist_ok=True)
                log=engine_dir/'engine.log'
                with log.open('x') as stream:
                    child=subprocess.Popen([sys.executable,'-m','scripts.stage14cv.worker',str(ep),'--manifest-sha256',sha(ep)],
                        stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
                    try:code=child.wait()
                    finally:stop_group(child)
                if code==0:
                    e=load(engine_dir/'exit.json')
                    if e.get('checkpoint'):
                        save(dest/'exit.json',dict(at=now(),complete=False,checkpoint=True,seconds=time.monotonic()-start));return
                    assert e['complete'];continue
                failure=load(engine_dir/'failure.json') if (engine_dir/'failure.json').exists() else dict(error=log.read_text(errors='replace'))
                if m['panel']=='technical':raise RuntimeError('Technical preflight failed; bounded diagnostic required')
                done={t['task_id'] for t in partition if checked(t)}
                action,culprit=oom_action(failure,done,recovery_used)
                if culprit:mark_missing(next(t for t in partition if t['task_id']==culprit),'OOM_SKIP',dict(job=job,engine=eid,failure=failure))
                recovery_used=True
                save(dest/f'recovery_{eid}.json',dict(at=now(),action=action,culprit=culprit,failure=failure,
                    context_change='Fresh engine and singleton active request; max_num_seqs remains18; no scientific recipe/input changes.'))
        save(dest/'exit.json',dict(at=now(),complete=True,queue_exhausted=True,
            completed=sum(checked(t) is not None for t in m['rows']),technical_missing=sum(missing_path(t).exists() for t in m['rows']),
            seconds=time.monotonic()-start))
    except BaseException as exc:
        save(dest/'failure.json',dict(at=now(),error=repr(exc),seconds=time.monotonic()-start,action='STOP_REVIEW'));raise


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('manifest');p.add_argument('--manifest-sha256',required=True)
    a=p.parse_args();run(a.manifest,a.manifest_sha256)
