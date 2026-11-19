#!/usr/bin/env python3
"""Launch one frozen applicability-expansion generation shard per A5000."""

from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parents[2]
MODEL = Path("/data/dataset/huggingface/hub/models--Qwen--Qwen3-VL-4B-Thinking/snapshots/1de27d8c51f12e819435303b9e84c4e25ba8401e")


def main() -> None:
    rank = int(os.environ["LOCAL_RANK"])
    if int(os.environ["LOCAL_WORLD_SIZE"]) != 2 or rank not in (0, 1) or torch.cuda.device_count() != 2:
        raise RuntimeError("Applicability-expansion generation requires exactly two allocation-visible GPUs")
    torch.cuda.set_device(rank)
    sys.argv = [
        str(ROOT / "scripts/stage3b9/run_prospective_generation.py"),
        "--manifest", str(ROOT / f"outputs/stage3b9/config/generation_applicability_expansion_shards/shard_{rank:02d}.jsonl"),
        "--dataset-root", "/data/dataset/MathVerse", "--model-checkpoint", str(MODEL),
        "--output-dir", str(ROOT / f"outputs/stage3b9/prospective_generation/raw/applicability_expansion_{rank:02d}"),
        "--required-gpu-class", "A5000", "--resume",
    ]
    runpy.run_path(str(ROOT / "scripts/stage3b9/run_prospective_generation.py"), run_name="__main__")


if __name__ == "__main__":
    main()
