#!/usr/bin/env python3
"""Launch one frozen Stage 3B.7-R scoring shard on each tmux-8 GPU."""

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
    parser.add_argument("--manifest-dir", type=Path, required=True)
    parser.add_argument("--manifest-prefix", required=True)
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--roi-mapping", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--output-prefix", required=True)
    parser.add_argument("--cohort-role", choices=("fresh_validation", "primary"), required=True)
    parser.add_argument("--phase", choices=("phase_a", "phase_b"), required=True)
    parser.add_argument("--targets", type=Path)
    parser.add_argument("--stage3b5-raw-root", type=Path)
    parser.add_argument("--repeat-first", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rank = int(os.environ["LOCAL_RANK"])
    world = int(os.environ["LOCAL_WORLD_SIZE"])
    if world != 2 or rank not in (0, 1):
        raise RuntimeError("Stage 3B.7-R tmux allocation requires exactly two local ranks")
    if torch.cuda.device_count() != 2:
        raise RuntimeError(f"Expected two allocation-visible GPUs, observed {torch.cuda.device_count()}")
    torch.cuda.set_device(rank)
    argv = [
        str(ROOT / "scripts/stage3b7r/run_roi_kv_scoring.py"),
        "--manifest", str(args.manifest_dir / f"{args.manifest_prefix}_{rank:02d}.jsonl"),
        "--annotations", str(args.annotations),
        "--roi-mapping", str(args.roi_mapping),
        "--config", str(ROOT / "outputs/stage3b7r/config/stage3b7r_config.json"),
        "--dataset-root", "/data/dataset/MathVerse",
        "--model-checkpoint", "/data/dataset/huggingface/hub/models--Qwen--Qwen3-VL-4B-Thinking/snapshots/1de27d8c51f12e819435303b9e84c4e25ba8401e",
        "--output-dir", str(args.output_root / f"{args.output_prefix}_{rank:02d}"),
        "--cohort-role", args.cohort_role,
        "--phase", args.phase,
        "--required-gpu-class", "A5000",
        "--resume",
    ]
    if args.targets:
        argv.extend(["--targets", str(args.targets)])
    if args.stage3b5_raw_root:
        argv.extend(["--stage3b5-raw-root", str(args.stage3b5_raw_root)])
    if args.repeat_first:
        argv.append("--repeat-first")
    sys.argv = argv
    runpy.run_path(str(ROOT / "scripts/stage3b7r/run_roi_kv_scoring.py"), run_name="__main__")


if __name__ == "__main__":
    main()
