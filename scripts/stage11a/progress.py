"""Execution metadata only: safe to inspect while native evidence review is blinded."""
import json,subprocess
from collections import defaultdict
from statistics import mean,median
from scripts.stage11a.common import ROOT,load,now

manifest=load(ROOT/'stage11a_probe_manifest.json');totals=defaultdict(int);done=defaultdict(list)
for r in manifest['rows']:totals[r['model_key']]+=1
for p in (ROOT/'probes/results').glob('*/result.json'):
    r=load(p);key='thinking' if r['arm']=='thinking' else 'instruct'
    done[key].append(dict(seconds=r['seconds'],tokens=r['tokens'],job=r['slurm_job_id']))
live=subprocess.check_output(['squeue','-u','hyunjin','-h','-o','%i %T %M %R'],text=True)
print(json.dumps(dict(at=now(),scientific_outputs_inspected=False,models={k:dict(total=n,completed=len(done[k]),remaining=n-len(done[k]),
    mean_seconds=mean(r['seconds'] for r in done[k]) if done[k] else None,median_seconds=median(r['seconds'] for r in done[k]) if done[k] else None,
    generation_gpu_minutes_remaining=(n-len(done[k]))*mean(r['seconds'] for r in done[k])/60 if done[k] else None) for k,n in totals.items()},
    failures=len(list((ROOT/'probes/results').glob('*/failure.json'))),live_slurm=live),indent=2))
