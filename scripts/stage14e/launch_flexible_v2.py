"""CPU-only launcher repair: wait for accounting propagation; worker protocol unchanged."""
import argparse,os,shlex,subprocess,sys
from pathlib import Path
from types import SimpleNamespace
from scripts.stage14e.common import *
from scripts.stage14e.accounting_retry import refresh
from scripts.stage14e.contracts import budget_admissible
sys.path.insert(0,str(Path('infra').resolve()))
import gpu_scheduler as scheduler

def launch(path,module='diagnostic_worker'):
 m=load(path);assert m['wall_seconds'] in [86400,172800];gpus=m['gpus'];gpu_type=m['gpu_type']
 ledger=refresh();assert budget_admissible(ledger['new_actual_gpu_seconds'],ledger['new_reserved_gpu_seconds']+m['budget_reservation_seconds'])
 ident='stage14e_'+m['id'];receipt=P/'audit/launches'/f'{ident}.json';assert not receipt.exists()
 opts=SimpleNamespace(max_user_gpus=8,squeue_output=None,all_squeue_output=None,scontrol_output=None,available_gpus=None)
 status=scheduler.gpu_status(opts,scheduler.load_gpu_queue(Path.cwd()));assert status['remaining_user_slots']>=gpus
 command=shlex.join(['env','VLLM_ENABLE_V1_MULTIPROCESSING=0','bash','scripts/stage14e/run.sh','-m','scripts.stage14e.'+module,path])
 index=Path('reports/index.md').read_text()
 try:
  subprocess.run(['.venv/bin/python','infra/gpu_scheduler.py','add','--project','.', '--id',ident,'--exp-id',ident,'--gpu-type',gpu_type,'--gpus',str(gpus),'--mem','16G','--cpus',str(gpus),'--allow-slurm-pending',
   '--command',command,'--log-path',f'runs/stage14e/{ident}/slurm.log','--result-path',str(P/'raw'/m['id'])],check=True,capture_output=True,text=True)
  selected=[j for j in scheduler.load_gpu_queue(Path.cwd())['jobs'] if j['id']==ident]
  plans=scheduler.plan_jobs({'jobs':selected},status);assert len(plans)==1
  os.environ['SBATCH_TIMELIMIT']='2-00:00:00' if m['wall_seconds']==172800 else '1-00:00:00';scheduler.execute_launch(Path.cwd(),plans[0])
  j=next(j for j in scheduler.load_gpu_queue(Path.cwd())['jobs'] if j['id']==ident)
  save(receipt,{'at':now(),'job':j,'manifest_sha256':sha(path),'capacity':status,'slurm_limit_seconds':m['wall_seconds'],'user_new_cycle_gpu_hour_ceiling':24})
  ledger['new_jobs'].append({'id':ident,'slurm_job_id':j['slurm_job_id'],'gpus':gpus,'reservation_seconds':m['budget_reservation_seconds'],'manifest':path,'launch_receipt':str(receipt)})
  update(P/'audit/resource_ledger.json',ledger);print('SUBMITTED',j['slurm_job_id'],ident)
 finally:Path('reports/index.md').write_text(index)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('manifest');p.add_argument('--module',default='diagnostic_worker');a=p.parse_args();launch(a.manifest,a.module)
