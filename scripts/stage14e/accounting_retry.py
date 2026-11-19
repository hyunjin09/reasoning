"""Tolerate sacct propagation delay; never infer a free or uncharged allocation."""
import time
from scripts.stage14e.accounting import refresh as refresh_once


def refresh():
    delays = [1, 2, 4, 8, 10]
    for attempt in range(len(delays)+1):
        try:
            return refresh_once()
        except RuntimeError as exc:
            if str(exc) != 'Missing Slurm accounting' or attempt == len(delays):
                raise
            time.sleep(delays[attempt])
