"""CPU watchdog for the explicit GPU budget, including stalled model startup."""
import argparse,json,os,subprocess,time
from pathlib import Path
def allowance(manifest):
 path=manifest.get('budget_grant_path')
 if path and Path(path).exists():
  grant=json.loads(Path(path).read_text())
  if grant['manifest_id']!=manifest['id']:raise ValueError('Wrong budget grant')
  value=grant['gpu_seconds']
 else:value=manifest['budget_reservation_seconds']
 if not isinstance(value,int) or not 0<value<=86400:raise ValueError('Invalid explicit allowance')
 return value
def exhausted(elapsed,gpus,grant,margin=30):return elapsed*gpus>=grant-margin
def run(path):
 m=json.loads(Path(path).read_text());job=os.environ['SLURM_JOB_ID'];failures=0
 while True:
  try:
   r=subprocess.run(['sacct','-X','-n','-P','-j',job,'--format=JobIDRaw,ElapsedRaw'],capture_output=True,text=True,check=True,timeout=10)
   a=[s.split('|') for s in r.stdout.splitlines() if s.split('|')[0]==job]
   if not a:raise RuntimeError('No allocation accounting')
   elapsed=int(a[0][1]);grant=allowance(m);failures=0
   stop=exhausted(elapsed,m.get('gpus',1),grant)
  except Exception as exc:
   failures+=1;print('BUDGET_GUARD_ACCOUNTING_ERROR',repr(exc),flush=True);stop=failures>=3
  if stop:
   print('BUDGET_GUARD_CANCEL_OWN_ALLOCATION',job,flush=True)
   subprocess.run(['scancel',job],check=True,timeout=10);return
  time.sleep(15)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('manifest');run(p.parse_args().manifest)
