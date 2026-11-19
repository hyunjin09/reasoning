"""Read technical completion receipts and capture allocation state; no outcomes."""
from collections import Counter
from pathlib import Path
import json
from scripts.stage13b.execution import ROOT,load,save,now
from scripts.stage13b.resources import account


def status():
    manifest=load(ROOT/'stage13b_seed_manifest.json');all_tasks=manifest['technical']+manifest['new_scientific']
    result={}
    for phase in ['technical','equal','image']:
        selected=[t for t in all_tasks if t['phase']==phase];cells={}
        for key in sorted({t['model_key']+'_'+t['arm'].split('_',1)[1] for t in selected}):
            rr=[t for t in selected if t['model_key']+'_'+t['arm'].split('_',1)[1]==key]
            completed=[t for t in rr if (ROOT/'generations'/t['task_id']/'result.json').exists()]
            cells[key]=dict(done=len(completed),planned=len(rr))
        result[phase]=cells
    ledger=account('progress')
    out=dict(at=now(),progress=result,allocated_gpu_hours_upper=ledger['allocated_gpu_hours_upper'],
             committed_gpu_hours_upper=ledger['committed_gpu_hours_upper'],jobs=[{k:r[k] for k in ['slurm_job_id','phase','state','closed']} for r in ledger['jobs']],
             failures=[str(p) for p in (ROOT/'workers').glob('*/failure.json')])
    save(ROOT/'audit/progress'/f"{now().replace(':','').replace('+','_')}.json",out)
    return out


if __name__=='__main__':print(json.dumps(status(),indent=2))
