#!/usr/bin/env python3
"""Aggregate Stage 3C.9 route interventions without path-fraction claims."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

from visual_reasoning.stage0.io import write_json, write_jsonl
from visual_reasoning.stage3c8.analysis import holm_adjust, inferential_summary, robust_positive
from visual_reasoning.stage3c9.analysis import aligned_preference, route_phenotype


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c9"
ARMS = ("direct", "prior_checkpoint", "short_history", "joint")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument("--role", choices=("validation", "primary"), required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    raw = [read_json(path) for path in sorted(args.raw_root.glob("**/examples/*/result.json"))]
    if args.role == "validation" and len(raw) != 3:
        raise RuntimeError(f"Validation route assay must contain 3 bases, observed {len(raw)}")
    if args.role == "primary":
        expected = {
            str(row["base_problem_id"])
            for row in read_jsonl(OUT / "phase_d_routes/route_pair_manifest.jsonl")
        }
        observed = {str(row["base_problem_id"]) for row in raw}
        if observed != expected:
            raise RuntimeError(f"Primary route result bases mismatch: {len(observed)}/{len(expected)}")
    rows = {arm: [] for arm in ARMS}
    classifications = []
    for result in raw:
        base = str(result["base_problem_id"])
        effects = {}
        for arm in ARMS:
            condition_deficits = {}
            for condition in ("O", "C"):
                condition_row = result["conditions"][condition]
                native = aligned_preference(float(condition_row["native"]["D"]), condition)
                perturbed = aligned_preference(float(condition_row[arm]["D"]), condition)
                condition_deficits[condition] = native - perturbed
            mean_deficit = float(np.mean(list(condition_deficits.values())))
            effects[arm] = mean_deficit
            rows[arm].append({
                "base_problem_id": base,
                "example_id": str(result["example_id"]),
                "event_a_id": int(result["event_a_id"]),
                "event_b_id": int(result["event_b_id"]),
                "condition_deficits": condition_deficits,
                "mean_deficit": mean_deficit,
                "checkpoint_b_state_divergence": {
                    condition: result["conditions"][condition]["checkpoint_b_state_divergence"][arm]
                    for condition in ("O", "C")
                },
                "selection_used_effect_size": False,
                "selection_used_attention": False,
            })
        phenotype = route_phenotype(
            direct_deficit=effects["direct"],
            short_history_deficit=effects["short_history"],
            joint_deficit=effects["joint"],
        )
        classifications.append({
            "base_problem_id": base,
            "event_a_id": int(result["event_a_id"]),
            "event_b_id": int(result["event_b_id"]),
            "effects": effects,
            "route_phenotype": phenotype,
            "prior_route_primary_arm": "fixed checkpoint-A-through-next-8 history",
            "single_checkpoint_A_arm_supporting": True,
            "path_fraction_interpretation": False,
        })
    stats = {}
    for arm in ARMS:
        stats[arm] = inferential_summary({row["base_problem_id"]: float(row["mean_deficit"]) for row in rows[arm]})
    adjusted = holm_adjust([stats[arm]["wilcoxon_p"] for arm in ARMS]) if raw else []
    for arm, p_value in zip(ARMS, adjusted):
        stats[arm]["holm_p"] = p_value
        stats[arm]["robust_positive"] = robust_positive(stats[arm])
    summary = {
        "cohort_role": args.role,
        "N_unique_bases": len(raw),
        "arm_statistics": stats,
        "route_phenotype_distribution": dict(Counter(row["route_phenotype"] for row in classifications)),
        "primary_statistical_unit": "base_problem_id",
        "algebraic_unique_path_fractions_reported": False,
    }
    if args.role == "primary":
        write_jsonl(OUT / "phase_d_routes/direct_route.jsonl", rows["direct"])
        write_jsonl(OUT / "phase_d_routes/prior_checkpoint_route.jsonl", rows["prior_checkpoint"])
        write_jsonl(OUT / "phase_d_routes/short_history_route.jsonl", rows["short_history"])
        write_jsonl(OUT / "phase_d_routes/joint_route.jsonl", rows["joint"])
        write_json(OUT / "phase_d_routes/route_classification.json", {"bases": classifications, "summary": summary})
        write_json(OUT / "analysis/route_analysis.json", summary)
    else:
        write_jsonl(OUT / "audit/validation_route_effects.jsonl", [row for arm in ARMS for row in rows[arm]])
        write_json(OUT / "audit/validation_route_classification.json", {"bases": classifications, "summary": summary})
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
