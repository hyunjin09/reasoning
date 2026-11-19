from pathlib import Path
from scripts.qwen3vl_official_eval.common import load, save, sha, now

ROOT = Path('outputs/stage12ar/v1')
PREFIX = 'stage12ar_'
ALLOWED_NODES = ['node02', 'node03', 'node06', 'node07']
CAPS = {'D': 64, 'C0': 32768, 'C1': 32768}
