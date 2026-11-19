#!/usr/bin/env python3
"""Bounded Slurm CUDA-visibility diagnostic; performs no model inference."""

from __future__ import annotations

import json
import os
import socket
import subprocess
from pathlib import Path

import torch


def main() -> None:
    output = Path("outputs/stage3a/scoring/node03_cuda_diagnostic.json")
    smi = subprocess.run(
        ["nvidia-smi", "-L"],
        check=False,
        capture_output=True,
        text=True,
    )
    record = {
        "hostname": socket.gethostname(),
        "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
        "slurm_job_gpus": os.environ.get("SLURM_JOB_GPUS"),
        "nvidia_smi_exit_code": smi.returncode,
        "nvidia_smi_stdout": smi.stdout.strip(),
        "nvidia_smi_stderr": smi.stderr.strip(),
        "torch_version": torch.__version__,
        "torch_cuda_version": torch.version.cuda,
        "torch_cuda_is_available": torch.cuda.is_available(),
        "torch_cuda_device_count": torch.cuda.device_count(),
    }
    try:
        record["torch_device_name"] = torch.cuda.get_device_name(0)
        tensor = torch.ones(1, device="cuda")
        record["torch_tensor_value"] = tensor.item()
        record["torch_cuda_initialization"] = "pass"
    except Exception as error:  # diagnostic must preserve the exact failure
        record["torch_cuda_initialization"] = "fail"
        record["torch_cuda_error"] = repr(error)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=2), flush=True)


if __name__ == "__main__":
    main()
