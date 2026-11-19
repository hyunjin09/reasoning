from pathlib import Path
from scripts.stage10c.common import load, save, sha, now

ROOT = Path('outputs/stage11a/v1')
OLD = Path('outputs/stage9a/v1')
SEED = 1120260928
ARMS = ('instruct_direct', 'instruct_cot', 'thinking')
