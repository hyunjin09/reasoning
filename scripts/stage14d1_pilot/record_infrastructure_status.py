"""Record external capacity block without claiming scientific completion."""
import csv
import subprocess
from pathlib import Path
from scripts.stage14d1_pilot.common import *

def command(*args):return subprocess.check_output(args,text=True)

def main():
    launch=[];spent=PRIOR_GPU_SECONDS;reservation=0
    for p in sorted((P/'audit/launches').glob('*.json')):
        r=load(p);job=r['job']['slurm_job_id']
        accounting=command('sacct','-j',job,'-X','-n','-P','--format=JobID,State,ElapsedRaw,AllocTRES').strip().split('|')
        state=accounting[1];charged=int(accounting[2]) if 'gres/gpu=1' in accounting[3] else 0
        spent+=charged
        pending=state=='PENDING'
        if state not in ('COMPLETED','FAILED','TIMEOUT','OUT_OF_MEMORY') and not state.startswith('CANCELLED'):
            reservation+=r['maximum_gpu_seconds']-charged
        launch.append(dict(job=job,state=state,actual_gpu_seconds=charged,pending=pending,
                           allocation_maximum_gpu_seconds=r['maximum_gpu_seconds'],launch_receipt=str(p)))
    assert spent+reservation<=CEILING_GPU_SECONDS
    nodes={node:command('scontrol','show','node',node,'-o') for node in ['node02','node03','node06','node07']}
    jobs={job:command('scontrol','show','job',job,'-o') for job in ['147582','147583']}
    assert all('JobState=PENDING' in text for text in jobs.values()),'Capacity changed; continue execution instead of recording block'
    seals=[]
    for source in [OLD/'audit/final_package_seal.json',RECOVERY/'audit/recovery_closure_seal.json']:
        seal=load(source);count=0
        for group in ['package_files','code_files']:
            for path,digest in seal[group].items():assert sha(path)==digest,path;count+=1
        seals.append(dict(seal=str(source),verified_files=count))
    for source in [P/'audit/execution_seal_v4.json',P/'audit/execution_seal_v5.json',P/'audit/execution_seal_v6.json',P/'audit/main_execution_seal.json']:
        seal=load(source)
        for path,digest in seal['files'].items():assert sha(path)==digest,path
        seals.append(dict(seal=str(source),verified_files=len(seal['files'])))
    save(P/'audit/resource_and_infrastructure_status.json',dict(at=now(),status='INFRASTRUCTURE_BLOCKED_PENDING_SLURM',
        pilot_complete=False,scientific_solver_completions=0,logical_slots_remaining=432,families_remaining=72,
        actual_gpu_seconds=spent,actual_gpu_hours=spent/3600,remaining_actual_budget_hours=(CEILING_GPU_SECONDS-spent)/3600,
        outstanding_maximum_gpu_seconds=reservation,maximum_cumulative_reserved_hours=(spent+reservation)/3600,
        available_repair_reservation_hours=(CEILING_GPU_SECONDS-spent-reservation)/3600,
        jobs=launch,node_snapshots=nodes,pending_job_snapshots=jobs,preservation_checks=seals,
        technical_usage_before_current_namespace_seconds=PRIOR_GPU_SECONDS,
        blocker='AllotherauthorizedA6000GPUsallocated;node06remainingGPUhasinsufficienthostRAM. PeaktechnicalRSSabout12.3GiB versus5GBunallocated;28Grequestpreserved.',
        work_remaining='Both36familymainshards;source-onlyremaining64queries/addresses;selected24readoutcasesandflags;full432slotresponse/scoring/pairs/casebook/H1-H4report. No scientificfinals fabricated.'))
    out=P/'analysis/planned_coverage_pending.csv';out.parent.mkdir(exist_ok=True)
    with out.open('x',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['family_id','item_id','arm','job','status','correct','generation_path']);w.writeheader()
        byfamily={r['family_id']:r for r in rows(P/'inference/families.jsonl')}
        for rank,job in [(0,'147582'),(1,'147583')]:
            m=load(P/'manifests'/f'main_v6_rank{rank}.json')
            for family in m['families']:
                for arm in ['N','G','Q','QI','QIA','QGL']:
                    w.writerow(dict(family_id=family,item_id=byfamily[family]['item_id'],arm=arm,job=job,status='PENDING_SLURM',correct='',generation_path=''))
    print('Recorded externalblock; preserved allseals; actualGPUh',spent/3600,'reservedceiling', (spent+reservation)/3600)
if __name__=='__main__':main()
