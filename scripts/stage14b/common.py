"""Stage-local immutable receipts and compact frozen task manifests."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path

ROOT=Path('outputs/stage14b')
SOURCE=Path('outputs/stage14a/v1')
ALLOWED_NODES={'node02','node03','node06','node07'}
PREFIX='vr_stage14b_'

def now():return dt.datetime.now(dt.timezone.utc).isoformat()
def load(path):return json.loads(Path(path).read_text())
def rows(path):return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()
def fingerprint(value):return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def save(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    data=json.dumps(value,ensure_ascii=False,indent=2)+'\n'
    temporary=path.with_name(path.name+f'.{os.getpid()}.tmp')
    with temporary.open('x') as f:f.write(data);f.flush();os.fsync(f.fileno())
    try:os.link(temporary,path)
    finally:temporary.unlink()
def write_text(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as f:f.write(value)
def write_rows(path,values):write_text(path,''.join(json.dumps(v,ensure_ascii=False,sort_keys=True)+'\n' for v in values))
def stage14a(name):return load(SOURCE/f'stage14a_{name}.json')
def all_tasks(mode):return rows(ROOT/'manifests'/f'{mode}_tasks.jsonl')
def result_dir(task,attempt=0):
    return ROOT/'raw'/task['collection']/task['task_id']/f'attempt_{attempt}'
def checked_result(task):
    found=[]
    for p in (ROOT/'raw'/task['collection']/task['task_id']).glob('attempt_*/result.json'):
        r=load(p)
        assert r['task_sha256']==fingerprint(task)
        assert sha(p.parent/'generation.json')==r['generation_sha256']
        assert sha(p.parent/'input.json')==r['input_sha256']
        found.append(p)
    assert len(found)<=1,('duplicate logical completions',task['task_id'])
    return found[0] if found else None
