"""Finite shared queue of complete trajectory bundles; no automatic follow-on."""
import argparse,os,gc,time,traceback,subprocess
from pathlib import Path
import torch
from scripts.stage10c.common import ROOT,load,save,sha,now
from scripts.stage10c.runtime import load_runtime,inputs,base_state,free,teacher,mask_args,CONDITIONS

@torch.inference_mode()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--split',choices=['primary','reserve'],default='primary');args=ap.parse_args()
 m=load(ROOT/'audit'/f'{args.split}_manifest.json');assert m['frozen']
 assert load(ROOT/'stage10c_technical_validation.json')['pass_all'] and m['validation_sha256']==sha(ROOT/'stage10c_technical_validation.json')
 for p,h in m['source_sha256'].items():assert sha(p)==h,p
 if args.split=='reserve':assert load(ROOT/'audit/primary_inference.json')['reserve_gate_pass']
 controls={r['trajectory_id']:r for r in load(ROOT/'stage10c_roi_controls.json')['rows']};split=load(ROOT/'stage10c_frozen_candidate_split.json');by={r['trajectory_id']:r for r in split['rows']}
 sid=os.environ['SLURM_JOB_ID']
 if all((ROOT/args.split/'claims'/tid).exists() for tid in m['ids']):
  save(ROOT/args.split/'workers'/sid/'complete.json',dict(at=now(),ids=[],reason='No unclaimed trajectory bundles; exit before loading model.'));return
 proc,model,env=load_runtime();save(ROOT/args.split/'workers'/sid/'environment.json',env);done=[]
 started=time.monotonic()
 for tid in m['ids']:
  claim=ROOT/args.split/'claims'/tid;claim.parent.mkdir(parents=True,exist_ok=True)
  try:claim.mkdir()
  except FileExistsError:continue
  save(claim/'owner.json',dict(at=now(),slurm_job_id=sid));row=by[tid];begin=time.monotonic()
  old=ROOT/'technical/cases'/tid/'result.json'
  if args.split=='reserve' and old.exists():
   result=load(old);assert result['config_sha256']==sha(ROOT/'config.json')
   save(ROOT/args.split/'cases'/tid/'result.json',dict(result,exact_reuse_path=str(old),exact_reuse_sha256=sha(old),manifest_sha256=sha(ROOT/'audit'/f'{args.split}_manifest.json')))
  else:
   prepared,meta,ids,seed,inputaudit=inputs(proc,row);base,prefix=base_state(model,prepared,ids,seed,row);data=[]
   torch.cuda.reset_peak_memory_stats()
   for condition in CONDITIONS:
    kwargs=mask_args(row,meta,controls[tid],condition)
    g=free(model,proc,base,ids,seed,row,kwargs)[0];nll=teacher(model,base,ids,seed,row,kwargs)
    data.append(dict(condition=condition,free=g,nll=nll))
   save(ROOT/args.split/'cases'/tid/'result.json',dict(at=now(),trajectory_id=tid,rows=data,input=inputaudit,prefix=prefix,
    slurm_job_id=sid,config_sha256=sha(ROOT/'config.json'),manifest_sha256=sha(ROOT/'audit'/f'{args.split}_manifest.json'),
    seconds=time.monotonic()-begin,peak_allocated_bytes=torch.cuda.max_memory_allocated()))
   del prepared,base;gc.collect();torch.cuda.empty_cache()
  done.append(tid);print('COMPLETE',tid,'conditions5',round(time.monotonic()-begin,2),'seconds',flush=True)
 save(ROOT/args.split/'workers'/sid/'complete.json',dict(at=now(),ids=done,seconds=time.monotonic()-started))
 if all((ROOT/args.split/'cases'/tid/'result.json').exists() for tid in m['ids']):
  cancellations=[]
  for job in load('state/gpu_experiment_queue.json')['jobs']:
   if not job['id'].startswith('stage10c_'+args.split+'_') or str(job.get('slurm_job_id'))==sid:continue
   peer=str(job.get('slurm_job_id'));state=subprocess.run(['squeue','-j',peer,'-h','-o','%T'],capture_output=True,text=True)
   if state.returncode==0 and state.stdout.strip()=='PENDING':
    result=subprocess.run(['scancel',peer],capture_output=True,text=True);cancellations.append(dict(slurm_job_id=peer,returncode=result.returncode,reason='All frozen trajectory bundles complete; pending GPU no longer needed.'))
  save(ROOT/args.split/'workers'/sid/'queue_drained.json',dict(at=now(),pending_peers_cancelled=cancellations))
if __name__=='__main__':
 try:main()
 except Exception as e:
  save(ROOT/f'audit/worker_failure_{os.environ.get("SLURM_JOB_ID","local")}.json',dict(at=now(),error=repr(e),traceback=traceback.format_exc()));raise
