"""Artifact helpers for the user-approved official-protocol audit only."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('outputs/qwen3vl_official_eval/v1')
OLD = Path('outputs/stage11cr/v1')
PREFIX = 'qwen3official_'
ALLOWED_NODES = ['node02', 'node03', 'node06', 'node07']

def now():
    return datetime.now(timezone.utc).isoformat()

def load(path):
    return json.loads(Path(path).read_text())

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(8*1024*1024), b''):
            h.update(block)
    return h.hexdigest()

def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as f:
        json.dump(value, f, indent=2, ensure_ascii=False)
        f.write('\n')
