#!/usr/bin/env python3
"""Launch one Stage 3B.6 shard per Slurm-assigned local GPU via torchrun."""

from __future__ import annotations

import argparse
import os
import runpy
import sys
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parents[2]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("discovery", "primary", "upstream", "source"), required=True)
    parser.add_argument("--manifest-dir", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--candidate-freeze", type=Path)
    parser.add_argument("--source-targets", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    local_rank = int(os.environ["LOCAL_RANK"])
    world_size = int(os.environ["LOCAL_WORLD_SIZE"])
    if world_size != 2 or local_rank not in (0, 1):
        raise RuntimeError("Stage 3B.6 tmux allocation requires exactly two local ranks")
    if torch.cuda.device_count() != 2:
        raise RuntimeError(
            f"Expected two Slurm-visible GPUs, observed {torch.cuda.device_count()}"
        )
    torch.cuda.set_device(local_rank)
    manifest = args.manifest_dir / f"{args.phase}_{local_rank:02d}.jsonl"
    output = args.output_root / f"{args.phase}_{local_rank:02d}"
    argv = [
        str(ROOT / "scripts/stage3b6/run_head_path_scoring.py"),
        "--manifest", str(manifest),
        "--annotations", str(ROOT / "outputs/stage3b2/annotations/discriminative_event_annotations.jsonl"),
        "--config", str(ROOT / "outputs/stage3b6/config/stage3b6_config.json"),
        "--dataset-root", "/data/dataset/MathVerse",
        "--model-checkpoint", "/data/dataset/huggingface/hub/models--Qwen--Qwen3-VL-4B-Thinking/snapshots/1de27d8c51f12e819435303b9e84c4e25ba8401e",
        "--stage3b5-raw-root", str(ROOT / "outputs/stage3b5"),
        "--output-dir", str(output),
        "--phase", args.phase,
        "--required-gpu-class", "A5000",
    ]
    if args.candidate_freeze:
        argv.extend(["--candidate-freeze", str(args.candidate_freeze)])
    if args.source_targets:
        argv.extend(["--source-targets", str(args.source_targets)])
    sys.argv = argv
    runpy.run_path(str(ROOT / "scripts/stage3b6/run_head_path_scoring.py"), run_name="__main__")


if __name__ == "__main__":
    main()
