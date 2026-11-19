from pathlib import Path
from scripts.stage14d1.common import load, rows, save, sha, now

P = Path("outputs/stage14d1_sava_pilot/v1")
OLD = Path("outputs/stage14d1_sava")
RECOVERY = Path("outputs/stage14d1_sava_recovery/v1")
PRIOR_GPU_SECONDS = 2709
CEILING_GPU_SECONDS = 57600
