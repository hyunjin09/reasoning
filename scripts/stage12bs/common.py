from pathlib import Path
from scripts.qwen3vl_official_eval.common import load, save, sha, now

ROOT = Path('outputs/stage12bs/v1')
PREFIX = 'stage12bs_'
ALLOWED_NODES = ['node02', 'node03', 'node06', 'node07']
CAPS = {'E': 256, 'N': 32768, 'O': 32768}
