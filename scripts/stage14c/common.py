"""Stage14C immutable run receipts; no parent output mutations."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
ROOT=Path('outputs/stage14c')
ALLOWED_NODES={'node02','node03','node06','node07'}
PREFIX='vr_stage14c_'
def now():return dt.datetime.now(dt.timezone.utc).isoformat()
def load(path):return json.loads(Path(path).read_text())
def rows(path):return [json.loads(x) for x in Path(path).read_text().splitlines() if x.strip()]
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()
def fingerprint(value):return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def save(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+f'.{os.getpid()}.tmp')
    with tmp.open('x') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    try:os.link(tmp,path)
    finally:tmp.unlink()
def write_rows(path,values):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as f:
        for v in values:f.write(json.dumps(v,ensure_ascii=False,sort_keys=True)+'\n')
def all_tasks(mode):return rows(ROOT/'manifests'/f'{mode}_tasks.jsonl')
def result_dir(task,attempt=0):return ROOT/'raw'/task['collection']/task['task_id']/f'attempt_{attempt}'
def checked_result(task):
    found=[]
    for p in (ROOT/'raw'/task['collection']/task['task_id']).glob('attempt_*/result.json'):
        r=load(p);assert r['task_sha256']==fingerprint(task)
        assert sha(p.parent/'generation.json')==r['generation_sha256']
        assert sha(p.parent/'input.json')==r['input_sha256'];found.append(p)
    assert len(found)<=1,('duplicate logical completions',task['task_id'])
    return found[0] if found else None
