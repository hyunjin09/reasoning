import os,subprocess,shlex
from pathlib import Path
from types import SimpleNamespace
import gpu_scheduler as scheduler
from scripts.stage14d1.common import *
assert not list((P/'audit').glob('compact_smoke_launch.json'))
prior=subprocess.run(['sacct','-j','146489,146490','--format=JobIDRaw,State,ElapsedRaw,AllocTRES','-P','-n'],capture_output=True,text=True,check=True).stdout
assert '146489|COMPLETED|' in prior and '146490|CANCELLED' in prior
sample=load(P/'protocol/sampler_and_seeds.json');path=P/'audit/shards/technical_compact_v2.json';save(path,dict(at=now(),mode='technical',families=sample['technical_families'],wall_seconds=3600,runtime_sha256=sha(P/'protocol/runtime_v2.json')))
ident='sava14d1_compact8_v2_20261019';command=shlex.join(['bash','scripts/stage14d1/run.sh','-m','scripts.stage14d1.worker_v2',str(path)])
args=SimpleNamespace(max_user_gpus=8,squeue_output=None,all_squeue_output=None,scontrol_output=None,available_gpus=None);status=scheduler.gpu_status(args,scheduler.load_gpu_queue(Path.cwd()));assert status['remaining_user_slots']>=1
saved=Path('reports/index.md').read_text()
try:
 subprocess.run(['.venv/bin/python','infra/gpu_scheduler.py','add','--project','.', '--id',ident,'--exp-id',ident,'--gpu-type','a6000','--node','node03','--gpus','1','--mem','28G','--cpus','1','--command',command,'--log-path',f'runs/stage14d1/{ident}/slurm.log','--result-path',str(P)],check=True,capture_output=True,text=True)
 jobs=[j for j in scheduler.load_gpu_queue(Path.cwd())['jobs'] if j['id']==ident];plan=scheduler.plan_jobs({'jobs':jobs},status);assert len(plan)==1
 os.environ['SBATCH_TIMELIMIT']='01:00:00';scheduler.execute_launch(Path.cwd(),plan[0]);reg=next(j for j in scheduler.load_gpu_queue(Path.cwd())['jobs'] if j['id']==ident)
 save(P/'audit/launches'/f"job_{reg['slurm_job_id']}.json",dict(at=now(),hours=1,mode='technical_v2',job=reg));save(P/'audit/compact_smoke_launch.json',dict(at=now(),job=reg,prior_accounting=prior,initial_observed_GPUh=548/3600,new_reserved_GPUh=1,within_initial_2GPUh=True,stage_limit=16));print('SUBMITTED',reg['slurm_job_id'],reg['node'])
finally:Path('reports/index.md').write_text(saved)
