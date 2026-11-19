"""Validate an explicitly recorded allocation move without rewriting old runs."""
from pathlib import Path
import re

from scripts.stage7a.common import read_json, sha


def validate_runtime_move(original, replacement):
    for key in ('model_checkpoint', 'locked_generation_protocol'):
        if original[key] != replacement[key]:
            raise ValueError('Allocation move changes the frozen model/protocol')
    operational = {'slurm_allocation', 'node', 'gpus', 'cpus', 'host_memory',
                   'tmux_session', 'tmux_pane'}
    old = {k: v for k, v in original['runtime'].items() if k not in operational}
    new = {k: v for k, v in replacement['runtime'].items() if k not in operational}
    if old != new:
        raise ValueError('Allocation move changes scientific runtime settings')


def pending_rows(root, rows, packet, run_id):
    root = Path(root).resolve()
    ids = [row['event_id'] for row in rows]
    completed = packet['completed_event_ids']
    if (packet.get('status') != 'FROZEN_ALLOCATION_CONTINUATION' or
            packet.get('continuation_run_id') != run_id or
            packet.get('all_event_ids') != ids or len(set(ids)) != len(ids) or
            not completed or completed != ids[:len(completed)] or len(completed) >= len(ids)):
        raise ValueError('Continuation identity/order must preserve the completed prefix')
    predecessor = packet['predecessor_run_id']
    if not re.fullmatch(r'[a-z0-9_]+', predecessor) or predecessor == run_id:
        raise ValueError('Unsafe or identical predecessor run')
    protected = packet['protected_files']
    if not protected:
        raise ValueError('Continuation requires protected original evidence')
    for name, digest in protected.items():
        path = (root / name).resolve()
        if not path.is_relative_to(root):
            raise ValueError('Protected evidence outside the project')
        if not path.is_file() or sha(path) != digest:
            raise ValueError('Changed or missing protected evidence: ' + name)
    base = root / 'outputs/stage7a_bench_v2/native_screen/generations' / predecessor
    for row in rows[:len(completed)]:
        directory = base / 'examples' / row['event_id']
        required = [directory / n for n in ('result.json', 'manifest_row.json')]
        result = read_json(required[0])
        if read_json(required[1]) != row or result['event_id'] != row['event_id']:
            raise ValueError('Completed source row changed')
        if not result.get('unavailable'):
            for name, extension in [('generation', '.json'), ('tokens', '.jsonl')]:
                path = directory / (name + extension)
                required.append(path)
                if sha(path) != result[name + '_sha256']:
                    raise ValueError('Completed native response changed')
        if any(str(path.relative_to(root)) not in protected for path in required):
            raise ValueError('Completed response is not protected by the continuation')
    existing = {p.parent.name for p in base.glob('examples/*/result.json')}
    if existing != set(completed):
        raise ValueError('Predecessor completion changed after continuation freeze')
    return rows[len(completed):]
