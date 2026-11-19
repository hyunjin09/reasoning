"""Preserve terminal Slurm accounting before short controller retention expires."""
import subprocess
from scripts.stage14c.common import *

def main():
    active=set(subprocess.run(['squeue','-u',os.environ.get('USER','hyunjin'),'-h','-o','%i'],capture_output=True,text=True,check=True).stdout.split())
    saved=[]
    for p in sorted((ROOT/'audit/launches').glob('job_*.json')):
        jid=str(load(p)['job']['slurm_job_id']);dest=ROOT/'audit'/f'job_{jid}_final_scontrol.json'
        if jid in active or dest.exists():continue
        response=subprocess.run(['scontrol','show','job',jid,'-o'],capture_output=True,text=True)
        if response.returncode==0:
            save(dest,dict(at=now(),text=response.stdout));saved.append(jid)
    if saved:print('Preserved terminal Slurm records:',','.join(saved))
if __name__=='__main__':main()
