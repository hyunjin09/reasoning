#!/usr/bin/env python3
"""Freeze Phase-B applicability, leave-one-value-out bases, and random seeds."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl
from visual_reasoning.stage3b9.local_geometry import fit_leave_one_out_bases


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b9"
TARGETS = ("target_a", "target_b_r")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--full-shard", type=Path, action="append", required=True)
    args = parser.parse_args()
    target_dir = OUT / "phase_b_local/local_deltas"
    if target_dir.exists() and any(target_dir.iterdir()):
        raise FileExistsError(f"Frozen Phase-B local assets already exist: {target_dir}")
    ensure_directory(target_dir)
    manifest = read_jsonl(args.manifest)
    if len(manifest) < 12:
        raise RuntimeError("Phase-B requires at least 12 valid base problems")
    results, vector_paths = {}, {}
    for shard in args.full_shard:
        for result_path in sorted(shard.glob("examples/*/result.json")):
            base = result_path.parent.name
            if base in results:
                raise RuntimeError(f"Duplicate full-V result for base {base}")
            results[base] = read_json(result_path)
            vector_paths[base] = result_path.parent / "vectors.npz"
    expected = {str(row["base_problem_id"]) for row in manifest}
    if set(results) != expected:
        raise RuntimeError(f"Full-V result mismatch: missing={sorted(expected-set(results))}, extra={sorted(set(results)-expected)}")
    gates, arrays, random_rows = [], {}, []
    for base in sorted(expected, key=int):
        result = results[base]
        if not all(value for key, value in result["mechanical_controls"].items() if key.startswith("all_")):
            raise RuntimeError(f"v3 mechanics failed before Phase-B local fitting for base {base}")
        target_rows = {row["target_id"]: row for row in result["targets"]}
        with np.load(vector_paths[base]) as vectors:
            for target_index, target in enumerate(TARGETS):
                pairs = []
                for value_index, pair in enumerate(target_rows[target]["pairs"], start=1):
                    arm = pair["full_v_arm"]
                    usable = bool(
                        math.isfinite(float(arm["BVR"]))
                        and float(arm["BVR"]) > 0.0
                        and arm["bidirectionally_source_consistent"]
                        and arm["all_scores_finite"]
                        and arm["all_query_head_selectivity_valid"]
                        and arm["all_recipient_tensor_alignment_exact"]
                        and arm["all_self_restorations_exact"]
                    )
                    pairs.append({
                        "pair_id": pair["pair_id"],
                        "counterfactual_value": pair["counterfactual_value"],
                        "full_BVR": float(arm["BVR"]),
                        "BVR_O": float(arm["BVR_O"]),
                        "BVR_C": float(arm["BVR_C"]),
                        "bidirectionally_source_consistent": bool(arm["bidirectionally_source_consistent"]),
                        "usable": usable,
                    })
                eligible = sum(pair["usable"] for pair in pairs) >= 3
                gates.append({
                    "base_problem_id": base,
                    "target_id": target,
                    "usable_pair_count": sum(pair["usable"] for pair in pairs),
                    "eligible": eligible,
                    "pairs": pairs,
                    "rule": "finite positive full-V BVR with bidirectional source consistency and passing v3 mechanics; at least 3/4 pairs",
                    "local_rank_outcomes_inspected": False,
                })
                if not eligible:
                    continue
                deltas = np.stack([
                    np.asarray(vectors[f"{target}__value_{value_index}__semantic_delta"], dtype=np.float64)
                    for value_index in range(1, 5)
                ])
                fitted = fit_leave_one_out_bases(deltas)
                for held_index in range(4):
                    for rank in (1, 2, 3):
                        arrays[f"{base}__{target}__value_{held_index + 1}__local_rank_{rank}"] = fitted[held_index][rank]
                    for random_index in range(100):
                        random_rows.append({
                            "base_problem_id": base,
                            "target_id": target,
                            "pair_id": f"value_{held_index + 1}",
                            "random_index": random_index,
                            "seed": 93_900_000 + int(base) * 10_000 + target_index * 5_000 + held_index * 1_000 + random_index,
                        })
    for target in TARGETS:
        with np.load(OUT / f"phase_a_shared/basis/{target}_rank_bases.npz") as values:
            arrays[f"{target}__global_rank_1"] = np.asarray(values["rank_1"][:, :1], dtype=np.float64)
            arrays[f"{target}__global_rank_2"] = np.asarray(values["rank_2"][:, :2], dtype=np.float64)
            arrays[f"{target}__global_rank_3"] = np.asarray(values["rank_4"][:, :3], dtype=np.float64)
    projector_path = target_dir / "projectors.npz"
    np.savez_compressed(projector_path, **arrays)
    write_jsonl(OUT / "phase_b_local/applicability_gate.jsonl", gates)
    write_json(OUT / "phase_b_local/applicability_gate.json", {
        "rule_frozen_before_local_rank_scoring": True,
        "base_problem_count": len(expected),
        "eligible_base_target_counts": {target: sum(row["target_id"] == target and row["eligible"] for row in gates) for target in TARGETS},
        "rows_file": "outputs/stage3b9/phase_b_local/applicability_gate.jsonl",
    })
    write_json(target_dir / "random_local_seeds.json", {
        "construction": "deterministic nested Gaussian QR rank family at ranks 1--3",
        "ambient_dimension": 512,
        "random_controls_per_base_target_pair": 100,
        "rows": random_rows,
    })
    write_json(target_dir / "freeze.json", {
        "frozen_at": datetime.now(timezone.utc).isoformat(),
        "full_v_results_inspected_only_for_prospective_applicability_gate": True,
        "local_projection_results_existed": False,
        "projector_file": str(projector_path.relative_to(ROOT)),
        "projector_sha256": sha256(projector_path),
        "projector_array_count": len(arrays),
        "random_seed_count": len(random_rows),
        "local_fit": "uncentered SVD on the three non-held-out semantic deltas within each base/target",
        "attention_used": False,
    })
    print(json.dumps({
        "bases": len(expected),
        "eligible_base_target_counts": {target: sum(row["target_id"] == target and row["eligible"] for row in gates) for target in TARGETS},
        "projector_arrays": len(arrays),
        "random_seed_rows": len(random_rows),
    }, indent=2))


if __name__ == "__main__":
    main()
