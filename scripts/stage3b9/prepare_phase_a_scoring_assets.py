#!/usr/bin/env python3
"""Materialize immutable compatibility inputs and Phase-A scoring arms."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b9"
RANKS = (1, 2, 4, 8, 16, 24, 32, 48)
TARGETS = ("target_a", "target_b_r")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    target_dir = OUT / "config/phase_a_scoring"
    if target_dir.exists() and any(target_dir.iterdir()):
        raise FileExistsError(f"Phase-A scoring inputs already exist: {target_dir}")
    ensure_directory(target_dir)
    stage_config = read_json(OUT / "config/stage3b9_config.json")
    targets = read_json(OUT / "config/frozen_targets.json")["targets"]
    runtime_config = {
        "locked_generation_protocol": stage_config["locked_generation_protocol"],
        "architecture_expected": {
            "language_layers": 36,
            "logical_query_heads": 32,
            "kv_heads": 8,
            "query_heads_per_kv_group": 4,
            "head_dimension": 128,
        },
        "targets": targets,
        "dose_response": {"lambdas": [1.0]},
        "representation": read_json(OUT / "config/frozen_targets.json")["representation"],
    }
    write_json(target_dir / "runtime_config.json", runtime_config)

    basis_dir = OUT / "phase_a_shared/basis"
    arrays: dict[str, np.ndarray] = {}
    for target in TARGETS:
        source = basis_dir / f"{target}_rank_bases.npz"
        with np.load(source) as values:
            for rank in RANKS:
                arrays[f"{target}__learned_rank_{rank}"] = np.asarray(values[f"rank_{rank}"], dtype=np.float64)
    with np.load(basis_dir / "sham_bases.npz") as values:
        for target in TARGETS:
            for rank in RANKS:
                arrays[f"{target}__sham_rank_{rank}"] = np.asarray(values[f"{target}__rank_{rank}"], dtype=np.float64)
    with np.load(basis_dir / "random_bases.npz") as values:
        for key in values.files:
            arrays[key] = np.asarray(values[key], dtype=np.float64)
    projector_path = target_dir / "projectors.npz"
    np.savez_compressed(projector_path, **arrays)

    write_json(target_dir / "full_v_arms.json", {"frozen_before_fresh_scoring": True, "arms": [{"arm_id": "full_V", "dose": 1.0}]})
    learned_arms = []
    for rank in RANKS:
        learned_arms.extend([
            {"arm_id": f"learned_rank_{rank}", "dose": 1.0, "basis_key": f"{{target_id}}__learned_rank_{rank}", "component": "parallel"},
            {"arm_id": f"complement_rank_{rank}", "dose": 1.0, "basis_key": f"{{target_id}}__learned_rank_{rank}", "component": "complement"},
            {"arm_id": f"sham_rank_{rank}", "dose": 1.0, "basis_key": f"{{target_id}}__sham_rank_{rank}", "component": "parallel"},
        ])
    write_json(target_dir / "learned_control_arms.json", {"frozen_before_fresh_scoring": True, "ranks": list(RANKS), "arms": learned_arms})
    random_arms = []
    for target in TARGETS:
        for random_index in range(100):
            for rank in RANKS:
                random_arms.append({
                    "arm_id": f"random_{random_index:03d}_rank_{rank}",
                    "dose": 1.0,
                    "basis_key": f"{target}__random_{random_index:03d}__rank_{rank}",
                    "component": "parallel",
                    "target_ids": [target],
                })
    write_json(target_dir / "random_arms.json", {"frozen_before_fresh_scoring": True, "random_subspaces_per_target_rank": 100, "ranks": list(RANKS), "arms": random_arms})

    rois = read_jsonl(OUT / "roi_validation/roi_token_mapping.jsonl")
    phase_a_rois = []
    for row in rois:
        if row["phase"] != "phase_a":
            continue
        row["four_condition_layout_exact"] = bool(row["all_condition_layout_exact"])
        phase_a_rois.append(row)
    write_jsonl(target_dir / "phase_a_roi_mapping.jsonl", phase_a_rois)
    write_json(
        target_dir / "freeze.json",
        {
            "frozen_at": datetime.now(timezone.utc).isoformat(),
            "fresh_scoring_existed": False,
            "phase_a_roi_count": len(phase_a_rois),
            "ranks": list(RANKS),
            "random_subspaces_per_target_rank": 100,
            "basis_array_count": len(arrays),
            "projector_sha256": sha256(projector_path),
            "source_hashes": {
                path.name: sha256(path)
                for path in sorted(basis_dir.glob("*.npz"))
            },
            "applicability_rule": "A target/base is usable iff full-V BVR is finite, strictly positive, bidirectionally source-consistent, all intervention scores are finite, and all v3 mechanical controls pass.",
            "attention_used": False,
            "fresh_value_vectors_or_causal_scores_used": False,
        },
    )
    print(json.dumps({"basis_arrays": len(arrays), "phase_a_rois": len(phase_a_rois), "random_arms": len(random_arms)}, indent=2))


if __name__ == "__main__":
    main()
