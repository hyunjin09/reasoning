"""Immutable calibration attempts, exact-task reuse, and bounded technical resume."""
import argparse
from scripts.stage11c.common import ROOT, load, save, sha, now
from scripts.stage11c.watch_jobs import TERMINAL


def collect():
    original_path = ROOT/'calibration_tasks.json'
    original = load(original_path)
    tasks = {r['task_id']: r for s in original['shards'] for r in s['rows']}
    models = {r['task_id']: s['model_key'] for s in original['shards'] for r in s['rows']}
    valid, attempts = {}, []
    paths = [original_path] + sorted(ROOT.glob('calibration_tasks_retry*.json'))
    for path in paths:
        manifest = load(path)
        assert manifest['frozen'] and manifest['config_sha256'] == sha(ROOT/'config.json')
        for shard in manifest['shards']:
            for task in shard['rows']:
                ident = task['task_id']
                assert task == tasks[ident] and shard['model_key'] == models[ident]
                dest = ROOT/manifest['queue']/'results'/ident/'result.json'
                if not dest.exists():
                    continue
                receipt = load(dest)
                assert receipt['manifest_sha256'] == sha(path)
                assert receipt['config_sha256'] == sha(ROOT/'config.json')
                assert receipt['task_id'] == ident and receipt['batch_size'] == 1
                assert receipt['arm'] == task['arm'] and receipt['cap'] == task['max_new_tokens']
                assert receipt['generation_sha256'] == sha(dest.parent/'generation.json')
                assert receipt['input_sha256'] == sha(dest.parent/'input.json')
                attempts.append(dict(task_id=ident, path=str(dest), manifest_path=str(path),
                                     interrupted=receipt['budget_interrupted']))
                if not receipt['budget_interrupted']:
                    assert ident not in valid, 'Never silently pick between duplicate valid scientific runs'
                    valid[ident] = dict(receipt=receipt, path=str(dest), manifest_path=str(path))
    return original, tasks, models, valid, attempts


def resume(version, parts=1):
    assert version >= 1
    assert parts in (1, 2)
    original, tasks, models, valid, attempts = collect()
    # Do not race a still-running calibration worker, including prior retries.
    jobs = [j for j in load('state/gpu_experiment_queue.json')['jobs']
            if j['id'].startswith('stage11c_cap_') or j['id'].startswith('stage11c_calretry')]
    assert jobs
    for job in jobs:
        path = ROOT/'audit/terminal_receipts'/f'{job["slurm_job_id"]}.json'
        assert path.exists() and load(path)['fields']['JobState'] in TERMINAL
    remaining = [task for ident, task in tasks.items() if ident not in valid]
    assert remaining
    shards = []
    for model in ['thinking', 'instruct']:
        rows = [r for r in remaining if models[r['task_id']]==model]
        for part in range(parts):
            shards.append(dict(id=f'{model}_{part}', model_key=model, rows=rows[part::parts]))
    shards = [s for s in shards if s['rows']]
    name = f'calibration_retry{version}'
    save(ROOT/f'calibration_tasks_retry{version}.json', dict(at=now(), frozen=True,
        queue=name, config_sha256=sha(ROOT/'config.json'), shards=shards,
        original_manifest_sha256=sha(ROOT/'calibration_tasks.json'),
        completed_valid_reused=len(valid), unfinished_calls=len(remaining),
        immutable_attempts=attempts,
        reason='Resume exact unfinished technical cases after finite allocation ends; completed valid calls reused, interrupted outputs preserved as technical unknowns.'))
    (ROOT/name/'claims').mkdir(parents=True, exist_ok=False)
    print('CALIBRATION_REMAINDER', len(remaining), 'VALID_REUSED', len(valid),
          [(s['id'], len(s['rows'])) for s in shards])


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--resume-version', type=int)
    p.add_argument('--parts', type=int, default=1)
    a = p.parse_args()
    if a.resume_version:
        resume(a.resume_version, a.parts)
    else:
        original, tasks, models, valid, attempts = collect()
        print('CALIBRATION_VALID', len(valid), '/', len(tasks), 'ATTEMPTS', len(attempts))
