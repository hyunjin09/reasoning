import datetime as dt
import hashlib
import json
from pathlib import Path

ROOT=Path('outputs/stage12xs/v1')
ALLOWED_NODES={'node02','node03','node06','node07'}
def now():return dt.datetime.now(dt.timezone.utc).isoformat()
def load(path):return json.loads(Path(path).read_text())
def save(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as f:json.dump(value,f,ensure_ascii=False,indent=2)
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

