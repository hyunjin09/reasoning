"""Bounded receipt collector: no inference, scoring, retries or launches."""
import re
import subprocess
import time
from scripts.stage12vs.common import ROOT,PREFIX,load,save,now
from scripts.stage12c.resources import TERMINAL


def poll():
    statuses=[]
    for j in load('state/gpu_experiment_queue.json')['jobs']:
        if not j['id'].startswith(PREFIX) or not j.get('slurm_job_id'):continue
        jid=str(j['slurm_job_id']);p=ROOT/'audit/terminal_receipts'/f'{jid}.json'
        if p.exists():r=load(p)
        else:
            q=subprocess.run(['scontrol','show','job',jid,'-o'],capture_output=True,text=True,check=True)
            r=dict(at=now(),raw=q.stdout,fields=dict(re.findall(r'(\w+)=([^\s]+)',q.stdout)))
            if r['fields']['JobState'] in TERMINAL:
                save(p,r);end=ROOT/'workers'/jid/'exit.json'
                success=r['fields']['JobState']=='COMPLETED' and r['fields'].get('ExitCode')=='0:0' and end.exists() and load(end)['complete']
                subprocess.run(['.venv/bin/python','infra/gpu_scheduler.py','update','--project','.',
                    '--id',j['id'],'--status','succeeded' if success else 'failed','--note','Stage12VS finite worker terminal; no automatic science'],check=True)
        statuses.append((jid,r['fields']['JobState']))
    print(now(),statuses,'outputs',len(list((ROOT/'generations').glob('*/result.json'))),flush=True)


def main():
    deadline=time.monotonic()+96*3600
    while time.monotonic()<deadline:
        poll()
        p=ROOT/'stage12vs_decision.json'
        if p.exists() and load(p).get('stop'):
            save(ROOT/'audit/observer_exit.json',dict(at=now(),complete=True,reason='Stage decision STOP; no follow-on.'));return
        time.sleep(30)
    save(ROOT/'audit/observer_deadline.json',dict(at=now(),reason='96hour finite observer timeout; no scientific cancellation.'))


if __name__=='__main__':main()
