#!/usr/bin/env python3
"""Launch one Stage 3B.7R generation shard on each tmux-8 GPU."""

from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    rank = int(os.environ["LOCAL_RANK"])
    world = int(os.environ["LOCAL_WORLD_SIZE"])
    if world != 2 or rank not in (0, 1):
        raise RuntimeError("Stage 3B.7R tmux allocation requires exactly two local ranks")
    if torch.cuda.device_count() != 2:
        raise RuntimeError(f"Expected two allocation-visible GPUs, observed {torch.cuda.device_count()}")
    torch.cuda.set_device(rank)
    sys.argv = [
        str(ROOT / "scripts/stage3b7r/run_prospective_generation.py"),
        "--manifest", str(ROOT / f"outputs/stage3b7r/validation_cohort/generation_shards/shard_{rank:02d}.jsonl"),
        "--dataset-root", "/data/dataset/MathVerse",
        "--model-checkpoint", "/data/dataset/huggingface/hub/models--Qwen--Qwen3-VL-4B-Thinking/snapshots/1de27d8c51f12e819435303b9e84c4e25ba8401e",
        "--output-dir", str(ROOT / f"outputs/stage3b7r/validation_cohort/generation_raw/shard_{rank:02d}"),
        "--resume",
    ]
    runpy.run_path(str(ROOT / "scripts/stage3b7r/run_prospective_generation.py"), run_name="__main__")


if __name__ == "__main__":
    main()
