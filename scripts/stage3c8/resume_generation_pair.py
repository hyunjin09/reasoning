#!/usr/bin/env python3
"""Dispatch one Slurm task to its frozen Stage 3C8 generation shard."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CHECKPOINT = Path("/data/dataset/huggingface/hub/models--Qwen--Qwen3-VL-4B-Thinking/snapshots/1de27d8c51f12e819435303b9e84c4e25ba8401e")


def main() -> None:
    task = int(os.environ["SLURM_PROCID"])
    if task not in {0, 1}:
        raise RuntimeError(f"Expected Slurm task 0 or 1, observed {task}")
    shard = f"{task:02d}"
    command = [
        str(ROOT / ".venv/bin/python"),
        str(ROOT / "scripts/stage3c8/run_prospective_generation.py"),
        "--manifest", str(ROOT / f"outputs/stage3c8/cohort/generation_shard_{shard}.jsonl"),
        "--dataset-root", "/data/dataset/MathVerse",
        "--model-checkpoint", str(CHECKPOINT),
        "--output-dir", str(ROOT / f"outputs/stage3c8/prospective_generation/raw/shard_{shard}"),
        "--required-gpu-class", "A5000",
        "--resume",
    ]
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(ROOT / "code")
    subprocess.run(command, cwd=ROOT, env=environment, check=True)


if __name__ == "__main__":
    main()
