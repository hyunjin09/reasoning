"""Final Slurm allocation charges, including failed attempts; no new jobs."""
import re
import subprocess
from scripts.stage14d1_pilot.common import P,load,save,sha,now

JOBS=['146487','146488','146489','146490','146494','146499','146598','146599',
      '147536','147542','147559','147582','147583','149675','149676','149690','149691']


def main():
    raw=subprocess.check_output(['sacct','-j',','.join(JOBS),'--noheader','-P',
        '--format=JobIDRaw,State,ElapsedRaw,AllocTRES,NodeList,Start,End'],text=True)
    records=[]
    for line in raw.splitlines():
        job,state,elapsed,tres,node,start,end=line.split('|')
        if job not in JOBS:continue
        assert state in ('COMPLETED','FAILED','OUT_OF_MEMORY','TIMEOUT') or state.startswith('CANCELLED'), line
        match=re.search(r'(?:^|,)gres/gpu=(\d+)(?:,|$)',tres)
        gpus=int(match[1]) if match else 0
        records.append(dict(job_id=job,state=state,elapsed_seconds=int(elapsed),allocated_gpus=gpus,
            gpu_seconds=int(elapsed)*gpus,node=node,start=start,end=end,allocation=tres))
    assert {r['job_id'] for r in records}==set(JOBS)
    total=sum(r['gpu_seconds'] for r in records)
    prior=sum(r['gpu_seconds'] for r in records if r['job_id'] not in ['149690','149691'])
    assert prior==45658
    save(P/'audit/resource_accounting_final_v8.json',dict(at=now(),jobs=records,raw_sacct=raw,
        total_gpu_seconds=total,total_gpu_hours=total/3600,prior_gpu_seconds=prior,
        resumption_gpu_hours=(total-prior)/3600,former_gpu_ceiling_hours=16,
        amendment='Latest user requested completion after resource HOLD and one/two-day job limits; fixed pilot only.',
        job_limit_hours=48,charged_basis='Slurm top-level allocation elapsed seconds times GPU count; failed attempts included; batch steps not double counted; CPU-only job has zero GPU charge.',
        all_allocations_terminal=True))
    print('Total charged GPU-hours:',round(total/3600,6))

if __name__=='__main__':main()
