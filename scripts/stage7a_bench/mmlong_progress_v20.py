"""Read-only scientific progress and timing; never retry, launch or rank."""
import json
import subprocess
from datetime import datetime
from pathlib import Path

O=Path('outputs/stage7a_bench_v2')
RUN='mmlong_causal_v15_20260915'

def read(path):
    if not path.exists():return None
    try:return json.loads(path.read_text())
    except json.JSONDecodeError:return None

def main():
    workers=[];errors=[]
    cache_path=Path('runs/stage7a_bench/'+RUN+'_progress_cache.json')
    cache=read(cache_path) or {}
    for index,total in [(0,22),(1,20)]:
        name=f'{RUN}__worker{index}';base=O/'causal_pilot/raw'/name
        files=list((base/'events').glob('*.json'));events=[]
        for path in files:
            info=path.stat();stamp=[info.st_size,info.st_mtime_ns]
            saved=cache.get(str(path))
            if saved and saved['stamp']==stamp:
                row=saved['row']
            else:
                full=read(path)
                row={k:full[k] for k in ('id','complete','checks','seconds')} if full and full.get('complete') else None
                after=path.stat()
                if row and stamp==[after.st_size,after.st_mtime_ns]:cache[str(path)]=dict(stamp=stamp,row=row)
            if row and row.get('complete'):
                if any(v is not True for v in row['checks'].values()):errors.append('Failed event checks: '+row['id'])
                events.append((path.stat().st_mtime,row))
        events.sort(key=lambda pair:pair[0])
        wrapper=read(O/'causal_pilot/wrappers'/f'{name}.json')
        summary=read(base/'run_summary.json')
        if wrapper and wrapper.get('exit_code')!=0:errors.append(f'Worker{index} exit {wrapper.get("exit_code")}')
        if summary and summary.get('completed') is not True:errors.append(f'Worker{index}: '+summary.get('error','incomplete run'))
        last=events[-1][1] if events else None
        workers.append(dict(worker=index,completed=len(events),total=total,
            mechanics_passed=(base/'device_mechanics_certificate.json').exists(),
            latest_event=last['id'] if last else None,latest_seconds=round(last['seconds'],1) if last else None,
            wrapper_complete=bool(wrapper and wrapper.get('completed') and wrapper.get('exit_code')==0)))
    parent=read(O/'causal_pilot/wrappers'/f'{RUN}.json')
    if parent and parent.get('exit_code')!=0:errors.append('Parent aggregation wrapper failed')
    success=bool(parent and parent.get('completed') and parent.get('exit_code')==0)
    slurm=subprocess.check_output(['squeue','-h','-j','114451','-o','%T %N'],text=True).strip()
    if not success and slurm!='RUNNING node02':errors.append('Allocation unavailable: '+slurm)
    steps=subprocess.check_output(['squeue','--steps','-h','-j','114451','-o','%i %j'],text=True).strip()
    active_step=any(line.split()[0]!='114451.0' for line in steps.splitlines() if line.strip())
    cache['_missing_step_checks']=0 if active_step or success else cache.get('_missing_step_checks',0)+1
    if not success and cache['_missing_step_checks']>=2:
        errors.append('Scientific step ended without a successful aggregate wrapper; inspect logs before continuing')
    result=dict(recorded_at=datetime.now().astimezone().isoformat(),status='FAILED' if errors else 'COMPLETE' if success else 'RUNNING',
        completed=sum(w['completed'] for w in workers),total=42,workers=workers,allocation=slurm,active_scientific_step=active_step,errors=errors)
    temporary=cache_path.with_suffix('.pending');temporary.write_text(json.dumps(cache));temporary.replace(cache_path)
    with Path('runs/stage7a_bench/'+RUN+'_progress.jsonl').open('a') as stream:stream.write(json.dumps(result)+'\n')
    print(json.dumps(result))

if __name__=='__main__':main()
