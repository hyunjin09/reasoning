#!/usr/bin/env python3
"""Create the complete frozen Stage 3C.8 figure set from analyzed artifacts."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c8"
FIG = OUT / "analysis/figures"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def finish(path: str, title: str, ylabel: str = "Directional gain") -> None:
    plt.title(title)
    plt.ylabel(ylabel)
    plt.tight_layout()
    plt.savefig(FIG / path, dpi=180)
    plt.close()


def grouped_medians(rows: Iterable[dict[str, Any]], field: str, value: str) -> tuple[list[str], list[float]]:
    groups: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        if row.get(value) is not None:
            groups[str(row[field])].append(float(row[value]))
    names = sorted(groups)
    return names, [float(np.median(groups[name])) for name in names]


def bar(path: str, title: str, names: list[str], values: list[float], ylabel: str = "Median directional gain") -> None:
    plt.figure(figsize=(max(6, 0.6 * max(1, len(names))), 4))
    plt.bar(range(len(names)), values, color="#4472c4")
    plt.axhline(0, color="black", linewidth=0.8)
    plt.xticks(range(len(names)), names, rotation=40, ha="right")
    finish(path, title, ylabel)


def placeholder(path: str, title: str, reason: str) -> None:
    plt.figure(figsize=(7, 3.5))
    plt.axis("off")
    plt.text(0.5, 0.58, title, ha="center", va="center", fontsize=14, weight="bold")
    plt.text(0.5, 0.38, reason, ha="center", va="center", wrap=True)
    plt.tight_layout()
    plt.savefig(FIG / path, dpi=180)
    plt.close()


def main() -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    a = read_jsonl(OUT / "phase_a_tpre/per_base_tpre_rescue.jsonl")
    af = [row for row in a if row["cohort_role"] == "fresh"]
    names, values = grouped_medians(af, "lexical_semantic_class", "KV_gain")
    bar("01_tpre_by_lexical_type.png", "Fresh t_pre K+V rescue by lexical type", names, values)
    names, values = grouped_medians(af, "visual_alignment", "KV_gain")
    bar("02_tpre_by_visual_alignment.png", "Fresh t_pre rescue by visual alignment", names, values)
    mode_rows = [{**row, "mode": mode, "gain": row[f"{mode}_gain"]} for row in af for mode in ("K", "V", "KV")]
    names, values = grouped_medians(mode_rows, "mode", "gain")
    bar("03_tpre_k_v_kv.png", "Fresh t_pre K/V mechanism", names, values)

    bpos = read_jsonl(OUT / "phase_b_recent/per_position_rescue.jsonl")
    bf = [row for row in bpos if row["cohort_role"] == "fresh"]
    distances = sorted({int(row["distance"]) for row in bf})
    plt.figure(figsize=(7, 4))
    plt.plot(distances, [np.median([row["gain"] for row in bf if int(row["distance"]) == distance]) for distance in distances], marker="o")
    plt.xlabel("Distance to t*")
    finish("04_recent_rescue_vs_distance.png", "Recent reasoning-token rescue vs distance")
    matched = [row for row in read_jsonl(OUT / "phase_b_recent/recency_matched_controls.jsonl") if row.get("comparison_family") == "lexical_semantic_class"]
    names, values = grouped_medians(matched, "focal_class", "gain_difference")
    bar("05_recent_type_recency_matched.png", "Token type minus recency-matched control", names, values)
    bgroups = [row for row in read_jsonl(OUT / "phase_b_recent/type_group_rescue.jsonl") if row["cohort_role"] == "fresh" and row["group"].startswith("lexical:")]
    names, values = grouped_medians(bgroups, "group", "gain")
    bar("06_recent_type_group.png", "Joint recent token-type group rescue", names, values)
    spans = [row for row in read_jsonl(OUT / "phase_b_recent/span_rescue.jsonl") if row["cohort_role"] == "fresh"]
    plt.figure(figsize=(6, 4))
    plt.boxplot([[row["gain"] for row in bf], [row["gain"] for row in spans]], tick_labels=["single token", "multi-token span"], showfliers=False)
    plt.axhline(0, color="black", linewidth=0.8)
    finish("07_span_vs_single.png", "Semantic-span vs single-position rescue")

    cpos = [row for row in read_jsonl(OUT / "phase_c_prompt/per_prompt_position_rescue.jsonl") if row["cohort_role"] == "fresh"]
    base_ids = sorted({row["base_problem_id"] for row in cpos}, key=int)[:20]
    max_position = max((int(row["relative_eligible_position"]) for row in cpos if row["base_problem_id"] in base_ids), default=0)
    matrix = np.full((len(base_ids), max_position + 1), np.nan)
    for row in cpos:
        if row["base_problem_id"] in base_ids:
            matrix[base_ids.index(row["base_problem_id"]), int(row["relative_eligible_position"])] = float(row["gain"])
    plt.figure(figsize=(10, max(4, 0.25 * len(base_ids))))
    plt.imshow(matrix, aspect="auto", cmap="coolwarm")
    plt.colorbar(label="Directional transfer gain")
    plt.xlabel("Eligible post-image prompt position")
    plt.ylabel("Fresh base")
    plt.yticks(range(len(base_ids)), base_ids)
    finish("08_prompt_position_heatmap.png", "Question/prompt token carrier heatmap", "Fresh base")
    cgroups = [row for row in read_jsonl(OUT / "phase_c_prompt/prompt_type_group_rescue.jsonl") if row["cohort_role"] == "fresh" and row["group"].startswith("lexical:")]
    names, values = grouped_medians(cgroups, "group", "gain")
    bar("09_prompt_type_group.png", "Prompt token-type group transfer", names, values)
    controls = read_jsonl(OUT / "phase_c_prompt/structural_controls.jsonl")
    for number, comparison, title in (
        (10, "target_aligned", "Target-aligned prompt token vs matched control"),
        (11, "punctuation", "Prompt punctuation vs matched control"),
    ):
        selected = [row for row in controls if row["comparison"] == comparison]
        plt.figure(figsize=(6, 4))
        plt.hist([row["gain_difference"] for row in selected], bins=20, color="#70ad47")
        plt.axvline(0, color="black", linewidth=0.8)
        finish(f"{number:02d}_{comparison}_matched.png", title, "Count")
    representative = sorted(cpos, key=lambda row: (int(row["base_problem_id"]), row["position"]))
    plt.figure(figsize=(9, 5))
    for base in sorted({row["base_problem_id"] for row in representative}, key=int)[:4]:
        rows = [row for row in representative if row["base_problem_id"] == base]
        plt.plot([row["relative_eligible_position"] for row in rows], [row["gain"] for row in rows], marker=".", label=f"base {base}")
    plt.legend()
    plt.xlabel("Eligible prompt position")
    finish("12_prompt_representative_sequences.png", "Representative prompt-token carrier profiles")

    cumulative = [row for row in read_jsonl(OUT / "phase_b_recent/fixed_recency_cumulative.jsonl") if row["cohort_role"] == "fresh"]
    widths = sorted({int(row["recent_width"]) for row in cumulative})
    plt.figure(figsize=(7, 4))
    plt.plot(widths, [np.median([row["gain"] for row in cumulative if int(row["recent_width"]) == width]) for width in widths], marker="o")
    plt.xlabel("Cumulative recent-cache width")
    finish("13_sparse_vs_distributed.png", "Fixed cumulative recent-cache rescue")
    specificity = read_json(OUT / "analysis/phase_specificity_analysis.json")["classes"]
    class_names = sorted(specificity)
    phases = ["phase_a_tpre_KV", "phase_b_recent_group_KV", "phase_c_prompt_group_KV"]
    values = np.asarray([[specificity[name][phase]["median"] if specificity[name][phase]["median"] is not None else np.nan for phase in phases] for name in class_names])
    plt.figure(figsize=(8, max(4, 0.35 * len(class_names))))
    plt.imshow(values, aspect="auto", cmap="coolwarm")
    plt.colorbar(label="Median gain")
    plt.xticks(range(3), ["t_pre", "recent group", "prompt group"], rotation=20)
    plt.yticks(range(len(class_names)), class_names)
    finish("14_phase_specificity.png", "Prefill vs late-reasoning carrier taxonomy", "Token class")
    names, values = grouped_medians(a, "cohort_role", "KV_gain")
    bar("15_historical_vs_fresh.png", "Historical anchor vs fresh t_pre rescue", names, values)
    special = [row for row in cpos if row["stream"] == "SPECIAL_CONTROL"]
    names, values = grouped_medians(special, "token_class", "gain")
    bar("16_special_control_tokens.png", "Special/control token carrier effects", names, values)

    d = read_jsonl(OUT / "phase_d_anchor/per_landmark_anchor_rescue.jsonl")
    if not d:
        gate = read_json(OUT / "phase_d_anchor/cohort_gate.json")
        reason = str(gate.get("reason", "Phase D was prospectively gated off"))
        for number, title in enumerate((
            "Long-horizon causal checkpoints",
            "Checkpoint density over reasoning progress",
            "Checkpoint type enrichment",
            "Acquisition vs future support",
            "Repeated-anchor trajectories",
            "Route phenotype comparison",
        ), start=17):
            placeholder(f"{number:02d}_phase_d_gated.png", title, reason)
    else:
        base = sorted({row["base_problem_id"] for row in d}, key=int)[0]
        rows = [row for row in d if row["base_problem_id"] == base]
        plt.figure(figsize=(9, 4)); plt.scatter([row["normalized_reasoning_position"] for row in rows], [row["future_rescue_gain"] for row in rows]); plt.xlabel("Normalized reasoning position"); finish("17_long_horizon_timeline.png", f"Causal checkpoints — base {base}")
        quarters = [0, 0, 0, 0]
        for row in d:
            if row["strong_checkpoint_A_plus_B"]: quarters[min(3, int(row["normalized_reasoning_position"] * 4))] += 1
        bar("18_checkpoint_density.png", "Directional checkpoint density", ["0-25%", "25-50%", "50-75%", "75-100%"], quarters, "Count")
        names, values = grouped_medians(d, "lexical_semantic_class", "future_rescue_gain"); bar("19_checkpoint_enrichment.png", "Checkpoint gain by lexical type", names, values)
        plt.figure(figsize=(6, 5)); plt.scatter([row["state_difference"]["mean_V_l2"] for row in d], [row["future_rescue_gain"] for row in d], alpha=.6); plt.xlabel("Landmark V-cache divergence"); finish("20_acquisition_future_scatter.png", "Acquisition-receiving vs future-supporting")
        counts = defaultdict(int)
        for row in d:
            counts[row["base_problem_id"]] += int(row["strong_checkpoint_A_plus_B"])
        names = sorted(counts, key=lambda value: (-counts[value], int(value)))[:12]; bar("21_repeated_anchor_trajectories.png", "Repeated directional checkpoints", names, [counts[name] for name in names], "Count")
        route = read_jsonl(OUT / "phase_d_anchor/route_ablation_results.jsonl")
        if route:
            names, values = grouped_medians(route, "route", "directional_loss"); bar("22_route_phenotypes.png", "Route phenotype comparison", names, values)
        else:
            placeholder("22_route_phenotypes.png", "Route phenotype comparison", "Route-control gate did not authorize a follow-up.")
    print(json.dumps({"figure_count": len(list(FIG.glob("*.png")))}, indent=2))


if __name__ == "__main__":
    main()
