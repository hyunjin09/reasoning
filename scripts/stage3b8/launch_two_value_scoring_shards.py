#!/usr/bin/env python3
"""Launch one Stage 3B.8 Value-scoring shard on each allocated GPU."""

from __future__ import annotations

import argparse
import os
import runpy
import sys
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest-dir", type=Path, required=True)
    parser.add_argument("--manifest-prefix", required=True)
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--roi-mapping", type=Path, required=True)
    parser.add_argument("--output-prefix", required=True)
    parser.add_argument("--cohort-role", choices=("discovery", "primary"), required=True)
    parser.add_argument("--experiment", choices=("capture", "dose", "projected"), required=True)
    parser.add_argument("--projectors", type=Path)
    parser.add_argument("--arms", type=Path)
    parser.add_argument("--stage3b7r-reference-root", type=Path)
    parser.add_argument("--repeat-first", action="store_true")
    args = parser.parse_args()
    rank = int(os.environ["LOCAL_RANK"])
    world = int(os.environ["LOCAL_WORLD_SIZE"])
    if world != 2 or rank not in (0, 1) or torch.cuda.device_count() != 2:
        raise RuntimeError("Stage 3B.8 scoring requires exactly two allocation-visible GPUs")
    torch.cuda.set_device(rank)
    arguments = [
        str(ROOT / "scripts/stage3b8/run_value_scoring.py"),
        "--manifest", str(args.manifest_dir / f"{args.manifest_prefix}_{rank:02d}.jsonl"),
        "--annotations", str(args.annotations),
        "--roi-mapping", str(args.roi_mapping),
        "--config", str(ROOT / "outputs/stage3b8/config/stage3b8_config.json"),
        "--dataset-root", "/data/dataset/MathVerse",
        "--model-checkpoint", "/data/dataset/huggingface/hub/models--Qwen--Qwen3-VL-4B-Thinking/snapshots/1de27d8c51f12e819435303b9e84c4e25ba8401e",
        "--output-dir", str(ROOT / f"outputs/stage3b8/scoring/raw/{args.output_prefix}_{rank:02d}"),
        "--cohort-role", args.cohort_role,
        "--experiment", args.experiment,
        "--required-gpu-class", "A5000",
        "--resume",
    ]
    for flag, value in (
        ("--projectors", args.projectors),
        ("--arms", args.arms),
        ("--stage3b7r-reference-root", args.stage3b7r_reference_root),
    ):
        if value is not None:
            arguments.extend([flag, str(value)])
    if args.repeat_first:
        arguments.append("--repeat-first")
    sys.argv = arguments
    runpy.run_path(str(ROOT / "scripts/stage3b8/run_value_scoring.py"), run_name="__main__")


if __name__ == "__main__":
    main()
