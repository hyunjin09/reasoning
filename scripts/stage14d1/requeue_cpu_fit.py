"""Pending-only resource repair: same frozen shards, one CPU per single GPU."""
import os,subprocess,shlex
from pathlib import Path
from types import SimpleNamespace
import gpu_scheduler as scheduler
from scripts.stage14d1.common import *
old=['146487','146488'];status_raw=subprocess.run(['sacct','-j',','.join(old),'--format=JobIDRaw,State,ElapsedRaw,AllocTRES','-P','-n'],capture_output=True,text=True,check=True).stdout
for job in old:
 line=next(x for x in status_raw.splitlines() if x.startswith(job+'|'));assert 'CANCELLED' in line and line.split('|')[2]=='0' and line.split('|')[3]=='',line
save(P/'audit/pending_cpu_repair_v1.json',dict(at=now(),cancelled_pending=old,accounting=status_raw,reason='node03 has two free GPUs but only2CPUs; frozen old4CPU requests cannot fit. Resubmit identical shards at1CPU each, OMP/BLAS already1. No GPU use/scientific changes.',old_requested_GPUh=2,old_allocated_GPUh=0,new_requested_GPUh=2))
args=SimpleNamespace(max_user_gpus=8,squeue_output=None,all_squeue_output=None,scontrol_output=None,available_gpus=None);status=scheduler.gpu_status(args,scheduler.load_gpu_queue(Path.cwd()));assert status['remaining_user_slots']>=2
saved=Path('reports/index.md').read_text();ids=[]
try:
 for k,p in enumerate(sorted((P/'audit/shards').glob('technical_*.json'))):
  ident=f'sava14d1_cpu1_{k}_20261019';ids.append(ident)
  command=shlex.join(['bash','scripts/stage14d1/run.sh','-m','scripts.stage14d1.worker',str(p)])
  subprocess.run(['.venv/bin/python','infra/gpu_scheduler.py','add','--project','.', '--id',ident,'--exp-id',ident,'--gpu-type','a6000','--node','node03','--gpus','1','--mem','28G','--cpus','1','--command',command,'--log-path',f'runs/stage14d1/{ident}/slurm.log','--result-path',str(P)],check=True,capture_output=True,text=True)
 jobs=[j for j in scheduler.load_gpu_queue(Path.cwd())['jobs'] if j['id'] in ids];plan=scheduler.plan_jobs({'jobs':jobs},status);assert len(plan)==2
 os.environ['SBATCH_TIMELIMIT']='01:00:00'
 for job in plan:
  scheduler.execute_launch(Path.cwd(),job);new=next(j for j in scheduler.load_gpu_queue(Path.cwd())['jobs'] if j['id']==job['id']);save(P/'audit/launches'/f"job_{new['slurm_job_id']}.json",dict(at=now(),hours=1,mode='technical',pending_only_replacement=True,job=new));print('SUBMITTED',new['slurm_job_id'],flush=True)
finally:Path('reports/index.md').write_text(saved)
