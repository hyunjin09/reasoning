"""CPU-testable reservation, resume and OOM decisions; no scientific outcomes."""
import math
from scripts.stage14c.oom_policy import is_gpu_oom, identified_sample


def budget_check(prior_charges, new_reservations):
    values=list(prior_charges)+list(new_reservations)
    if any(not math.isfinite(v) or v<0 for v in values):raise ValueError('Invalid allocation charge')
    total=sum(values)
    if total>24+1e-9:raise ValueError('Approved24GPUh ceiling exceeded')
    return total


def pending_ids(ordered_ids, completed, missing):
    ids=set(ordered_ids)
    if len(ids)!=len(ordered_ids) or completed & missing or not (completed|missing)<=ids:
        raise ValueError('Duplicate, conflicting or foreign completion identity')
    return [i for i in ordered_ids if i not in completed|missing]


def wave_groups(tasks, completed, missing):
    todo=set(pending_ids([t['task_id'] for t in tasks],completed,missing));groups={}
    for t in tasks:
        if t['task_id'] in todo:groups.setdefault(t['wave'],[]).append(t)
    return list(groups.values())


def oom_action(failure,completed,recovery_used=False):
    message='\n'.join(str(failure.get(k,'')) for k in ['error','traceback'])
    if not is_gpu_oom(message):raise RuntimeError('Non-OOM failure: hold for diagnosis')
    active=set(failure.get('active_ids',[]))
    if failure.get('pending_id'):active.add(failure['pending_id'])
    if not active or active & completed:raise RuntimeError('Startup/completed-identity OOM cannot be assigned')
    culprit=identified_sample(failure)
    if culprit:return 'SKIP',culprit
    if recovery_used:raise RuntimeError('Repeated unattributable OOM: hold')
    return 'SINGLETON_RECOVERY',None
