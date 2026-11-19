from pathlib import Path
from scripts.qwen3vl_official_eval.common import load,save,sha,now
ROOT=Path('outputs/stage12a/v1')
PREFIX='stage12a_'
ALLOWED_NODES=['node02','node03','node06','node07']
CAPS={'E':128,'D':16,'C':8192}
ANALYSIS_SEED=1120260928
