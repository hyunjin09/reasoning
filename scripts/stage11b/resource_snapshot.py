import sys,re,subprocess
from scripts.stage11b.common import ROOT,load,save,now

rows=[]
for j in load('state/gpu_experiment_queue.json')['jobs']:
    if not j['id'].startswith('stage11b_'):continue
    r=subprocess.run(['scontrol','show','job',str(j.get('slurm_job_id')),'-o'],capture_output=True,text=True)
    fields=dict(re.findall(r'(\w+)=([^\s]+)',r.stdout)) if not r.returncode else {}
    rows.append(dict(queue=j,slurm_fields=fields,slurm_raw=r.stdout,slurm_error=r.stderr))
save(ROOT/'audit'/f'resource_snapshot_{sys.argv[1]}.json',dict(at=now(),jobs=rows,
    live_slurm=subprocess.check_output(['squeue','-u','hyunjin','-h','-o','%i %T %R'],text=True)))
print('SNAPSHOT',sys.argv[1],len(rows))
