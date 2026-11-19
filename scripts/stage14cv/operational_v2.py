"""Approved resource amendment; unchanged scientific inputs and old receipts."""
import datetime as dt
import math
import os
import re
import subprocess
import time
from scripts.stage14cv.common import *


def approval():
    a=load(ROOT/'spec/time_limit_recovery_approval_v1.json')
    assert a['hard_GPU_hours']==32 and a['max_total_calls']==2642
    assert sha(a['proposal'])==a['proposal_sha256']
    return a


def check_amended_budget(prior,new):
    values=list(prior)+list(new)
    if any(not math.isfinite(v) or v<0 for v in values) or sum(values)>32+1e-9:
        raise ValueError('Approved32GPUh ceiling exceeded or invalid charge')
    return sum(values)


def admit_wave(remaining_seconds,model,panel,durations):
    # Prospective operational margins, independent of answer correctness.
    baseline=300 if model=='I' else (2700 if panel=='R' else (600 if panel=='technical' else 1200))
    margin=max(baseline,1.5*max(durations,default=0)+120)
    return remaining_seconds>margin


def slurm_deadline():
    r=subprocess.run(['scontrol','show','job',os.environ['SLURM_JOB_ID'],'-o'],
                     check=True,text=True,capture_output=True)
    end=re.search(r'\bEndTime=(\S+)',r.stdout)
    assert end and end[1] not in {'Unknown','None'},'Finite Slurm deadline required'
    return dt.datetime.fromisoformat(end[1]).timestamp(),r.stdout


def output_folder(t,attempt,m):
    if t['task_id'] in m.get('context_ids',[]):
        assert attempt==1
        return ROOT/'raw/recovery_context'/t['task_id']/f'attempt_{attempt}'
    return folder(t,attempt)


def completed_receipt(t,m):
    if t['task_id'] not in m.get('context_ids',[]):return checked(t)
    p=output_folder(t,1,m)/'result.json'
    if not p.exists():return None
    r=load(p)
    assert r['task_sha256']==fingerprint(t)
    assert sha(p.parent/'input.json')==r['input_sha256']
    assert sha(p.parent/'generation.json')==r['generation_sha256']
    return p


def authorize_v2(m):
    approval();authorize(m)
    seal=load(ROOT/'audit/operational_repair_seal_v1.json')
    for p,h in seal['files'].items():assert sha(p)==h,p
    context=set(m.get('context_ids',[]))
    if m['panel']=='technical':
        allowed={f'G2_{model}_{r}_{c}' for model,c in [('I','C1'),('T','R2')] for r in [0,1]}
        assert {t['task_id'] for t in m['rows']}<=allowed
        assert {t['task_id'] for t in m['rows']}<=context<=allowed
    else:
        assert load(ROOT/'audit/operational_repair_preflight_v1.json')['status']=='PASS'
        if m['panel']=='R':
            p=load(ROOT/'audit/time_limit_recovery_proposal_v1.json')
            assert context<=set(p['context_replay_ids'])
            allowed=set(p['context_replay_ids']+p['interrupted_ids']+p['unstarted_ids'])
            assert {t['task_id'] for t in m['rows']}<=allowed
        else:assert not context
