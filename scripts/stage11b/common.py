from pathlib import Path
from scripts.stage10c.common import load, save, sha, now

ROOT = Path('outputs/stage11b/v1')
SEED = 1120260929
ARMS = ('instruct_cot', 'thinking')
