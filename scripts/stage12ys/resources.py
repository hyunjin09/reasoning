"""Conservative allocation accounting with immutable live Slurm snapshots."""
import datetime as dt
import re
import subprocess
from zoneinfo import ZoneInfo
from scripts.stage12ys.execution import ROOT,load,save,now

def timestamp(text):
    if not text or text in ['Unknown','None','N/A']:return None
    return dt.datetime.fromisoformat(text).replace(tzinfo=ZoneInfo('Asia/Seoul')).timestamp()

def account(tag):
    previous={}
    snapshots=sorted((ROOT/'audit/resources').glob('*.json'))
    if snapshots:previous={r['slurm_job_id']:r for r in load(snapshots[-1])['jobs']}
    registrations=[]
    for p in (ROOT/'audit/launches').glob('*.json'):registrations+=load(p)['jobs']
    assert len({str(j['slurm_job_id']) for j in registrations})==len(registrations)
    current=dt.datetime.now(dt.timezone.utc);rows=[]
    for job in registrations:
        jid=str(job['slurm_job_id']);old=previous.get(jid,{})
        if old.get('closed'):
            rows.append(old);continue
        proc=subprocess.run(['scontrol','show','job',jid,'-o'],capture_output=True,text=True)
        fields=dict(re.findall(r'(\w+)=(\S+)',proc.stdout))
        state=fields.get('JobState','NOT_IN_SLURM')
        start=timestamp(fields.get('StartTime')) or old.get('start_timestamp')
        # A predicted StartTime for a pending job is not an allocation start.
        if state=='PENDING':start=None
        end=timestamp(fields.get('EndTime'))
        closed=state not in ['RUNNING','PENDING','COMPLETING','CONFIGURING','SUSPENDED']
        if state=='PENDING':upper=0.0
        elif start is not None:
            # COMPLETING still reserves resources even when Slurm EndTime exists.
            last=end if closed and end is not None else current.timestamp()
            upper=max(0,last-start)/3600
        else:
            # Purged before first running observation: retain a safe launch-to-disappearance bound.
            launch=dt.datetime.fromisoformat(job['registered_at']).timestamp()
            upper=max(0,current.timestamp()-launch)/3600
        requested=job['minutes']/60
        rows.append(dict(slurm_job_id=jid,phase=job['phase'],state=state,closed=closed,
            start_timestamp=start,upper_gpu_hours=upper,
            committed_gpu_hours=upper if closed else max(requested,upper),
            requested_minutes=job['minutes'],observed_at=current.isoformat(),
            raw_scontrol=proc.stdout,stderr=proc.stderr,
            end_basis='Slurm terminal EndTime' if closed and end else 'Observed time; conservative if record disappeared'))
    result=dict(at=current.isoformat(),tag=tag,jobs=rows,
        allocated_gpu_hours_upper=sum(r['upper_gpu_hours'] for r in rows),
        committed_gpu_hours_upper=sum(r['committed_gpu_hours'] for r in rows),hard_gpu_hours=16,
        active_jobs=[r['slurm_job_id'] for r in rows if not r['closed']])
    save(ROOT/'audit/resources'/f'{current.strftime("%Y%m%dT%H%M%S%f")}_{tag}.json',result)
    return result

if __name__=='__main__':
    import json
    r=account('status');print(json.dumps({k:v for k,v in r.items() if k!='jobs'}))
