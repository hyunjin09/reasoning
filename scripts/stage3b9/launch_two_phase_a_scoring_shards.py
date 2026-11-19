#!/usr/bin/env python3
"""Launch one frozen Stage 3B.9 Phase-A scoring shard per allocated GPU."""

from __future__ import annotations

import argparse
import os
import runpy
import sys
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parents[2]
MODEL = Path("/data/dataset/huggingface/hub/models--Qwen--Qwen3-VL-4B-Thinking/snapshots/1de27d8c51f12e819435303b9e84c4e25ba8401e")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest-dir", type=Path, required=True)
    parser.add_argument("--output-prefix", required=True)
    parser.add_argument("--arms", type=Path, required=True)
    parser.add_argument("--annotations", type=Path, default=ROOT / "outputs/stage3b9/evidence_audit/annotations.jsonl")
    parser.add_argument("--roi-mapping", type=Path, default=ROOT / "outputs/stage3b9/config/phase_a_scoring/phase_a_roi_mapping_all_fresh.jsonl")
    args = parser.parse_args()
    rank = int(os.environ["LOCAL_RANK"])
    if int(os.environ["LOCAL_WORLD_SIZE"]) != 2 or rank not in (0, 1) or torch.cuda.device_count() != 2:
        raise RuntimeError("Phase-A scoring requires exactly two allocation-visible GPUs")
    torch.cuda.set_device(rank)
    assets = ROOT / "outputs/stage3b9/config/phase_a_scoring"
    sys.argv = [
        str(ROOT / "scripts/stage3b9/run_phase_a_scoring.py"),
        "--manifest", str((args.manifest_dir / f"shard_{rank:02d}.jsonl").resolve()),
        "--annotations", str(args.annotations.resolve()),
        "--roi-mapping", str(args.roi_mapping.resolve()),
        "--config", str(assets / "runtime_config.json"),
        "--dataset-root", "/data/dataset/MathVerse",
        "--model-checkpoint", str(MODEL),
        "--output-dir", str(ROOT / f"outputs/stage3b9/scoring/raw/{args.output_prefix}_{rank:02d}"),
        "--cohort-role", "discovery",
        "--experiment", "projected",
        "--projectors", str(assets / "projectors.npz"),
        "--arms", str(args.arms.resolve()),
        "--required-gpu-class", "A5000",
        "--resume",
    ]
    runpy.run_path(str(ROOT / "scripts/stage3b9/run_phase_a_scoring.py"), run_name="__main__")


if __name__ == "__main__":
    main()
