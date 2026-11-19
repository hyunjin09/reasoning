from pathlib import Path
from scripts.stage9a3.prepare import load,save,sha,now

ROOT=Path('outputs/stage10ar/v1')
OLD=Path('outputs/stage9a5/v1')
PRIOR=Path('outputs/stage10a/v1')
DATA=Path('outputs/stage9a3/v1')
PROTOCOL=Path('plan/stage10ar_execution_protocol_v1.md')


def verify_config():
    cfg=load(ROOT/'config.json')
    assert sha(PROTOCOL)==cfg['protocol_sha256']
    for p,d in cfg['inputs_sha256'].items():assert sha(p)==d,p
    return cfg
