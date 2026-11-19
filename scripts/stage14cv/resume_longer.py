"""One bounded, CPU-only handoff after a safe wave checkpoint.

The sealed inference worker, scientific manifests, and model recipes stay intact.
"""
import time
from collections import defaultdict

from scripts.stage14cv.common import ROOT, checked, folder, load, now, save, sha, tasks
from scripts.stage14cv.control import budget_check
from scripts.stage14cv.launch import accounting, launch

OLD_JOBS = {'139758', '139759', '139760'}
# Remaining R0/R1 waves use measured wave durations; R2 has not generated yet.
RESERVATIONS = {'R0': 5.25, 'R1': 4.0, 'R2': 6.0}


def validate_checkpoint(wave_ids, attempted, completed):
    ordered = [task_id for _, task_id in wave_ids]
    if len(set(ordered)) != len(ordered) or not completed <= set(ordered):
        raise ValueError('Invalid task identity')
    if attempted != completed:
        raise ValueError('An attempted call lacks a completed receipt; do not restart')
    groups = defaultdict(set)
    for wave, task_id in wave_ids:
        groups[wave].add(task_id)
    if any(group & completed and not group <= completed for group in groups.values()):
        raise ValueError('Partial wave would change the frozen batch context')
    return [task_id for task_id in ordered if task_id not in completed]


def main():
    audit = ROOT / 'audit'
    seal = load(audit / 'time_limit_resume_adapter_seal_v1.json')
    for path, digest in seal['files'].items():
        assert sha(path) == digest, path
    sentinel = audit / 'STOP_BETWEEN_WAVES'
    assert sentinel.exists(), 'Drain signal must stay in place until all old jobs exit'
    save(audit / 'time_limit_resume_coordinator_started_v1.json',
         dict(at=now(),old_jobs=sorted(OLD_JOBS),reservations=RESERVATIONS))
    deadline = time.monotonic() + 25 * 60
    while True:
        # Cache each terminal Slurm duration promptly: sacct is disabled here.
        charges = accounting()
        old = {c['job_id']: c for c in charges if c['job_id'] in OLD_JOBS}
        assert len(old) == len(OLD_JOBS)
        if all(c['state'] == 'COMPLETED' for c in old.values()):
            break
        assert all(c['state'] in {'RUNNING', 'COMPLETING', 'PENDING', 'COMPLETED'}
                   for c in old.values()), 'Unexpected terminal state: hold for review'
        assert time.monotonic() < deadline, 'Drain deadline: leave stop signal and hold'
        time.sleep(15)
    for job_id in OLD_JOBS:
        receipt = load(audit / 'workers' / job_id / 'exit.json')
        assert receipt.get('checkpoint') or receipt.get('complete'), receipt
    remaining = {}
    all_rows = tasks('R')
    for condition in RESERVATIONS:
        selected = [t for t in all_rows if t['model_key'] == 'T' and t['condition'] == condition]
        completed = {t['task_id'] for t in selected if checked(t)}
        attempted = {t['task_id'] for t in selected if (folder(t) / 'input.json').exists()}
        remaining[condition] = validate_checkpoint(
            [(t['wave'], t['task_id']) for t in selected], attempted, completed)
    total = budget_check([c['charge_GPUh'] for c in charges],
                         [h for c, h in RESERVATIONS.items() if remaining[c]])
    save(audit / 'time_limit_checkpoint_validation_v1.json',
         dict(at=now(),status='PASS',charges=charges,remaining=remaining,
              conservative_reserved_GPUh=total,hard_GPUh=24,
              incomplete_attempts=0,partial_waves=0,scientific_changes=False))
    # Only after every old worker has exited and all receipts have been checked.
    sentinel.rename(audit / 'STOP_BETWEEN_WAVES_applied_v1.txt')
    for condition, hours in RESERVATIONS.items():
        if remaining[condition]:
            launch('R', 'T', condition, hours, allow_pending=True)
    save(audit / 'time_limit_resume_release_v1.json',
         dict(at=now(),status='SUBMITTED',reservations=RESERVATIONS,
              remaining_counts={c:len(ids) for c,ids in remaining.items()},
              C_launched=False,follow_on_launched=False))


if __name__ == '__main__':
    try:
        main()
    except BaseException as exc:
        save(ROOT / 'audit/time_limit_resume_failure_v1.json',
             dict(at=now(),error=repr(exc),action='HOLD_FOR_REVIEW'))
        raise
