"""Technical progress/accounting only; never inspect correctness or launch work."""
from collections import Counter
from pathlib import Path
import json
from scripts.stage12ys.execution import ROOT,load,now
from scripts.stage12ys.resources import account

def main():
    ledger=account('progress');rows=[]
    for p in (ROOT/'generations').glob('*/generation.json'):
        r=load(p);rows.append({k:r[k] for k in ['job','arm','phase','tokens','cap_hit']})
    totals={}
    for phase in 'ABC':
        p=ROOT/'audit'/f'phase{phase}_execution.json'
        if p.exists():totals[phase]=len(load(p)['tasks'])
    out=dict(at=now(),saved=len(rows),by_phase=dict(Counter(r['phase'] for r in rows)),expected=totals,
        by_arm=dict(Counter(r['arm'] for r in rows)),by_job=dict(Counter(r['job'] for r in rows)),
        allocation_gpu_hours=ledger['allocated_gpu_hours_upper'],active_jobs=ledger['active_jobs'],
        worker_failures=[str(p) for p in (ROOT/'workers').glob('*/failure.json')],
        review_counts={x:len(list((ROOT/'audit'/x).glob('*.json'))) for x in ['technical_decisions','first_scores','second_scores']})
    p=Path('reports/stage12ys/v1');p.mkdir(parents=True,exist_ok=True)
    (p/'status.md').write_text('# Stage12Y-S technical progress\n\n```json\n'+json.dumps(out,indent=2)+'\n```\n\nNo correctness-based selection or automated next-stage launch.\n')
    print(json.dumps(out,indent=2))

if __name__=='__main__':main()
