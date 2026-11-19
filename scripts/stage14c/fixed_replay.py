"""One bounded G2 diagnostic: same seeded request in two identical fresh engines."""
import argparse
import subprocess
import sys
from scripts.stage14c.common import *
from scripts.stage14c.oom_runner import stop_group
from scripts.stage14c import worker

def authorize(m):
    proposal=load(ROOT/'audit/g2_fixed_context_replay_repair_v1.json')
    for p,h in proposal['files'].items():assert sha(p)==h,p
    assert m['mode']=='fixed_replay_repair' and m['model_key']=='T' and len(m['rows'])==1 and m['batch_size']==18
    assert m['config_sha256']==sha(ROOT/'spec/model_and_recipe_identity.json')
    original=next(t for t in all_tasks('preflight') if t['task_id']=='seed_replay_T_0')
    t=m['rows'][0];assert t['task_id'] in proposal['task_ids']
    assert {k:v for k,v in t.items() if k!='task_id'}=={k:v for k,v in original.items() if k!='task_id'}

def main(child,path,expected):
    if child:
        worker.authorize=authorize;worker.run(path,expected);return
    proposal=load(ROOT/'audit/g2_fixed_context_replay_repair_v1.json')
    job=os.environ['SLURM_JOB_ID'];dest=ROOT/'audit/workers'/job;start=dt.datetime.now(dt.timezone.utc)
    for i in range(2):
        task=load(ROOT/'audit/g2_fixed_context_replay_tasks_v1.json')['rows'][i]
        m=dict(mode='fixed_replay_repair',model_key='T',rows=[task],batch_size=18,
               config_sha256=sha(ROOT/'spec/model_and_recipe_identity.json'),engine_id=f'{i:04d}',attempts={task['task_id']:0})
        authorize(m);p=dest/f'replay_{i}_manifest.json';save(p,m);log=dest/f'replay_{i}.log'
        with log.open('x') as f:
            proc=subprocess.Popen([sys.executable,'-m','scripts.stage14c.fixed_replay','--child',str(p),'--manifest-sha256',sha(p)],stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
            try:code=proc.wait(timeout=900)
            finally:stop_group(proc)
        assert code==0,'Fixed-context replay failed; no automatic retry'
        assert checked_result(task)
    save(dest/'exit.json',dict(at=now(),complete=True,queue_exhausted=True,calls=2,
        seconds=(dt.datetime.now(dt.timezone.utc)-start).total_seconds(),diagnostic='fixed-context exact seed replay',science_calls=0))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--child',action='store_true');p.add_argument('manifest',nargs='?');p.add_argument('--manifest-sha256');a=p.parse_args();main(a.child,a.manifest,a.manifest_sha256)
