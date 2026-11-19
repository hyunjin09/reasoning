"""Allocation accounting includes validation, startup, failures and pending cancellations."""
from datetime import datetime
from scripts.stage10c.common import ROOT,load,save,now
from scripts.stage9a5.account import seconds

def main():
 terminal={'COMPLETED','FAILED','CANCELLED','TIMEOUT','OUT_OF_MEMORY'};best={}
 for path in sorted((ROOT/'audit').glob('resource_snapshot_*.json')):
  for r in load(path)['jobs']:
   f=r['slurm_fields'];name=r['queue']['id'];old=best.get(name)
   if not f.get('RunTime'):continue
   if old is None or seconds(f['RunTime'])>seconds(old['slurm_fields']['RunTime']) or (seconds(f['RunTime'])==seconds(old['slurm_fields']['RunTime']) and f.get('JobState') in terminal):best[name]=dict(r,snapshot=str(path))
 expected={j['id'] for j in load('state/gpu_experiment_queue.json')['jobs'] if j['id'].startswith('stage10c_') and j['gpus']}
 jobs=[];timeline=[];gpu_seconds=0
 for name,r in sorted(best.items()):
  q=r['queue'];f=r['slurm_fields'];g=q['gpus'];secs=seconds(f['RunTime'])
  jobs.append(dict(id=name,slurm_job_id=q['slurm_job_id'],gpus=g,runtime_seconds=secs,state=f['JobState'],exit_code=f.get('ExitCode'),node=f.get('NodeList'),command=q['command'],snapshot=r['snapshot']))
  if g:
   assert f['JobState'] in terminal,(name,f['JobState']);gpu_seconds+=g*secs
   if secs:timeline.extend([(datetime.fromisoformat(f['StartTime']),g),(datetime.fromisoformat(f['EndTime']),-g)])
 assert expected=={j['id'] for j in jobs if j['gpus']}
 current=peak=0
 for _,change in sorted(timeline):current+=change;peak=max(peak,current)
 assert current==0 and peak<=8 and gpu_seconds<4*3600
 stage={}
 for name in ['technical','primary','reserve','optional']:
  receipts=list((ROOT/name/'cases').glob('*/result.json'))
  stage[name]=dict(cases=len(receipts),new_free_runs=sum(0 if load(p).get('exact_reuse_path') else len(load(p)['rows']) for p in receipts),
    exact_reused_runs=sum(len(load(p)['rows']) if load(p).get('exact_reuse_path') else 0 for p in receipts))
 save(ROOT/'stage10c_resource_accounting.json',dict(at=now(),jobs=jobs,allocated_gpu_hours=gpu_seconds/3600,all_gpu_jobs_terminal=True,
  peak_gpus=peak,authorized_gpu_ceiling=8,hard_gpu_cap=4,stages=stage,
  max_allocated_vram_bytes=max([load(p).get('peak_allocated_bytes',0) for name in stage for p in (ROOT/name/'cases').glob('*/result.json')],default=0),
  technical_extra_noop_comparison_runs=3,new_benchmark_scale_generations=0,existing_native_traces_unchanged=True,
  limitations='Allocation hours include startup/validation and any failures. Technical cases include three extra unpatched greedy validation runs. Fixed88-token local branches are new continuations; historical sampled suffixes are not counted as greedy reuses. CPU final job may have only a running snapshot.'))
 print('ALLOCATED_GPU_HOURS',gpu_seconds/3600)
if __name__=='__main__':main()
