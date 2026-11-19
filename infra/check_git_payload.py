#!/usr/bin/env python3
"""Validate the Git index without executing research code or printing secrets."""
from __future__ import annotations
import argparse
import pathlib
import re
import subprocess
import sys

MAX_FILE = 5 * 1024 * 1024
MAX_TOTAL = 100 * 1024 * 1024
DENIED_ROOTS = {'.venv', 'venv', 'runs', 'state', 'datasets', 'models', 'checkpoints',
                'piqd_agent_specs_v4', 'piqd_agent_sepcs_v4', '.pytest_cache'}
DENIED_PARTS = {'__pycache__', 'uv_cache', 'node_modules', '.cache', '.pytest_cache'}
LOCAL_FILES = {'ACCESS_POLICY.md', 'infra/gpu_policy.md', 'infra/gpu_scheduler.py',
               'workspace/env_state.md', 'fix_AGENTS.md'}
DENIED_SUFFIXES = {'.pt', '.pth', '.ckpt', '.safetensors', '.bin', '.npy', '.npz',
                   '.parquet', '.arrow', '.whl', '.so', '.zip', '.pem', '.key', '.log'}
SECRET_PATTERNS = [
    re.compile(rb'gh[pousr]_[A-Za-z0-9]{36,}'),
    re.compile(rb'github_pat_[A-Za-z0-9_]{60,}'),
    re.compile(rb'hf_[A-Za-z0-9]{30,}'),
    re.compile(rb'sk-(?:proj-)?[A-Za-z0-9_-]{32,}'),
    re.compile(rb'AKIA[0-9A-Z]{16}'),
    re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----\s*\n'),
    re.compile(rb'https?://[^\s/:]+:[^\s/@]+@'),
]


def problems(path: str, mode: str, data: bytes) -> list[str]:
    p = pathlib.PurePosixPath(path)
    issues = []
    if p.parts[0] in DENIED_ROOTS or any(x in DENIED_PARTS for x in p.parts):
        issues.append('local/artifact/cache directory')
    if path in LOCAL_FILES or p.name == '.env' or p.name.startswith('.env.'):
        issues.append('machine-local or environment file')
    if p.suffix in DENIED_SUFFIXES:
        issues.append('binary/artifact/credential extension')
    if mode not in {'100644', '100755'}:
        issues.append('symlink or non-regular Git object')
    if len(data) > MAX_FILE:
        issues.append('larger than 5 MiB')
    if b'\0' in data:
        issues.append('binary payload')
    if any(pattern.search(data) for pattern in SECRET_PATTERNS):
        issues.append('possible credential; value suppressed')
    return issues


def self_test() -> None:
    assert not problems('scripts/example.py', '100644', b'print("ok")\n')
    assert problems('.venv/lib/file.py', '100644', b'x')
    assert problems('workspace/uv_cache/file.py', '100644', b'x')
    assert problems('infra/gpu_scheduler.py', '100644', b'x')
    assert problems('scripts/data.pt', '100644', b'x')
    assert problems('scripts/link.py', '120000', b'/external/path')
    assert problems('scripts/large.py', '100644', b'x' * (MAX_FILE + 1))
    assert problems('scripts/value.py', '100644', b'\0')
    assert problems('scripts/config.py', '100644', b'ghp_' + b'A' * 36)
    assert problems('scripts/config.py', '100644', b'hf_' + b'B' * 30)
    assert problems('scripts/config.py', '100644', b'https://' + b'name:password@example.org')
    assert not problems('infra/templates/gpu_scheduler.py.example', '100644', b'# configure')
    print('Payload guard: 12 regression checks passed.')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    root = subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], text=True).strip()
    raw = subprocess.check_output(['git', 'ls-files', '--stage', '-z'], cwd=root)
    entries = []
    for entry in raw.split(b'\0'):
        if not entry:
            continue
        meta, name = entry.split(b'\t', 1)
        mode, oid, stage = meta.decode().split()
        if stage != '0':
            print('FAIL: unresolved merge entries in index', file=sys.stderr)
            return 1
        entries.append((name.decode(), mode, oid))
    if not entries:
        print('FAIL: empty index; stage the intended files first.', file=sys.stderr)
        return 1
    # Also reject files force-added through the documented ignore boundary.
    ignored = subprocess.run(
        ['git', 'check-ignore', '--no-index', '-z', '--stdin'], cwd=root,
        input=b''.join(p.encode()+b'\0' for p, _, _ in entries), stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, check=False,
    )
    if ignored.returncode not in {0, 1}:
        print('FAIL: could not verify ignore rules.', file=sys.stderr)
        return 1
    ignored_paths = {p.decode() for p in ignored.stdout.split(b'\0') if p}
    # Check sizes before loading blobs, so an accidental multi-GB file cannot
    # exhaust memory before the guard gets a chance to reject it.
    request = ''.join(oid+'\n' for _, _, oid in entries).encode()
    metadata = subprocess.check_output(['git', 'cat-file', '--batch-check'], cwd=root, input=request)
    headers = [line.decode().split() for line in metadata.splitlines()]
    if len(headers) != len(entries) or any(len(h) != 3 or h[1] != 'blob' for h in headers):
        print('FAIL: non-blob or invalid staged object.', file=sys.stderr)
        return 1
    oversized = [entries[i][0] for i, h in enumerate(headers) if int(h[2]) > MAX_FILE]
    if oversized or sum(int(h[2]) for h in headers) > MAX_TOTAL:
        for path in oversized:
            print(f'FAIL {path}: larger than 5 MiB', file=sys.stderr)
        print('FAIL: payload size policy; blobs were not loaded.', file=sys.stderr)
        return 1
    # Use one process; inspect the exact staged bytes, not mutable working files.
    batch = subprocess.run(
        ['git', 'cat-file', '--batch'], cwd=root,
        input=''.join(oid+'\n' for _, _, oid in entries).encode(),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    ).stdout
    cursor = total = 0
    failures = []
    for path, mode, oid in entries:
        end = batch.index(b'\n', cursor)
        header = batch[cursor:end].decode().split()
        if len(header) != 3 or header[1] != 'blob':
            print('FAIL: unexpected staged object type.', file=sys.stderr)
            return 1
        size = int(header[2]); cursor = end + 1
        data = batch[cursor:cursor+size]; cursor += size + 1; total += size
        issues = problems(path, mode, data)
        if path in ignored_paths:
            issues.append('force-added despite ignore policy')
        if issues:
            failures.append((path, issues))
    if total > MAX_TOTAL:
        failures.append(('<index>', ['total exceeds 100 MiB; review artifact selection']))
    for path, issues in failures:
        print(f'FAIL {path}: {"; ".join(issues)}', file=sys.stderr)
    print(f'Index: {len(entries)} files, {total / 1024 / 1024:.2f} MiB, {len(failures)} violations.')
    return int(bool(failures))


if __name__ == '__main__':
    raise SystemExit(main())
