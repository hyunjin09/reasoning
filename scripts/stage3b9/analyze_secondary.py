#!/usr/bin/env python3
"""Run frozen post-primary Stage 3B.9 metadata and attention diagnostics."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import spearmanr

from visual_reasoning.stage0.data import load_mathverse_rows
from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b9"
TARGETS = ("target_a", "target_b_r")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def collect_results(prefix: str) -> dict[str, dict]:
    rows: dict[str, dict] = {}
    for path in sorted((OUT / "scoring/raw").glob(f"{prefix}_*/examples/*/result.json")):
        base = path.parent.name
        if base in rows:
            raise RuntimeError(f"Duplicate {prefix} result for base {base}")
        rows[base] = read_json(path)
    return rows


def latest_existing(primary: Path, fallback: Path) -> Path:
    """Use an expanded frozen asset when it exists, otherwise the original freeze."""
    return primary if primary.is_file() else fallback


def select_cohort_results(rows: dict[str, dict], bases: list[str]) -> dict[str, dict]:
    """Filter pre-gate full-V screening outputs to the frozen Phase-A cohort."""
    missing = set(bases) - set(rows)
    if missing:
        raise RuntimeError(f"Missing Phase-A full-V results for bases {sorted(missing, key=int)}")
    return {base: rows[base] for base in bases}


def target_row(result: dict, target_id: str) -> dict:
    return next(row for row in result["targets"] if row["target_id"] == target_id)


def selected_head_roi_attention(row: dict) -> tuple[float, float]:
    """Average target-ROI mass/density across frozen heads and O/C recipients."""
    mass, density = [], []
    for condition in ("O", "C"):
        audit = row["no_intervention"][condition]["capture_audits"]["original_candidate"]
        summary = audit["recipient_attention_summary"]
        for head in row["heads"]:
            mass.append(float(summary["V_target_mass_per_head"][int(head)]))
            density.append(float(summary["V_target_density_per_head"][int(head)]))
    return float(np.mean(mass)), float(np.mean(density))


def safe_spearman(left: list[float], right: list[float]) -> dict:
    if len(left) < 3 or len(set(left)) < 2 or len(set(right)) < 2:
        return {"n": len(left), "rho": None, "pvalue": None}
    result = spearmanr(left, right)
    return {"n": len(left), "rho": float(result.statistic), "pvalue": float(result.pvalue)}


def tokenization_class(annotation: dict) -> str:
    lengths = []
    for pair in annotation["candidate_pairs"]:
        lengths.extend(
            [len(pair["original_divergent_suffix_ids"]), len(pair["counterfactual_divergent_suffix_ids"])]
        )
    return "single-token divergent suffix" if lengths and max(lengths) == 1 else "multi-token divergent suffix"


def main() -> None:
    # This script is intentionally gated on frozen primary outputs.
    rank_stats_path = OUT / "phase_a_shared/analysis/rank_curve_statistics.json"
    shared_decision_path = OUT / "phase_a_shared/analysis/shared_geometry_decision.json"
    local_stats_path = OUT / "phase_b_local/analysis/local_rank_statistics.json"
    if not all(path.is_file() for path in (rank_stats_path, shared_decision_path, local_stats_path)):
        raise RuntimeError("Primary Phase-A and Phase-B analyses must be frozen before secondary diagnostics")

    rank_stats = read_json(rank_stats_path)
    shared_decision = read_json(shared_decision_path)
    annotation_path = latest_existing(
        OUT / "evidence_audit/annotations_v2.jsonl",
        OUT / "evidence_audit/annotations.jsonl",
    )
    roi_path = latest_existing(
        OUT / "roi_validation/roi_token_mapping_all_fresh_v2.jsonl",
        OUT / "roi_validation/roi_token_mapping_all_fresh.jsonl",
    )
    annotations = {str(row["base_problem_id"]): row for row in read_jsonl(annotation_path)}
    rois = {str(row["base_problem_id"]): row for row in read_jsonl(roi_path)}
    source_rows = {str(row["sample_index"]): row for row in load_mathverse_rows(Path("/data/dataset/MathVerse"))}
    cohort = [
        *read_jsonl(OUT / "phase_a_shared/fresh_confirmation_manifest.jsonl"),
        *read_jsonl(OUT / "phase_b_local/cohort_manifest.jsonl"),
    ]
    metadata_rows = []
    for item in cohort:
        base = str(item["base_problem_id"])
        source = source_rows[str(item["example_id"])]
        edit = read_json(ROOT / item["edit_metadata"])
        annotation = annotations[base]
        roi = rois[base]
        answer = str(source["answer"])
        metadata_rows.append(
            {
                "base_problem_id": base,
                "example_id": str(item["example_id"]),
                "phase": annotation["phase"],
                "mathverse_variant": str(source["problem_version"]),
                "question_type": str(source.get("question_type")),
                "answer_format": "multiple_choice" if answer.strip().upper() in set("ABCDE") else "free_response",
                "subject": source.get("metadata", {}).get("subject"),
                "subfield": source.get("metadata", {}).get("subfield"),
                "edit_version": str(edit["edit_version"]),
                "target": str(edit["target"]),
                "render_suffix": str(edit["render_suffix"]),
                "original_value": str(edit["original"]),
                "counterfactual_value_count": len(annotation["candidate_pairs"]),
                "candidate_tokenization_class": tokenization_class(annotation),
                "roi_visual_token_count": int(roi["target_token_count"]),
                "e0_start_token": int(annotation["e0_start_token"]),
                "ed_generated_index": int(annotation["candidate_pairs"][0]["ed_generated_index"]),
            }
        )
    ensure_directory(OUT / "phase_c_secondary")
    write_jsonl(OUT / "phase_c_secondary/metadata_manifest.jsonl", metadata_rows)

    metadata_by_base = {row["base_problem_id"]: row for row in metadata_rows}
    strata_payload: dict[str, dict] = {}
    for target_id in TARGETS:
        selected_rank = shared_decision["targets"][target_id]["k_shared"] or 48
        per_base = rank_stats[target_id][str(selected_rank)]["per_base"]
        strata = {}
        labels = sorted({metadata_by_base[row["base_problem_id"]]["candidate_tokenization_class"] for row in per_base})
        for label in labels:
            selected = [
                row
                for row in per_base
                if metadata_by_base[row["base_problem_id"]]["candidate_tokenization_class"] == label
            ]
            strata[label] = {
                "base_count": len(selected),
                "median_B_full": float(np.median([row["B_full"] for row in selected])),
                "median_B_parallel": float(np.median([row["B_parallel"] for row in selected])),
                "median_SR": float(np.median([row["SR"] for row in selected if row["SR"] is not None])),
                "median_CR": float(np.median([row["CR"] for row in selected if row["CR"] is not None])),
            }
        strata_payload[target_id] = {
            "reporting_rank": int(selected_rank),
            "reporting_rank_rule": "frozen k_shared when one passes; otherwise the prospectively frozen maximum rank 48",
            "candidate_tokenization_strata": strata,
        }
    write_json(
        OUT / "analysis/format_stratification.json",
        {
            "secondary_only": True,
            "cohort_or_rank_modified": False,
            "primary_distribution_note": "Fresh Stage 3B.9 candidates are free-response Vision-Dominant solid-geometry numeric-label problems; tokenization is the informative within-cohort format split.",
            "targets": strata_payload,
        },
    )

    phase_a_bases = [str(row["base_problem_id"]) for row in read_jsonl(OUT / "phase_a_shared/fresh_confirmation_manifest.jsonl")]
    full = select_cohort_results(collect_results("phase_a_full"), phase_a_bases)
    attention_rows, attention_stats = [], {}
    for target_id in TARGETS:
        selected_rank = shared_decision["targets"][target_id]["k_shared"] or 48
        per_base = {row["base_problem_id"]: row for row in rank_stats[target_id][str(selected_rank)]["per_base"]}
        for base, result in full.items():
            mass, density = selected_head_roi_attention(target_row(result, target_id))
            row = per_base[base]
            attention_rows.append(
                {
                    "base_problem_id": base,
                    "target_id": target_id,
                    "selected_head_target_roi_mass": mass,
                    "selected_head_target_roi_density": density,
                    "B_full": float(row["B_full"]),
                    "reporting_rank": int(selected_rank),
                    "B_parallel": float(row["B_parallel"]),
                    "SR": row["SR"],
                }
            )
        target_values = [row for row in attention_rows if row["target_id"] == target_id]
        sr_pairs = [
            (row["selected_head_target_roi_density"], float(row["SR"]))
            for row in target_values
            if row["SR"] is not None
        ]
        attention_stats[target_id] = {
            "attention_vs_full_BVR": safe_spearman(
                [row["selected_head_target_roi_density"] for row in target_values],
                [row["B_full"] for row in target_values],
            ),
            "attention_vs_shared_SR": safe_spearman(
                [left for left, _ in sr_pairs],
                [right for _, right in sr_pairs],
            ),
            "reporting_rank": int(selected_rank),
        }
    write_json(
        OUT / "analysis/attention_secondary.json",
        {
            "secondary_only": True,
            "attention_used_for_selection_or_rank_choice": False,
            "attention_definition": "mean target-ROI density over the frozen selected logical query heads and O/C recipient captures at E_d or E_d-1",
            "causal_interpretation_prohibited": True,
            "targets": attention_stats,
            "per_base": attention_rows,
        },
    )

    figures = OUT / "analysis/figures"
    ensure_directory(figures)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    for ax, target_id in zip(axes, TARGETS):
        labels = list(strata_payload[target_id]["candidate_tokenization_strata"])
        values = [strata_payload[target_id]["candidate_tokenization_strata"][label]["median_SR"] for label in labels]
        ax.bar(np.arange(len(labels)), values, color="#4c78a8")
        ax.axhline(0.8, color="black", linestyle="--", linewidth=1)
        ax.set_xticks(np.arange(len(labels)), [label.replace(" divergent suffix", "") for label in labels], rotation=15)
        ax.set(title=f"{target_id} (rank {strata_payload[target_id]['reporting_rank']})", ylabel="median shared SR")
    fig.suptitle("Secondary candidate-tokenization stratification")
    fig.tight_layout()
    fig.savefig(figures / "secondary_format_stratification.png", dpi=180)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    colors = {"target_a": "#1f77b4", "target_b_r": "#d62728"}
    for target_id in TARGETS:
        selected = [row for row in attention_rows if row["target_id"] == target_id]
        axes[0].scatter(
            [row["selected_head_target_roi_density"] for row in selected],
            [row["B_full"] for row in selected],
            label=target_id,
            alpha=0.75,
            color=colors[target_id],
        )
        axes[1].scatter(
            [row["selected_head_target_roi_density"] for row in selected],
            [row["SR"] for row in selected],
            label=target_id,
            alpha=0.75,
            color=colors[target_id],
        )
    axes[0].set(xlabel="target-ROI attention density", ylabel="full-V BVR", title="Attention vs full causal effect")
    axes[1].set(xlabel="target-ROI attention density", ylabel="shared recovery ratio", title="Attention vs shared geometry recovery")
    for ax in axes:
        ax.grid(alpha=0.2)
        ax.legend()
    fig.suptitle("Secondary descriptive attention comparison (not causal evidence)")
    fig.tight_layout()
    fig.savefig(figures / "secondary_attention_vs_geometry.png", dpi=180)
    plt.close(fig)

    print(json.dumps({"metadata_bases": len(metadata_rows), "attention_rows": len(attention_rows), "attention": attention_stats}, indent=2))


if __name__ == "__main__":
    main()
