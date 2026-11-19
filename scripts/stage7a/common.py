"""Stage7A artifact helpers; earlier-stage artifacts are read-only inputs."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'outputs/stage7a'


def configure_fresh_processor(processor):
    from transformers.image_utils import SizeDict
    budget = read_json(OUT / 'config/image_preprocessing.json')
    processor.image_processor.size = SizeDict(
        longest_edge=budget['max_pixels'], shortest_edge=budget['min_pixels'])
    return budget


def read_json(path):
    return json.loads(Path(path).read_text())


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value, *, freeze=False):
    path = Path(path)
    text = json.dumps(value, indent=2, ensure_ascii=False) + '\n'
    if freeze and path.exists():
        if path.read_text() != text:
            raise RuntimeError('Frozen artifact differs: ' + str(path))
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def write_jsonl(path, rows, *, freeze=False):
    path = Path(path)
    text = ''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows)
    if freeze and path.exists():
        if path.read_text() != text:
            raise RuntimeError('Frozen artifact differs: ' + str(path))
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
