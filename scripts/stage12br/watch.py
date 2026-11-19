"""Finite observational watcher; no launch/retry authority."""
import argparse
import re
import subprocess
import time
from scripts.stage12br.common import ROOT,load,save,now
from scripts.stage12br.resources import TERMINAL

def main(launch):
    jobs=load(launch)['jobs'];deadline=time.monotonic()+4*3600
    while time.monotonic()<deadline:
        status=[]
        for j in jobs:
            jid=str(j['slurm_job_id']);path=ROOT/'audit/terminal_receipts'/f'{jid}.json'
            if path.exists():r=load(path)
            else:
                res=subprocess.run(['scontrol','show','job',jid,'-o'],capture_output=True,text=True,check=True)
                r=dict(at=now(),raw=res.stdout,fields=dict(re.findall(r'(\w+)=([^\s]+)',res.stdout)))
                if r['fields'].get('JobState') in TERMINAL:
                    save(path,r);ex=ROOT/'workers'/jid/'exit.json'
                    success=r['fields']['JobState']=='COMPLETED' and r['fields'].get('ExitCode')=='0:0' and ex.exists() and load(ex)['complete']
                    subprocess.run(['.venv/bin/python','infra/gpu_scheduler.py','update','--project','.',
                        '--id',j['id'],'--status','succeeded' if success else 'failed','--note','Stage12B-R finite job terminal; no automatic next action'],check=True)
            status.append((jid,r['fields'].get('JobState')))
        print(now(),status,flush=True)
        if all(s in TERMINAL for _,s in status):return
        time.sleep(45)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('launch');a=p.parse_args();main(a.launch)
