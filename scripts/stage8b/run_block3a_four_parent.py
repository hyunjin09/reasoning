"""Each Slurm task owns one GPU; children inherit its device binding unchanged."""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', required=True)
    ap.add_argument('--phase', choices=['census'], required=True)
    args = ap.parse_args()
    cfg = json.loads(Path(args.config).read_text())
    assert os.environ.get('SLURM_NTASKS') == '4' and os.environ.get('SLURM_PROCID') in ('0', '1', '2', '3')
    per_gpu = cfg['workers_per_gpu'];assert per_gpu==2
    workers = []; streams = []
    try:
        for lane in range(per_gpu):
            rank = int(os.environ['SLURM_PROCID'])*per_gpu+lane
            log = Path(cfg['log_dir'])/f'{args.phase}_{rank}.log'
            log.parent.mkdir(parents=True, exist_ok=True)
            stream = log.open('x'); streams.append(stream)
            script = 'run_block3a_four_native.py'
            command = [sys.executable, f'scripts/stage8b/{script}', '--config', args.config,
                       '--lane', str(lane), '--workers-per-gpu', str(per_gpu)]
            if args.phase == 'census':
                command += ['--phase', 'census']
            workers.append(subprocess.Popen(command, stdout=stream, stderr=subprocess.STDOUT))
        while any(p.poll() is None for p in workers):
            if any(p.poll() not in (None, 0) for p in workers):
                raise RuntimeError('A child failed; stopping its sibling and Slurm step')
            time.sleep(.25)
        if any(p.returncode != 0 for p in workers):
            raise RuntimeError('A child failed')
    finally:
        for p in workers:
            if p.poll() is None:
                p.terminate()
        for p in workers:
            try:
                p.wait(timeout=10)
            except subprocess.TimeoutExpired:
                p.kill(); p.wait()
        for stream in streams:
            stream.close()


if __name__ == '__main__':
    main()
