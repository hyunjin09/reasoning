"""Outcome-blind, bounded OOM recovery under the user's skip amendment."""
import re
from scripts.stage14c.common import *

AMENDMENT = ROOT/'spec/model_and_recipe_identity.json'

def verify_recovery():
    assert load(ROOT/'audit/g1_final_source_seal_v1.json')['status']=='G1_PASS'
    for p,h in load(ROOT/'audit/g2_execution_seal_v1.json')['files'].items():assert sha(p)==h,p


def is_gpu_oom(text):
    return bool(re.search(r'CUDA(?: error:)? out of memory|CUDA_ERROR_OUT_OF_MEMORY|torch(?:\.cuda)?\.OutOfMemoryError', text, re.I))


def missing_path(task):
    return ROOT/'scoring/technical_missingness'/f"{task['task_id']}.json"


def mark_missing(task, reason, evidence):
    assert checked_result(task) is None, 'Never discard a valid completed result'
    p = missing_path(task)
    if p.exists():
        old = load(p)
        assert old['task_sha256'] == fingerprint(task) and old['final_technical_failure']
        return
    save(p, dict(at=now(), task_id=task['task_id'], task_sha256=fingerprint(task),
                 status='TECHNICAL_MISSING', final_technical_failure=True,
                 reason=reason, evidence=evidence, correctness_used=False,
                 amendment=str(AMENDMENT)))


def remaining(tasks):
    pending, attempts = [], {}
    for task in tasks:
        if checked_result(task):
            assert not missing_path(task).exists(), 'Result/missingness conflict'
            continue
        if missing_path(task).exists():
            r = load(missing_path(task))
            assert r['task_sha256'] == fingerprint(task) and r['final_technical_failure']
            continue
        folders = list((ROOT/'raw'/task['collection']/task['task_id']).glob('attempt_*'))
        for folder in folders:
            failure = folder/'technical_failure.json'
            if failure.exists() and load(failure).get('reason') != 'OOM_SKIP':
                raise RuntimeError(f"non-OOM failure requires review: {task['task_id']}")
        if result_dir(task, 1).exists():
            mark_missing(task, 'INFRASTRUCTURE_RETRY_EXHAUSTED', dict(attempt_directories=[str(p) for p in folders]))
            continue
        attempts[task['task_id']] = int(bool(folders))
        pending.append(task)
    return pending, attempts


def identified_sample(failure):
    # Preparation happens outside the engine; otherwise only a singleton engine
    # request is attributable. Batched scheduler failure has no known culprit.
    if failure.get('phase') == 'prepare':
        return failure.get('pending_id')
    ids = list(dict.fromkeys(failure.get('active_ids', []) +
                            ([failure['pending_id']] if failure.get('pending_id') else [])))
    return ids[0] if len(ids) == 1 else None


def resolve_oom(tasks, failure, log, evidence):
    if not is_gpu_oom(log + '\n' + failure.get('traceback', '') + '\n' + failure.get('error', '')):
        raise RuntimeError('non-OOM failure requires review')
    task_by_id = {t['task_id']: t for t in tasks}
    affected = set(failure.get('active_ids', []))
    if failure.get('pending_id'):
        affected.add(failure['pending_id'])
    if not affected:
        raise RuntimeError('OOM before a sample was active; startup/infrastructure hold')
    assert affected <= task_by_id.keys()
    culprit = identified_sample(failure)
    if culprit:
        mark_missing(task_by_id[culprit], 'OOM_SKIP', evidence)
    return culprit
