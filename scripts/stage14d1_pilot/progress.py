"""Read-only progress; never opens final text or correctness for monitoring."""
import json
import subprocess
from scripts.stage14d1_pilot.common import *

def main():
    design=load(P/'manifests/main_design.json');out=[]
    for attempt in design['attempts']:
        root=P/'raw'/attempt;launch=P/'audit/launches'/f'sava14d1_pilot_{attempt}.json'
        if not launch.exists():out.append(dict(attempt=attempt,status='NOT_SUBMITTED'));continue
        job=load(launch)['job']['slurm_job_id']
        account=subprocess.check_output(['sacct','-j',job,'-X','-n','-P','--format=JobID,State,ElapsedRaw,AllocTRES'],text=True).strip()
        records=[]
        for path in root.glob('*/result.json'):
            inp=load(path.parent/'input.json');g=load(path.parent/'generation.json')
            records.append(dict(id=g['id'],kind=inp['kind'],tokens=g['tokens'],cap_hit=g['cap_hit']))
        plan=load(root/'continuation_plan.json') if (root/'continuation_plan.json').exists() else None
        logical=0;done={r['id'] for r in records if r['kind']=='solver'}
        for path in (root/'acquisition').glob('*.json'):
            state=load(path);logical+=sum(rid in done for rid in state['logical_continuations'].values())
        beats=sorted((root/'heartbeats').glob('*.json'))
        heartbeat=load(beats[-1]) if beats else None
        result=dict(attempt=attempt,job=job,slurm=account,physical_solver_done=len(done),logical_solver_done=logical,
            physical_solver_total=len(plan['requests']) if plan else None,
            logical_solver_total=plan['logical_slots'] if plan else len(load(P/'manifests'/f'{attempt}.json')['families'])*6,
            helper_calls_done=sum(r['kind']!='solver' for r in records),solver_tokens=sum(r['tokens'] for r in records if r['kind']=='solver'),
            heartbeat=heartbeat,complete=(root/'exit.json').exists(),error=load(root/'error.json') if (root/'error.json').exists() else None)
        out.append(result)
    print(json.dumps(dict(at=now(),jobs=out),indent=2))
if __name__=='__main__':main()
