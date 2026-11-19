"""Stage14A source-only serialization; no generation/runtime dependencies."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('outputs/stage14a/v1')


def now():
    return datetime.now(timezone.utc).isoformat()


def load(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as f:
        json.dump(value, f, indent=2, ensure_ascii=False)
        f.write('\n')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()
