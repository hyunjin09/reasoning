"""Stage-local provenance and immutable artifact helpers."""
from pathlib import Path
from scripts.stage9a3.prepare import load,save,sha,now

ROOT=Path('outputs/stage10a/v1')
OLD=Path('outputs/stage9a5/v1')
DATA=Path('outputs/stage9a3/v1')
PROTOCOL=Path('plan/stage10a_execution_protocol_v1.md')


def verify_config():
    cfg=load(ROOT/'config.json')
    for p,d in cfg['inputs_sha256'].items():assert sha(p)==d,p
    assert sha(PROTOCOL)==cfg['protocol_sha256']
    return cfg
