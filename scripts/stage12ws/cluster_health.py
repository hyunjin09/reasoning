"""One bounded CPU-only connectivity probe; never launches or retries science."""
import datetime
import json
import os
import socket
import subprocess
from pathlib import Path


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as out:
        json.dump(value, out, indent=2)


root = Path('outputs/stage12ws/v1/audit/cluster_health')
job = os.environ['SLURM_JOB_ID']
stamp = lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()
save(root/f'{job}_started.json', dict(at=stamp(), node=socket.gethostname(), gpus_requested=0))
rows = []
for node in ['node02', 'node03', 'node06', 'node07']:
    for port in [22, 6818]:
        try:
            with socket.create_connection((node, port), timeout=2):
                result = 'connected'
        except OSError as exc:
            result = repr(exc)
        rows.append(dict(node=node, port=port, result=result))
try:
    result = subprocess.run(['nvidia-smi', '--query-gpu=index,utilization.gpu,memory.used',
                             '--format=csv,noheader'], capture_output=True, text=True, timeout=8)
    gpu = dict(returncode=result.returncode, stdout=result.stdout, stderr=result.stderr)
except (OSError, subprocess.TimeoutExpired) as exc:
    gpu = dict(error=repr(exc))
save(root/f'{job}_complete.json', dict(at=stamp(), node=socket.gethostname(), connectivity=rows,
                                    gpu_read_only_status=gpu, inference_calls=0))
print('CPU-only health check complete', job, flush=True)
