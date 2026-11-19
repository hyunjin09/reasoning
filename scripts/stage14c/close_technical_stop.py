"""Close a failed G2 gate without inventing scientific results or launching work."""
import re
import subprocess
from scripts.stage14c.common import *

def seconds(value):
    days=0
    if '-' in value:d,value=value.split('-',1);days=int(d)
    h,m,s=map(int,value.split(':'));return days*86400+h*3600+m*60+s

def main():
    gate=load(ROOT/'audit/preflight_validation.json');assert gate['pass'] is False
    jobs=[]
    for p in sorted((ROOT/'audit/launches').glob('job_*.json')):
        r=load(p);j=r['job'];jid=j['slurm_job_id']
        receipt=ROOT/'audit'/f'job_{jid}_final_scontrol.json'
        call=subprocess.run(['scontrol','show','job',str(jid),'-o'],capture_output=True,text=True)
        text=load(receipt)['text'] if receipt.exists() else call.stdout if call.returncode==0 else None
        if text:
            fields=dict(re.findall(r'(\w+)=([^\s]+)',text));assert fields['JobState'] in ['COMPLETED','FAILED','CANCELLED','TIMEOUT','OUT_OF_MEMORY'],fields['JobState']
            dur=seconds(fields['RunTime']);state=fields['JobState'];exit_code=fields['ExitCode'];node=fields['NodeList']
            basis='Slurm final scontrol allocated runtime'
            if not receipt.exists():save(receipt,dict(at=now(),text=text))
        else:
            exit_record=load(ROOT/'audit/workers'/str(jid)/'exit.json');assert exit_record['queue_exhausted']
            dur=max(exit_record['seconds'],(dt.datetime.fromisoformat(exit_record['at'])-dt.datetime.fromisoformat(r['at'])).total_seconds())+10
            state='WORKER_COMPLETE_SLURM_RECORD_EXPIRED';exit_code=None;node=j['node']
            basis='Conservative submission-to-worker-finish proxy plus10s cleanup allowance; Slurm retention expired, sacct unavailable'
        gpus=int(j['gpus'])
        jobs.append(dict(job_id=str(jid),node=node,state=state,exit_code=exit_code,
            allocated_seconds_or_proxy=dur,gpus=gpus,GPU_hours=dur*gpus/3600,requested_hours=r['hours'],command=j['command'],
            log_path=j['log_path'],scontrol=text,accounting_basis=basis,mode=r['mode']))
    active=subprocess.run(['squeue','-u',os.environ.get('USER','hyunjin'),'-h','-o','%i'],capture_output=True,text=True,check=True).stdout.split()
    assert not {j['job_id'] for j in jobs}&set(active)
    save(ROOT/'audit/resource_accounting.json',dict(at=now(),jobs=jobs,total_GPU_hours=sum(j['GPU_hours'] for j in jobs),
        source_CPU_only_jobs=['139089','139093'],CPU_source_GPU_hours=0,source_annotation=dict(primary=1714,second_original_eligible=556,chart_consistency=25,hash_reread=172,new_evidence_confirmations=26),
        actual_science_preflight_calls=42,short_synthetic_calls=4,main_execution_released=False,D1_calls=0,
        source='Final Slurm scontrol where preserved, explicit conservative worker/submission proxy when records expired; includes startup/repair time.',hard_ceiling_GPU_hours=120,active_stage_GPUs=0))
    hashes={}
    for t in all_tasks('preflight'):
        p=checked_result(t);assert p
        for name in ['input.json','generation.json','result.json']:hashes[str(p.parent/name)]=sha(p.parent/name)
    save(ROOT/'audit/g2_raw_seal.json',dict(at=now(),calls=46,files=hashes,science_accuracy_computed=False))
    save(ROOT/'audit/g2_technical_stop_validation.json',dict(at=now(),status='STOP_G2_TECHNICAL_GATE',
        gate_sha256=sha(ROOT/'audit/preflight_validation.json'),resource_sha256=sha(ROOT/'audit/resource_accounting.json'),
        G1_source_seal_sha256=sha(ROOT/'audit/g1_final_source_seal_v1.json'),all_calls_preserved=True,
        active_stage_jobs=0,main_released=False,D1_launched=False,scientific_contrasts_estimated=False,stage14c_science_complete=False))
    print(json.dumps(dict(GPU_hours=sum(j['GPU_hours'] for j in jobs),active_GPUs=0)))
if __name__=='__main__':main()
