"""Stage6B file contracts; all outputs stay in the project."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'outputs/stage6b'
SOURCE = ROOT / 'outputs/stage6a'


def read_json(path):
    return json.loads(Path(path).read_text())


def read_jsonl(path):
    with Path(path).open() as stream:
        return [json.loads(line) for line in stream if line.strip()]


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()


def write_json(path, value, *, freeze=False):
    path = Path(path)
    text = json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n'
    if freeze and path.exists():
        if path.read_text() != text:
            raise RuntimeError('Frozen file changed: ' + str(path))
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.part')
    temporary.write_text(text)
    temporary.replace(path)


def write_jsonl(path, rows, *, freeze=False):
    path = Path(path)
    text = ''.join(json.dumps(r, ensure_ascii=False, allow_nan=False)+'\n' for r in rows)
    if freeze and path.exists():
        if path.read_text() != text:
            raise RuntimeError('Frozen manifest changed: ' + str(path))
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def verify_stage6a():
    audit = read_json(OUT/'audit/input_preflight.json')
    for name, expected in audit['protected_stage6a_sha256'].items():
        if sha(SOURCE/name) != expected:
            raise RuntimeError('Frozen Stage6A input changed: ' + name)
    return audit
