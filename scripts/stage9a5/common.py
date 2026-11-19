"""Stage-local immutable state; prior stage inputs remain untouched."""
from pathlib import Path
from scripts.stage9a3.prepare import load,save,sha,now

ROOT=Path('outputs/stage9a5/v1')
OLD=Path('outputs/stage9a3/v1')
COT=Path('outputs/stage9a4/v1')
PROTOCOL=Path('plan/stage9a5_execution_protocol_v1.md')


def tasks(split):
    return [r for r in load(ROOT/'audit/inference_tasks.json')['rows'] if r['split']==split]


def verify_config():
    c=load(ROOT/'config.json')
    for p,d in c['inputs_sha256'].items():assert sha(p)==d,p
    assert sha(PROTOCOL)==c['protocol_sha256']
    return c
