"""Stage11C-R identity; archived stages are read-only inputs."""
from pathlib import Path
from scripts.stage10c.common import load, save, sha, now

ROOT = Path('outputs/stage11cr/v1')
OLD = Path('outputs/stage11c/v1')
SEED = 1120260930
ARMS = ('thinking', 'instruct_direct')


def verify_frozen():
    cfg = load(ROOT/'config.json')
    for path, digest in cfg['frozen_scientific_inputs'].items():
        assert sha(path) == digest, path
    return cfg
