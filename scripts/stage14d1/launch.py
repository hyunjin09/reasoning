"""Submit only explicitly enumerated SAVA shards through the project scheduler."""
import argparse,os,subprocess,shlex,datetime
from pathlib import Path
from types import SimpleNamespace
import gpu_scheduler as scheduler
from scripts.stage14d1.common import *
def launch(mode,workers,hours):
 assert mode in ['technical','main'] and 1<=workers<=8 and hours>0
 cfg=load(P/'protocol/runtime.json');sampler=load(P/'protocol/sampler_and_seeds.json')
 existing=list((P/'audit/launches').glob('job_*.json')) if (P/'audit/launches').exists() else []
 # Conservative reservation includes full requested allocations, even finished early.
 reserved=sum(load(p)['hours'] for p in existing)
 assert reserved+workers*hours<=cfg['stage_gpu_hour_ceiling']
 if mode=='technical':assert not existing and workers*hours<=cfg['technical_gpu_hour_ceiling']
 else:assert load(P/'audit/technical_gate.json')['pass']
 ids=sampler['technical_families'] if mode=='technical' else [r['family_id'] for r in rows(P/'inference/families.jsonl')]
 active=subprocess.run(['squeue','-u',os.environ.get('USER','hyunjin'),'-h','-o','%i|%j|%T'],capture_output=True,text=True,check=True).stdout
 assert 'sava14d1' not in active,'Existing SAVA job; do not duplicate'
 args=SimpleNamespace(max_user_gpus=8,squeue_output=None,all_squeue_output=None,scontrol_output=None,available_gpus=None)
 status=scheduler.gpu_status(args,scheduler.load_gpu_queue(Path.cwd()));assert not status['warnings'] and status['remaining_user_slots']>=workers
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S');jobids=[];saved_report=Path('reports/index.md').read_text()
 try:
  for k in range(workers):
   mpath=P/'audit/shards'/f'{mode}_{k}_{stamp}.json';save(mpath,dict(at=now(),mode=mode,families=ids[k::workers],wall_seconds=int(hours*3600),runtime_sha256=sha(P/'protocol/runtime.json')))
   ident=f'sava14d1_{mode}_{k}_{stamp}';jobids.append(ident)
   command=shlex.join(['bash','scripts/stage14d1/run.sh','-m','scripts.stage14d1.worker',str(mpath)])
   subprocess.run(['.venv/bin/python','infra/gpu_scheduler.py','add','--project','.', '--id',ident,'--exp-id',ident,'--gpu-type','a6000','--gpus','1','--mem','28G','--cpus','4','--exclude-node','node01','--exclude-node','node04','--exclude-node','node05','--command',command,'--log-path',f'runs/stage14d1/{ident}/slurm.log','--result-path',str(P)],check=True,capture_output=True,text=True)
  jobs=[j for j in scheduler.load_gpu_queue(Path.cwd())['jobs'] if j['id'] in jobids];plan=scheduler.plan_jobs({'jobs':jobs},status);assert len(plan)==workers,('Live capacity changed; no automatic pending submissions',status)
  save(P/'audit/launches'/f'{stamp}_plan.json',dict(at=now(),mode=mode,hours=hours,workers=workers,status=status,jobs=plan))
  os.environ['SBATCH_TIMELIMIT']=f'{int(hours):02d}:{round((hours%1)*60):02d}:00'
  for job in plan:
   assert job['node'] in ['node02','node03','node06','node07'];scheduler.execute_launch(Path.cwd(),job)
   registered=next(j for j in scheduler.load_gpu_queue(Path.cwd())['jobs'] if j['id']==job['id']);save(P/'audit/launches'/f"job_{registered['slurm_job_id']}.json",dict(at=now(),hours=hours,mode=mode,job=registered));print('SUBMITTED',registered['slurm_job_id'],registered['node'],flush=True)
 finally:Path('reports/index.md').write_text(saved_report)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('mode');p.add_argument('--workers',type=int,default=2);p.add_argument('--hours',type=float,default=1);a=p.parse_args();launch(a.mode,a.workers,a.hours)
