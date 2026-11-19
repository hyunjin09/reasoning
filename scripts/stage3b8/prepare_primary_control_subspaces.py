#!/usr/bin/env python3
"""Freeze random, sham, and cross-target Stage 3B.8 projector controls."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from visual_reasoning.stage0.io import write_json
from visual_reasoning.stage3b8.geometry import random_orthonormal_basis


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b8"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    selected_path = OUT / "subspace/frozen_subspace_definition.npz"
    arm_path = OUT / "config/primary_projected_arms.json"
    if not selected_path.is_file() or not arm_path.is_file():
        raise RuntimeError("Discovery-only rank selection must be frozen first")
    config = read_json(OUT / "config/stage3b8_config.json")
    arms = read_json(arm_path)
    selected_ranks = {str(key): int(value) for key, value in arms["selected_ranks"].items()}
    target_ids = [str(row["target_id"]) for row in config["targets"]]
    if set(selected_ranks) != set(target_ids):
        raise RuntimeError("Frozen selected ranks do not cover the exact target family")
    dimension = int(config["representation"]["dimension"])
    count = int(config["subspace"]["random_subspaces"])
    seed = int(config["subspace"]["random_seed"])
    random_arrays: dict[str, np.ndarray] = {}
    random_arms = []
    for target_offset, target_id in enumerate(target_ids):
        rank = selected_ranks[target_id]
        for index in range(count):
            key = f"{target_id}__random_{index:03d}"
            basis = random_orthonormal_basis(
                dimension=dimension,
                rank=rank,
                seed=seed + target_offset * 100_000 + index,
            ).numpy()
            random_arrays[key] = basis
            random_arms.append({
                "arm_id": f"random_{index:03d}",
                "dose": 1.0,
                "basis_key": "{target_id}__random_" + f"{index:03d}",
                "component": "parallel",
                "target_ids": [target_id],
            })
    np.savez_compressed(OUT / "subspace/random_subspace_definitions.npz", **random_arrays)
    write_json(OUT / "config/random_subspace_arms.json", {
        "frozen_after_discovery_rank_selection": True,
        "primary_results_existed_at_control_freeze": True,
        "primary_results_were_inspected_before_control_freeze": True,
        "primary_results_used_for_control_construction": False,
        "construction_was_fully_prespecified": "100 Haar-random same-rank subspaces per target with frozen seed 1234",
        "random_seed": seed,
        "random_subspaces_per_target": count,
        "selected_ranks": selected_ranks,
        "arms": random_arms,
    })

    learned = dict(np.load(selected_path))
    cross_arrays = {
        "target_a__cross": learned["target_b_r__learned"],
        "target_b_r__cross": learned["target_a__learned"],
    }
    # Cross-target projection is mathematically defined only when ranks agree.
    # Differing ranks are allowed, and the receiving target records donor rank.
    np.savez_compressed(OUT / "subspace/cross_target_subspace_definitions.npz", **cross_arrays)
    write_json(OUT / "config/cross_target_arms.json", {
        "frozen_after_both_discovery_target_results": True,
        "primary_results_existed_at_control_freeze": True,
        "primary_results_were_inspected_before_control_freeze": True,
        "primary_results_used_for_control_construction": False,
        "construction_was_fully_prespecified": "swap the two discovery-learned rank-8 bases by ordinal frozen-head coordinate",
        "arms": [{
            "arm_id": "cross_target_parallel",
            "dose": 1.0,
            "basis_key": "{target_id}__cross",
            "component": "parallel",
        }],
        "source_target_by_recipient_target": {
            "target_a": "target_b_r",
            "target_b_r": "target_a",
        },
    })
    print(json.dumps({
        "random_array_count": len(random_arrays),
        "random_arms": len(random_arms),
        "cross_targets": target_ids,
    }, indent=2))


if __name__ == "__main__":
    main()
