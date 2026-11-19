#!/usr/bin/env python3
"""Run one Stage 3C.1 extraction shard per allocation-visible A5000."""

from __future__ import annotations

import argparse
import os
import runpy
import sys
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parents[2]
MODEL = Path(
    "/data/dataset/huggingface/hub/models--Qwen--Qwen3-VL-4B-Thinking/"
    "snapshots/1de27d8c51f12e819435303b9e84c4e25ba8401e"
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("smoke", "smoke_v3", "full"), required=True)
    args = parser.parse_args()
    rank = int(os.environ["LOCAL_RANK"])
    world = int(os.environ["LOCAL_WORLD_SIZE"])
    if world != 2 or rank not in (0, 1) or torch.cuda.device_count() != 2:
        raise RuntimeError("Stage 3C.1 requires exactly two allocation-visible GPUs")
    torch.cuda.set_device(rank)
    output_dir = (
        ROOT / f"outputs/stage3c1/{args.mode}/shard_{rank:02d}"
        if args.mode.startswith("smoke")
        else ROOT / f"outputs/stage3c1/extraction/shards/shard_{rank:02d}"
    )
    argv = [
        str(ROOT / "scripts/stage3c1/run_extraction.py"),
        "--config", str(ROOT / "outputs/stage3c1/config/stage3c1_config.json"),
        "--manifest", str(ROOT / "outputs/stage3b6/config/primary_manifest.jsonl"),
        "--annotations", str(ROOT / "outputs/stage3b2/annotations/discriminative_event_annotations.jsonl"),
        "--roi-mapping", str(ROOT / "outputs/stage3b7/roi_audit/roi_token_mapping.jsonl"),
        "--dataset-root", "/data/dataset/MathVerse",
        "--model-checkpoint", str(MODEL),
        "--output-dir", str(output_dir),
        "--shard-index", str(rank),
        "--shard-count", "2",
        "--resume",
    ]
    if args.mode.startswith("smoke"):
        argv.extend(["--max-bases", "1", "--baseline-audit", "--repeat-first"])
    sys.argv = argv
    runpy.run_path(str(ROOT / "scripts/stage3c1/run_extraction.py"), run_name="__main__")


if __name__ == "__main__":
    main()
