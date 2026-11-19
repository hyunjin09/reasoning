#!/usr/bin/env python3
"""Descriptive state continuity and Stage 3C.2 retrieval-phenotype overlap."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import torch
from scipy.stats import spearmanr


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c5"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def tensor_path(root: Path, base: str, name: str) -> Path:
    matches = list(root.glob(f"shard_*/examples/{base}/{name}"))
    if len(matches) != 1:
        raise RuntimeError(f"Expected one tensor artifact for {base}/{name}, found {len(matches)}")
    return matches[0]


def relative_delta(left: torch.Tensor, right: torch.Tensor) -> dict[str, float]:
    left = left.double().flatten()
    right = right.double().flatten()
    delta = torch.linalg.vector_norm(left - right)
    norm = torch.linalg.vector_norm(left)
    cosine = torch.nn.functional.cosine_similarity(left[None, :], right[None, :]).item()
    return {
        "l2_delta": float(delta.item()),
        "relative_l2_delta": float((delta / norm).item()) if float(norm.item()) else 0.0,
        "cosine_similarity": float(cosine),
    }


def finite_spearman(left: list[float], right: list[float]) -> dict[str, Any]:
    result = spearmanr(left, right)
    return {"N": len(left), "rho": float(result.statistic), "p_value_two_sided": float(result.pvalue)}


def main() -> None:
    config = read_json(OUT / "config/stage3c5_config.json")
    bases = config["primary_base_problem_ids"]
    phase_a = {row["base_problem_id"]: row for row in read_jsonl(OUT / "phase_a_tpre_layer/per_problem_tpre_scope_results.jsonl")}
    phase_b = {row["base_problem_id"]: row for row in read_jsonl(OUT / "phase_b_handoff/per_problem_handoff.jsonl")}
    continuity_rows = []
    for base in bases:
        a_states = torch.load(tensor_path(OUT / "raw/phase_a", base, "state_readouts.pt"), weights_only=True)
        b_states = torch.load(tensor_path(OUT / "raw/phase_b", base, "hpre_states.pt"), weights_only=True)
        target_rows = {}
        for target_id in ("target_a", "target_b"):
            intervention = {}
            semantic = []
            sham = []
            for candidate in ("original_candidate", "counterfactual_candidate"):
                intervention[candidate] = {
                    boundary: relative_delta(
                        a_states[f"{target_id}.A0.{candidate}.{boundary}"],
                        a_states[f"{target_id}.P4.{candidate}.{boundary}"],
                    )
                    for boundary in ("h_pre", "h_post_attn")
                }
                semantic.append(relative_delta(
                    b_states[f"{target_id}.O.{candidate}"],
                    b_states[f"{target_id}.C.{candidate}"],
                ))
                sham.extend([
                    relative_delta(b_states[f"{target_id}.O.{candidate}"], b_states[f"{target_id}.O_sham.{candidate}"]),
                    relative_delta(b_states[f"{target_id}.C.{candidate}"], b_states[f"{target_id}.C_sham.{candidate}"]),
                ])
            target_rows[target_id] = {
                "P4_tpre_suppression_propagation_to_tstar": intervention,
                "semantic_O_C_hpre_relative_l2_mean": float(np.mean([row["relative_l2_delta"] for row in semantic])),
                "paired_sham_hpre_relative_l2_mean": float(np.mean([row["relative_l2_delta"] for row in sham])),
                "semantic_to_sham_hpre_state_ratio": float(np.mean([row["relative_l2_delta"] for row in semantic]) / np.mean([row["relative_l2_delta"] for row in sham])),
            }
        continuity_rows.append({
            "base_problem_id": base, "targets": target_rows,
            "P4_tpre_loss": float(phase_a[base]["base_aggregated_loss_by_scope"]["P4"]),
            "R_last1_BCR": float(phase_b[base]["carriers"]["R_last1"]["BCR"]),
            "Q_BCR": float(phase_b[base]["carriers"]["Q"]["BCR"]),
            "h_pre_BCR": float(phase_b[base]["carriers"]["h_pre"]["BCR"]),
        })
    continuity = {
        "primary_unit": "base_problem_id", "N_unique_bases": len(continuity_rows),
        "no_new_probe_fitted": True,
        "measure": "raw-state relative L2/cosine plus frozen evidence-preference patch effects",
        "median_P4_propagation_relative_l2": {
            boundary: float(np.median([
                np.mean([
                    row["targets"][target]["P4_tpre_suppression_propagation_to_tstar"][candidate][boundary]["relative_l2_delta"]
                    for target in ("target_a", "target_b") for candidate in ("original_candidate", "counterfactual_candidate")
                ]) for row in continuity_rows
            ]))
            for boundary in ("h_pre", "h_post_attn")
        },
        "median_semantic_O_C_hpre_relative_l2": float(np.median([
            np.mean([row["targets"][target]["semantic_O_C_hpre_relative_l2_mean"] for target in ("target_a", "target_b")])
            for row in continuity_rows
        ])),
        "median_paired_sham_hpre_relative_l2": float(np.median([
            np.mean([row["targets"][target]["paired_sham_hpre_relative_l2_mean"] for target in ("target_a", "target_b")])
            for row in continuity_rows
        ])),
        "rows": continuity_rows,
        "interpretation": "descriptive continuity only; residual differences are not a fitted evidence direction or unique carrier fraction",
    }
    write_json(OUT / "secondary/continuity_analysis.json", continuity)

    qk = read_jsonl(ROOT / "outputs/stage3c2/measurements/qk_results.jsonl")
    source = read_jsonl(ROOT / "outputs/stage3c2/measurements/source_mass_results.jsonl")
    value = read_jsonl(ROOT / "outputs/stage3c2/measurements/value_contribution_results.jsonl")
    sink = read_jsonl(ROOT / "outputs/stage3c2/measurements/sink_results.jsonl")
    base_set = set(bases)
    phenotype: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for row in qk:
        if str(row["base_problem_id"]) in base_set and row["condition"] == "O" and row["head_role"] == "causal" and int(row["offset_from_target"]) == -1 and row["source_group"] == "target_roi":
            phenotype[str(row["base_problem_id"])]["qk_T_tpre"].append(float(row["qk_cosine"]["attention_weighted_mean"]))
    for row in source:
        if str(row["base_problem_id"]) in base_set and row["condition"] == "O" and row["head_role"] == "causal" and int(row["offset_from_target"]) == -1 and row["source_group"] == "target_roi":
            phenotype[str(row["base_problem_id"])]["attention_T_tpre"].append(float(row["attention_density"]))
    for row in value:
        if str(row["base_problem_id"]) in base_set and row["condition"] == "O" and row["head_role"] == "causal" and int(row["offset_from_target"]) == -1 and row["source_group"] == "target_roi":
            phenotype[str(row["base_problem_id"])]["alphaV_T_tpre"].append(float(row["alpha_v_norm"]))
    sink_by_base_offset: dict[tuple[str, int], list[float]] = defaultdict(list)
    for row in sink:
        base = str(row["base_problem_id"])
        offset = int(row["offset_from_target"])
        if base in base_set and row["condition"] == "O" and row["head_role"] == "causal" and offset in {-2, -1}:
            sink_by_base_offset[(base, offset)].append(float(row["primary_candidate"]["attention_mass"]))
    phenotype_rows = []
    for base in bases:
        values = {key: float(np.mean(items)) for key, items in phenotype[base].items()}
        values["candidate_sink_release_tminus2_to_tpre"] = float(
            np.mean(sink_by_base_offset[(base, -2)]) - np.mean(sink_by_base_offset[(base, -1)])
        )
        values.update({
            "P4_tpre_loss": float(phase_a[base]["base_aggregated_loss_by_scope"]["P4"]),
            "R_last1_BCR": float(phase_b[base]["carriers"]["R_last1"]["BCR"]),
            "h_pre_BCR": float(phase_b[base]["carriers"]["h_pre"]["BCR"]),
        })
        phenotype_rows.append({"base_problem_id": base, **values})
    descriptors = ("qk_T_tpre", "attention_T_tpre", "alphaV_T_tpre", "candidate_sink_release_tminus2_to_tpre")
    outcomes = ("P4_tpre_loss", "R_last1_BCR", "h_pre_BCR")
    correlations = {
        descriptor: {
            outcome: finite_spearman([row[descriptor] for row in phenotype_rows], [row[outcome] for row in phenotype_rows])
            for outcome in outcomes
        }
        for descriptor in descriptors
    }
    overlap = {
        "primary_unit": "base_problem_id", "N_unique_bases": len(phenotype_rows),
        "selected_necessary_scope": "P4_layers_16_35",
        "historical_phenotype_layers": [28, 29],
        "historical_layers_contained_in_selected_scope": True,
        "measurements": "Stage 3C.2 O-condition causal-head means at t_pre; sink release is mass(t*-2)-mass(t_pre)",
        "correlations": correlations, "rows": phenotype_rows,
        "attention_is_descriptive_not_causal": True,
        "candidate_sink_not_intervened": True,
    }
    write_json(OUT / "secondary/retrieval_phenotype_overlap.json", overlap)
    print(json.dumps({
        "continuity_medians": continuity["median_P4_propagation_relative_l2"],
        "semantic_hpre": continuity["median_semantic_O_C_hpre_relative_l2"],
        "sham_hpre": continuity["median_paired_sham_hpre_relative_l2"],
        "correlations": correlations,
    }, indent=2))


if __name__ == "__main__":
    main()
