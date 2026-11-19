#!/usr/bin/env python3
"""Launch the two frozen Stage 3B.9 expansion-generation shards."""

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
    world = int(os.environ["LOCAL_WORLD_SIZE"])
    if world != 2 or rank not in (0, 1) or torch.cuda.device_count() != 2:
        raise RuntimeError("Stage 3B.9 expansion generation requires exactly two allocation-visible GPUs")
    torch.cuda.set_device(rank)
    manifest = (
        ROOT / "outputs/stage3b9/config/generation_expansion_shards_v2/shard_00.jsonl"
        if rank == 0
        else ROOT / "outputs/stage3b9/config/generation_expansion_shards/shard_01.jsonl"
    )
    sys.argv = [
        str(ROOT / "scripts/stage3b9/run_prospective_generation.py"),
        "--manifest", str(manifest),
        "--dataset-root", "/data/dataset/MathVerse",
        "--model-checkpoint", str(MODEL),
        "--output-dir", str(ROOT / f"outputs/stage3b9/prospective_generation/raw/expansion_shard_{rank:02d}"),
        "--required-gpu-class", "A5000",
        "--resume",
    ]
    runpy.run_path(str(ROOT / "scripts/stage3b9/run_prospective_generation.py"), run_name="__main__")


if __name__ == "__main__":
    main()
