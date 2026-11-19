#!/usr/bin/env python3
"""Lightweight Phase 0 CUDA/PyTorch environment check."""

from __future__ import annotations

import argparse
import json
import platform
import socket
import subprocess
from pathlib import Path


def run_command(command: list[str]) -> dict[str, object]:
    try:
        result = subprocess.run(command, text=True, capture_output=True, timeout=30)
    except Exception as exc:  # pragma: no cover - diagnostic script
        return {
            "command": command,
            "returncode": None,
            "stdout": "",
            "stderr": str(exc),
        }
    return {
        "command": command,
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    import torch

    report = {
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "nvidia_smi": run_command(["nvidia-smi"]),
        "torch": {
            "version": torch.__version__,
            "cuda_available": torch.cuda.is_available(),
            "torch_cuda": torch.version.cuda,
            "device_count": torch.cuda.device_count(),
            "device_names": [
                torch.cuda.get_device_name(index)
                for index in range(torch.cuda.device_count())
            ],
        },
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

