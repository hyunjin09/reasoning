from pathlib import Path
from scripts.qwen3vl_official_eval.common import load,save,sha,now
ROOT=Path('outputs/stage12ts/v1')
OLD=Path('outputs/stage12cr/v1')
PREFIX='stage12ts_'
ALLOWED_NODES=['node02','node03','node06','node07']
