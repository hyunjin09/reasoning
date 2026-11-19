#!/usr/bin/env python3
"""Execute the finalized artifact-only Stage 2C pipeline on allocated A6000s."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "outputs/stage2c/summaries"


def run(arguments: list[str]) -> None:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT / "code")
    subprocess.run(arguments, cwd=ROOT, env=env, check=True)


def main() -> None:
    visible = torch.cuda.device_count()
    names = [torch.cuda.get_device_name(index) for index in range(visible)]
    if not torch.cuda.is_available() or visible != 2:
        raise RuntimeError(f"Stage 2C final run requires exactly two allocated GPUs; visible={visible}, names={names}")
    if any("A6000" not in name for name in names):
        raise RuntimeError(f"Stage 2C requires A6000 GPUs; visible names={names}")
    gpu_health_checks = []
    for index in range(visible):
        with torch.cuda.device(index):
            values = torch.arange(4096, device=f"cuda:{index}", dtype=torch.float32)
            checksum = float((values * 2 + 1).sum().cpu())
            torch.cuda.synchronize(index)
            gpu_health_checks.append({"visible_device_index": index, "name": names[index], "arithmetic_checksum": checksum, "status": "pass"})
    runtime = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "stage": "2C artifact-only temporal measurement audit",
        "hostname": os.uname().nodename,
        "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
        "slurm_job_name": os.environ.get("SLURM_JOB_NAME"),
        "allocated_gpu_count": visible,
        "gpu_names": names,
        "gpu_health_checks": gpu_health_checks,
        "torch_version": torch.__version__,
        "cuda_version": torch.version.cuda,
        "inference_performed": False,
        "model_loaded": False,
        "purpose_of_gpu_allocation": "honor requested A6000 execution environment while deriving statistics from retained Stage 1 arrays",
        "historical_stage1_stage2a_stage2b_outputs_modified": False,
    }
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "runtime_environment.json").write_text(json.dumps(runtime, indent=2) + "\n", encoding="utf-8")
    run([sys.executable, "-m", "unittest", "discover", "-s", "tests/stage2c", "-v"])
    run([sys.executable, "scripts/stage2c/prepare_stage2c.py"])
    run([sys.executable, "scripts/stage2c/analyze_stage2c.py"])
    run([sys.executable, "scripts/stage2c/validate_outputs.py"])
    print(json.dumps(runtime, indent=2))


if __name__ == "__main__":
    main()
