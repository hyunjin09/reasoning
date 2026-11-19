#!/usr/bin/env python3
"""Resume Stage 3C.8 shard 01 on local rank 1 of the live two-GPU allocation."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    local_rank = int(os.environ.get("SLURM_LOCALID", "0"))
    if local_rank == 0:
        print("local rank 0 reserved for the already-running shard 00; exiting", flush=True)
        return
    if local_rank != 1:
        raise RuntimeError(f"Expected local rank 0 or 1, observed {local_rank}")
    command = [
        sys.executable,
        str(ROOT / "scripts/stage3c8/run_prospective_generation.py"),
        "--manifest", str(ROOT / "outputs/stage3c8/cohort/generation_shard_01.jsonl"),
        "--dataset-root", "/data/dataset/MathVerse",
        "--model-checkpoint",
        "/data/dataset/huggingface/hub/models--Qwen--Qwen3-VL-4B-Thinking/"
        "snapshots/1de27d8c51f12e819435303b9e84c4e25ba8401e",
        "--output-dir", str(ROOT / "outputs/stage3c8/prospective_generation/raw/shard_01"),
        "--required-gpu-class", "A5000",
        "--resume",
    ]
    print("local rank 1 resuming prospective-generation shard 01 on CUDA device 1", flush=True)
    completed = subprocess.run(command, cwd=ROOT, env={**os.environ, "PYTHONPATH": "code:."})
    raise SystemExit(completed.returncode)


if __name__ == "__main__":
    main()
