"""Capture scheduler receipts while Slurm still retains completed jobs."""
import argparse,re,subprocess
from scripts.stage9a4.common import ROOT,load,save,now


def snapshot(label):
    jobs=[];live=subprocess.check_output(['squeue','-u','hyunjin','-h','-o','%A %T %N'],text=True)
    for j in load('state/gpu_experiment_queue.json')['jobs']:
        if not j['id'].startswith('stage9a4_'):continue
        sid=j.get('slurm_job_id');r=subprocess.run(['scontrol','show','job',str(sid),'-o'],capture_output=True,text=True) if sid else None
        text=r.stdout if r and r.returncode==0 else None;fields=dict(re.findall(r'(\w+)=([^\s]+)',text)) if text else {}
        jobs.append(dict(queue=j,slurm_fields=fields,slurm_raw=text,slurm_error=r.stderr if r and r.returncode else None))
    path=ROOT/f'audit/resource_snapshot_{label}.json';save(path,dict(at=now(),live_slurm=live,jobs=jobs))
    print(str(path),len(jobs),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('label');snapshot(p.parse_args().label)
