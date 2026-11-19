"""Read-only hash verification of frozen source and prior-stage bytes."""
import os,time
from concurrent.futures import ThreadPoolExecutor
from scripts.stage14a.common import *
assert os.environ.get('SLURM_JOB_ID'),'Large hash pass requires CPU Slurm.'
start=time.monotonic();checks={}
for name in ['source_file_snapshot','prior_stage12_13_preservation','pre_review_code_seal','pre_review_code_seal_supplement','pre_review_code_seal_supplement_v3']:
 snap=ROOT/f'audit/{name}.json';files=load(snap)['files']
 def check(kv):
  p,v=kv;expected=v['sha256'] if isinstance(v,dict) else v
  try: actual=sha(p);return None if actual==expected else dict(path=p,expected=expected,actual=actual)
  except Exception as e:return dict(path=p,error=str(e))
 with ThreadPoolExecutor(max_workers=2) as pool: mismatches=[x for x in pool.map(check,files.items()) if x]
 checks[name]=dict(count=len(files),snapshot_sha256=sha(snap),mismatches=mismatches,all_match=not mismatches)
 print(name,len(files),'mismatches',len(mismatches),flush=True)
save(ROOT/'audit/final_input_preservation_verification.json',dict(at=now(),job_id=os.environ['SLURM_JOB_ID'],elapsed_seconds=time.monotonic()-start,allocated_cpus=2,gpus=0,gpu_hours=0,checks=checks,all_match=all(c['all_match'] for c in checks.values())))
assert all(c['all_match'] for c in checks.values())
