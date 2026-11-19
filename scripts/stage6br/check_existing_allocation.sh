#!/usr/bin/env bash
# Read-only allocation/device status; no CUDA kernels or model loading.
set -eu
cd /data/projects/hyunjin/MLLM/reasoning_steps
test "${SLURM_JOB_ID:-}" = 111485
test "${SLURM_JOB_NODELIST:-}" = node06
test -n "${CUDA_VISIBLE_DEVICES:-}"
case "$CUDA_VISIBLE_DEVICES" in *,*) exit 2 ;; esac
mkdir -p runs/stage6br/allocation_preflight
.venv/bin/python - <<'PY' > runs/stage6br/allocation_preflight/environment.json
import json, os, socket
from datetime import datetime
from zoneinfo import ZoneInfo
print(json.dumps({'checked_at':datetime.now(ZoneInfo('Asia/Seoul')).isoformat(),
 'hostname':socket.gethostname(), 'environment':{k:os.environ.get(k) for k in
 ['SLURM_JOB_ID','SLURM_JOB_NODELIST','SLURM_CPUS_PER_TASK','CUDA_VISIBLE_DEVICES']},
 'gpu_computation':False},indent=2))
PY
nvidia-smi --id="$CUDA_VISIBLE_DEVICES" --query-gpu=index,uuid,name,memory.total,memory.used,utilization.gpu --format=csv > runs/stage6br/allocation_preflight/assigned_gpu.csv
cat runs/stage6br/allocation_preflight/assigned_gpu.csv
