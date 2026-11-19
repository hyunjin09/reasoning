"""Preserve native evidence and advance only after an identified sample CUDA OOM."""
from copy import deepcopy
from pathlib import Path
import subprocess
import time

from scripts.stage7a.common import ROOT, read_json, sha, write_json

OUT = ROOT / 'outputs/stage7a_bench_v2'
OOM_EXIT = 75


def claim_next(state, rank, predecessor):
    if type(rank) is not int or not 0 <= rank < 4:
        raise ValueError('Expected one of four Slurm task ranks')
    if (state.get('startup_error') or state.get('worker_errors') or
            any(b['status'] == 'failed' for b in state['batches'])):
        return None
    if any(b['status'] == 'running' and b['rank'] == rank for b in state['batches']):
        raise ValueError('Worker already owns an active batch')
    old = {b['run_id']: b for b in predecessor['batches']}
    for batch in state['batches']:
        if batch['status'] != 'pending':
            continue
        if old[batch['predecessor_run_id']]['status'] == 'running':
            continue
        batch.update(status='running', rank=rank)
        return deepcopy(batch)
    return None


def result_records(dest):
    return {p.parent.name: read_json(p) for p in (Path(dest) / 'examples').glob('*/result.json')}


def restart_after_oom(code, before, results, allowed):
    if code == 0:
        return False
    if code != OOM_EXIT:
        raise ValueError(f'Non-recoverable native exit {code}')
    ids = set(results)
    new = ids - before
    if not before <= ids <= allowed or not new:
        raise ValueError('OOM restart requires preserved results and forward progress')
    failures = [results[x] for x in new if results[x].get('unavailable_reason') == 'cuda_oom'
                and results[x].get('unavailable') is True]
    if len(failures) != 1:
        raise ValueError('Exactly one newly recorded native sample CUDA OOM required')
    return True


def run_attempts(command, dest, log_path, allowed):
    """Use a fresh OS process after each recorded OOM, with bounded progress."""
    dest, log_path = Path(dest), Path(log_path)
    attempts = []
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open('x') as log:
        for attempt in range(len(allowed) + 1):
            before = set(result_records(dest))
            current = command + (['--resume'] if (dest / 'signature.json').exists() else [])
            started = time.time()
            code = subprocess.call(current, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
            record = dict(attempt=attempt, command=current, exit_code=code,
                          started_unix=started, finished_unix=time.time(),
                          elapsed_seconds=time.time() - started)
            saved = result_records(dest)
            record['terminal_events_before'] = sorted(before)
            record['terminal_events_after'] = sorted(saved)
            attempts.append(record)
            attempt_dir = dest / 'process_attempts' / str(attempt)
            write_json(attempt_dir / 'result.json', record, freeze=True)
            for name in ('environment.json', 'mechanics.json'):
                if (dest / name).exists():
                    (attempt_dir / name).write_bytes((dest / name).read_bytes())
            if code == 0:
                if set(saved) != allowed:
                    raise ValueError('Successful process omitted native events')
                return code, attempts
            if code != OOM_EXIT:
                return code, attempts
            restart_after_oom(code, before, saved, allowed)
            log.write('\nRESTART_AFTER_RECORDED_SAMPLE_OOM\n')
            log.flush()
    raise ValueError('OOM continuation exceeded its finite event budget')


def oom_result(row, example, elapsed, error):
    return dict(event_id=row['event_id'], base_id=row['base_id'], benchmark=row['benchmark'],
        condition=row['condition'], family_id=row['family_id'], complete=False,
        unavailable=True, unavailable_reason='cuda_oom', ended_with_eos=None,
        artifact_dir=str(example.relative_to(ROOT)), elapsed_seconds=elapsed,
        generation_sha256=None, tokens_sha256=None, token_count=0, truncated=None,
        error=error, scientific_state=None,
        interpretation='Observed native CUDA OOM; resource exclusion, not a model error or causal state; no retry')


def preserve_predecessor(dest, rows, old_batch, source_plan_ref):
    """Reuse terminal artifacts only after the original model subprocess exits."""
    dest = Path(dest)
    plan_path = (ROOT / source_plan_ref['path']).resolve()
    if not plan_path.is_relative_to(OUT / 'config') or sha(plan_path) != source_plan_ref['sha256']:
        raise ValueError('Predecessor execution provenance changed')
    source_plan = read_json(plan_path)
    specs = [b for b in source_plan['batches'] if b['run_id'] == old_batch['run_id']]
    if len(specs) != 1 or old_batch['log_path'] != specs[0]['log_path']:
        raise ValueError('Predecessor batch identity changed')
    selection = read_json(ROOT / source_plan['selection']['path'])
    if sha(ROOT / source_plan['selection']['path']) != source_plan['selection']['sha256']:
        raise ValueError('Predecessor selection changed')
    members = next(b['event_ids'] for b in selection['batches'] if b['run_id'] == old_batch['run_id'])
    if members != [r['event_id'] for r in rows]:
        raise ValueError('Continuation changed predecessor batch membership')
    status = old_batch['status']
    if status not in ('pending', 'succeeded', 'failed'):
        raise ValueError('Cannot import an active or unknown predecessor')
    source = OUT / 'native_screen/generations' / old_batch['run_id']
    ledger = dict(predecessor_run_id=old_batch['run_id'], predecessor_status=status,
                  source_execution=source_plan_ref, preserved=[], runtime_oom=[])
    if status == 'pending':
        if source.exists():
            raise ValueError('Pending predecessor unexpectedly has native artifacts')
        write_json(dest / 'predecessor_import.json', ledger, freeze=True)
        return ledger
    wrapper_path = OUT / 'raw' / old_batch['run_id'] / 'run_summary.json'
    wrapper = read_json(wrapper_path)
    if (wrapper['plan_sha256'] != source_plan_ref['sha256'] or
            wrapper['exit_code'] != old_batch['exit_code']):
        raise ValueError('Predecessor exit provenance mismatch')
    signature = read_json(source / 'signature.json')
    if signature['event_ids'] != members:
        raise ValueError('Predecessor signature changed event ownership')
    for path, digest in signature['dependencies'].items():
        if sha(ROOT / path) != digest:
            raise ValueError('Predecessor dependency changed: ' + path)
    missing = []
    for row in rows:
        old = source / 'examples' / row['event_id']
        target = dest / 'examples' / row['event_id']
        if not (old / 'result.json').exists():
            missing.append(row)
            continue
        result = read_json(old / 'result.json')
        if result['event_id'] != row['event_id'] or read_json(old / 'manifest_row.json') != row:
            raise ValueError('Predecessor result/input identity mismatch')
        if not result.get('unavailable'):
            for file, key in [('generation.json', 'generation_sha256'), ('tokens.jsonl', 'tokens_sha256')]:
                if sha(old / file) != result[key]:
                    raise ValueError('Predecessor output hash mismatch')
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() or target.is_symlink():
            if not target.is_symlink() or target.resolve() != old.resolve():
                raise ValueError('Refusing to overwrite native output')
        else:
            target.symlink_to(old, target_is_directory=True)
        ledger['preserved'].append(dict(event_id=row['event_id'], source=str(old.relative_to(ROOT)),
                                       result_sha256=sha(old / 'result.json')))
    if status == 'succeeded' and (missing or wrapper['exit_code'] != 0):
        raise ValueError('Successful predecessor lacks full accounted coverage')
    if status == 'failed':
        log = ROOT / old_batch['log_path']
        text = log.read_text()
        checks = read_json(source / 'mechanics.json')['checks']
        if (not missing or wrapper['exit_code'] == 0 or 'MECHANICS_PASSED' not in text or
                not checks or not all(c['repeat_token_ids_exact'] for c in checks) or
                'torch.OutOfMemoryError: CUDA out of memory.' not in text or
                'scripts/stage7a_bench/document_runtime_v2.py' not in text):
            raise ValueError('Failed predecessor is not a verified native sample CUDA OOM')
        row = missing[0]
        old = source / 'examples' / row['event_id']
        if (not (old / 'input.json').exists() or read_json(old / 'manifest_row.json') != row or
                any((source / 'examples' / r['event_id'] / 'input.json').exists() for r in missing[1:])):
            raise ValueError('Native OOM sample identity is ambiguous')
        target = dest / 'examples' / row['event_id']
        result = oom_result(row, target, 0.0, next(l for l in text.splitlines() if l.startswith('torch.OutOfMemoryError:')))
        result['predecessor_failure'] = dict(log_path=str(log.relative_to(ROOT)), log_sha256=sha(log),
            wrapper_path=str(wrapper_path.relative_to(ROOT)), wrapper_sha256=sha(wrapper_path),
            partial_artifact_dir=str(old.relative_to(ROOT)), cost_accounting='Already charged to predecessor wrapper')
        write_json(target / 'manifest_row.json', row, freeze=True)
        write_json(target / 'result.json', result, freeze=True)
        ledger['runtime_oom'].append(row['event_id'])
    write_json(dest / 'predecessor_import.json', ledger, freeze=True)
    return ledger
