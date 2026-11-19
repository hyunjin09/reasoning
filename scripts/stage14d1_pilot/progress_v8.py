"""Read execution metadata only, without exposing model answers."""
import json
import subprocess
from scripts.stage14d1_pilot.common import P,load,save,now


def snapshot(persist=False):
    design=load(P/'manifests/resumption_v8_design.json')
    shards=[]
    completed=set(design['completed_reuse'])
    for attempt in design['attempts']:
        manifest=load(P/'manifests'/f'{attempt}.json')
        root=P/'raw'/attempt
        requests={r['id'] for r in manifest['requests']}
        done=[];tokens=0
        for rid in requests:
            if (root/rid/'result.json').exists():
                g=load(root/rid/'generation.json');done.append(rid);tokens+=g['tokens']
        completed.update(done)
        hs=sorted((root/'heartbeats').glob('*.json'))
        h=load(hs[-1]) if hs else None
        gate=load(root/'technical_gate.json')['passed'] if (root/'technical_gate.json').exists() else None
        shards.append(dict(attempt=attempt,total=len(requests),completed=len(done),completed_tokens=tokens,
            gate=gate,heartbeat=h,exit=load(root/'exit.json') if (root/'exit.json').exists() else None,
            error=load(root/'error.json') if (root/'error.json').exists() else None))
    logical=0;full=0
    for source in design['source_states'].values():
        m=load(source)['logical_continuations'];n=sum(rid in completed for rid in m.values())
        logical+=n;full+=n==6
    accounting=subprocess.check_output(['sacct','-j','149675,149676,149690,149691','--noheader','-P',
        '--format=JobIDRaw,State,ElapsedRaw,AllocTRES,NodeList'],text=True)
    out=dict(at=now(),physical_primary_completed=len(completed),physical_primary_total=345,
        logical_completed=logical,logical_total=432,complete_families=full,families=72,
        shards=shards,slurm_accounting=accounting)
    if persist:
        import time
        save(P/'audit/progress_v8'/f'{time.time_ns()}.json',out)
    return out

if __name__=='__main__': print(json.dumps(snapshot(True),indent=2))
