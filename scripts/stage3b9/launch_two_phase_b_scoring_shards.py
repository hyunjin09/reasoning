#!/usr/bin/env python3
"""Launch Phase-B full or projected scoring on two allocated GPUs."""

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
    parser.add_argument("--mode", choices=("full", "projected"), required=True)
    parser.add_argument("--output-prefix", required=True)
    args = parser.parse_args()
    rank = int(os.environ["LOCAL_RANK"])
    if int(os.environ["LOCAL_WORLD_SIZE"]) != 2 or rank not in (0, 1) or torch.cuda.device_count() != 2:
        raise RuntimeError("Phase-B scoring requires exactly two allocation-visible GPUs")
    torch.cuda.set_device(rank)
    common = [
        "--manifest", str((args.manifest_dir / f"shard_{rank:02d}.jsonl").resolve()),
        "--annotations", str(ROOT / "outputs/stage3b9/evidence_audit/annotations.jsonl"),
        "--roi-mapping", str(ROOT / "outputs/stage3b9/roi_validation/roi_token_mapping_all_fresh.jsonl"),
        "--config", str(ROOT / "outputs/stage3b9/config/phase_a_scoring/runtime_config.json"),
        "--dataset-root", "/data/dataset/MathVerse",
        "--model-checkpoint", str(MODEL),
        "--output-dir", str(ROOT / f"outputs/stage3b9/phase_b_local/scoring/raw/{args.output_prefix}_{rank:02d}"),
        "--required-gpu-class", "A5000",
        "--resume",
    ]
    if args.mode == "full":
        script = ROOT / "scripts/stage3b9/run_phase_b_full_scoring.py"
    else:
        script = ROOT / "scripts/stage3b9/run_phase_b_projected_scoring.py"
        common.extend([
            "--applicability", str(ROOT / "outputs/stage3b9/phase_b_local/applicability_gate.jsonl"),
            "--projectors", str(ROOT / "outputs/stage3b9/phase_b_local/local_deltas/projectors.npz"),
            "--random-seeds", str(ROOT / "outputs/stage3b9/phase_b_local/local_deltas/random_local_seeds.json"),
        ])
    sys.argv = [str(script), *common]
    runpy.run_path(str(script), run_name="__main__")


if __name__ == "__main__":
    main()
