from pathlib import Path
from scripts.qwen3vl_official_eval.common import load, save, sha, now

ROOT = Path('outputs/stage12b/v1')
PREFIX = 'stage12b_'
ALLOWED_NODES = ['node02', 'node03', 'node06', 'node07']
CAPS = {'E': 256, 'N': 32768, 'O': 32768}
