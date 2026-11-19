#!/usr/bin/env python3
"""Compare frozen residual rescue with prior semantic patch and retrieval phenotypes."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import spearmanr


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c6"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def correlation(left: list[float], right: list[float]) -> dict[str, Any]:
    result = spearmanr(left, right)
    rho = float(result.statistic)
    p_value = float(result.pvalue)
    return {"N": len(left), "rho": rho if np.isfinite(rho) else None, "p_value_two_sided": p_value if np.isfinite(p_value) else None}


def main() -> None:
    config = read_json(OUT / "config/stage3c6_config.json")
    bases = [str(value) for value in config["primary_base_problem_ids"]]
    boundary = read_json(OUT / "phase_b_boundary/boundary_statistics.json")
    per_problem = {str(row["base_problem_id"]): row for row in read_jsonl(OUT / "phase_b_boundary/per_problem_boundary_rescue.jsonl")}
    active = list(boundary["targets"])
    stage3c5_rows = read_jsonl(ROOT / "outputs/stage3c5/phase_b_handoff/hpre_results.jsonl")
    stage3c5 = {(str(row["base_problem_id"]), str(row["target_id"])): row for row in stage3c5_rows}
    comparison_rows = []
    comparison_stats: dict[str, Any] = {}
    for target in active:
        spec = boundary["targets"][target]["strongest_confirmed_boundary"]
        key = f"L{spec['layer']}_{spec['boundary']}"
        target_rows = []
        for base in bases:
            current = per_problem[base]["targets"][target]
            old = stage3c5[(base, target)]
            row = {
                "base_problem_id": base, "target_id": target,
                "stage3c5_semantic_hpre_BCR": float(old["BCR"]), "stage3c5_semantic_hpre_CRR": float(old["CRR"]),
                "stage3c6_boundary": key,
                "stage3c6_suppression_rescue_gain": float(current["sign_aligned"][key]["rescue_gain"]),
                "stage3c6_suppression_rescue_RR": float(current["sign_aligned"][key]["rescue_ratio"]),
            }
            comparison_rows.append(row)
            target_rows.append(row)
        comparison_stats[target] = {
            "stage3c5_median_CRR": float(np.median([row["stage3c5_semantic_hpre_CRR"] for row in target_rows])),
            "stage3c6_median_RR": float(np.median([row["stage3c6_suppression_rescue_RR"] for row in target_rows])),
            "CRR_vs_RR_spearman": correlation(
                [row["stage3c5_semantic_hpre_CRR"] for row in target_rows],
                [row["stage3c6_suppression_rescue_RR"] for row in target_rows],
            ),
        }
    write_json(OUT / "secondary/stage3c5_semantic_patch_comparison.json", {
        "primary_unit": "base_problem_id", "N_unique_bases": len(bases),
        "targets": comparison_stats, "rows": comparison_rows,
        "interpretation_boundary": "cross-image semantic transfer and within-condition suppression rescue answer different causal questions; neither ratio is a unique information fraction",
    })

    measurements: dict[tuple[str, str, int], dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for filename, name, extractor in (
        ("qk_results.jsonl", "qk", lambda row: float(row["qk_cosine"]["attention_weighted_mean"])),
        ("source_mass_results.jsonl", "attention", lambda row: float(row["attention_density"])),
        ("value_contribution_results.jsonl", "alphaV", lambda row: float(row["alpha_v_norm"])),
    ):
        for row in read_jsonl(ROOT / "outputs/stage3c2/measurements" / filename):
            base, target, offset = str(row["base_problem_id"]), str(row["target_id"]), int(row["offset_from_target"])
            if base in bases and target in active and row["condition"] == "O" and row["head_role"] == "causal" and row["source_group"] == "target_roi" and offset in {-1, 0}:
                measurements[(base, target, offset)][name].append(extractor(row))
    for row in read_jsonl(ROOT / "outputs/stage3c2/measurements/sink_results.jsonl"):
        base, target, offset = str(row["base_problem_id"]), str(row["target_id"]), int(row["offset_from_target"])
        if base in bases and target in active and row["condition"] == "O" and row["head_role"] == "causal" and offset in {-2, -1, 0}:
            measurements[(base, target, offset)]["sink"].append(float(row["primary_candidate"]["attention_mass"]))
    phenotype_rows = []
    for target in active:
        spec = boundary["targets"][target]["strongest_confirmed_boundary"]
        key = f"L{spec['layer']}_{spec['boundary']}"
        for base in bases:
            values = {}
            for offset, label in ((-1, "tpre"), (0, "tstar")):
                for name in ("qk", "attention", "alphaV"):
                    values[f"{name}_{label}"] = float(np.mean(measurements[(base, target, offset)][name]))
            values["sink_release_to_tpre"] = float(np.mean(measurements[(base, target, -2)]["sink"]) - np.mean(measurements[(base, target, -1)]["sink"]))
            values["sink_release_to_tstar"] = float(np.mean(measurements[(base, target, -1)]["sink"]) - np.mean(measurements[(base, target, 0)]["sink"]))
            current = per_problem[base]["targets"][target]
            phenotype_rows.append({
                "base_problem_id": base, "target_id": target, **values,
                "suppression_loss": float(current["sign_aligned_suppression_loss"]),
                "strongest_rescue_gain": float(current["sign_aligned"][key]["rescue_gain"]),
                "strongest_rescue_RR": float(current["sign_aligned"][key]["rescue_ratio"]),
            })
    descriptors = ("qk_tpre", "qk_tstar", "attention_tpre", "attention_tstar", "alphaV_tpre", "alphaV_tstar", "sink_release_to_tpre", "sink_release_to_tstar")
    correlations = {}
    for target in active:
        selected = [row for row in phenotype_rows if row["target_id"] == target]
        correlations[target] = {
            descriptor: {
                outcome: correlation([row[descriptor] for row in selected], [row[outcome] for row in selected])
                for outcome in ("suppression_loss", "strongest_rescue_gain", "strongest_rescue_RR")
            }
            for descriptor in descriptors
        }
    write_json(OUT / "secondary/retrieval_phenotype_overlap.json", {
        "primary_unit": "base_problem_id", "N_unique_bases": len(bases),
        "candidate_regions": {target: read_json(OUT / "phase_a_hpre_scan/candidate_region_freeze.json")["targets"][target]["candidate_region"] for target in active},
        "historical_retrieval_layers": {"target_a": 29, "target_b": 28},
        "correlations": correlations, "rows": phenotype_rows,
        "attention_is_descriptive_not_causal": True, "candidate_sink_not_intervened": True,
    })
    print(json.dumps({"stage3c5_comparison": comparison_stats, "phenotype_rows": len(phenotype_rows)}, indent=2))


if __name__ == "__main__":
    main()
