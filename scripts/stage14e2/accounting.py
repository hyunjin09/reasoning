"""Actual Slurm charges plus exclusive reservations for the new24GPU-hour cycle."""
import subprocess,re
from scripts.stage14e2.common import *
TERMINAL={'COMPLETED','FAILED','CANCELLED','TIMEOUT','OUT_OF_MEMORY','NODE_FAIL','PREEMPTED','BOOT_FAIL','DEADLINE'}
def refresh():
 ledger=load(P/'audit/resource_ledger.json');total=0;reserved=0
 for j in ledger['new_jobs']:
  result=subprocess.run(['sacct','-X','-n','-P','-j',str(j['slurm_job_id']),'--format=JobIDRaw,State,ElapsedRaw,AllocTRES,NodeList,Start,End'],capture_output=True,text=True,check=True)
  lines=[s.split('|') for s in result.stdout.splitlines() if s.split('|')[0]==str(j['slurm_job_id'])]
  if not lines:raise RuntimeError('Missing Slurm accounting')
  a=lines[0];state=a[1].split()[0].rstrip('+');sec=int(a[2]);match=re.search(r'(?:^|,)gres/gpu=(\d+)(?:,|$)',a[3]);gpus=int(match.group(1)) if match else (0 if state=='PENDING' else j['gpus'])
  charged=sec*gpus;j.update(state=state,elapsed_seconds=sec,allocated_gpus=gpus,actual_gpu_seconds=charged,alloc_tres=a[3],node=a[4],start=a[5],end=a[6])
  total+=charged
  if state not in TERMINAL:reserved+=max(0,j['reservation_seconds']-charged)
 ledger.update(at=now(),new_actual_gpu_seconds=total,new_reserved_gpu_seconds=reserved,new_remaining_unreserved_seconds=86400-total-reserved)
 update(P/'audit/resource_ledger.json',ledger)
 return ledger
if __name__=='__main__':print(refresh())
