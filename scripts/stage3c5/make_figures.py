#!/usr/bin/env python3
"""Create the 13 required Stage 3C.5 figures from frozen tables."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c5"
FIG = OUT / "analysis/figures"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def save(name: str) -> None:
    plt.tight_layout()
    plt.savefig(FIG / name, dpi=170)
    plt.close()


def main() -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    phase_a = read_json(OUT / "phase_a_tpre_layer/tpre_layer_statistics.json")
    per_a = read_jsonl(OUT / "phase_a_tpre_layer/per_problem_tpre_scope_results.jsonl")
    handoff = read_json(OUT / "phase_b_handoff/handoff_statistics.json")
    per_h = read_jsonl(OUT / "phase_b_handoff/per_problem_handoff.jsonl")
    gated = read_json(OUT / "phase_b_handoff/gated_r_statistics.json")
    hetero = read_json(OUT / "analysis/target_heterogeneity.json")
    controls = read_json(OUT / "controls/target_specificity_statistics.json")
    overlap = read_json(OUT / "secondary/retrieval_phenotype_overlap.json")
    classification = read_json(OUT / "analysis/handoff_classification.json")
    scopes = phase_a["scopes"]

    for target_id, number in (("target_a", "01"), ("target_b", "02")):
        values = [phase_a["targets"][target_id][scope]["loss_summary"]["median"] for scope in scopes]
        plt.figure(figsize=(6, 4))
        plt.plot(scopes, values, marker="o")
        plt.axhline(0, color="black", linewidth=0.8)
        plt.ylabel("Median evidence loss")
        plt.xlabel("Frozen t_pre layer scope")
        plt.title(f"{target_id.replace('_', ' ').title()}: t_pre necessity")
        save(f"{number}_{target_id}_tpre_loss.png")

    baseline_labels = ["A1 current", "A2 t_pre", "A3 joint"]
    baseline_keys = ["A1_current", "A2_tpre", "A3_joint"]
    baseline_values = [phase_a["baselines"][key]["retained_median"] for key in baseline_keys]
    plt.figure(figsize=(6, 4))
    plt.bar(baseline_labels, baseline_values, color=["#4C78A8", "#F58518", "#E45756"])
    plt.axhline(0.8, color="black", linestyle="--", linewidth=1)
    plt.ylabel("Median evidence retention")
    plt.title("Current-only, t_pre-only, and joint suppression")
    save("03_current_tpre_joint.png")

    plt.figure(figsize=(7, 4))
    for row in per_a:
        plt.plot(scopes, [row["base_aggregated_loss_by_scope"][scope] for scope in scopes], alpha=0.3)
    plt.plot(scopes, [phase_a["base_aggregated"][scope]["loss_summary"]["median"] for scope in scopes], color="black", marker="o", linewidth=2, label="median")
    plt.ylabel("Evidence loss")
    plt.title("Per-base t_pre layer-scope curves")
    plt.legend()
    save("04_per_base_tpre_curves.png")

    for carrier, number, color in (("R_last1", "05", "#4C78A8"), ("Q", "06", "#F58518"), ("h_pre", "07", "#54A24B")):
        values = [row["carriers"][carrier]["BCR"] for row in per_h]
        plt.figure(figsize=(8, 4))
        plt.bar(range(len(values)), values, color=color)
        plt.axhline(0, color="black", linewidth=0.8)
        plt.xlabel("Base problem")
        plt.ylabel("Bidirectional carrier restoration (BCR)")
        plt.title(f"{carrier}: semantic restoration")
        save(f"{number}_{carrier}_restoration.png")

    plt.figure(figsize=(6, 4))
    values = [[row["carriers"][carrier]["BCR"] for row in per_h] for carrier in ("R_last1", "Q", "h_pre")]
    plt.boxplot(values, tick_labels=["R_last1", "Q", "h_pre"], showfliers=False)
    plt.axhline(0, color="black", linewidth=0.8)
    plt.ylabel("BCR")
    plt.title("Carrier comparison across bases")
    save("08_carrier_comparison.png")

    r1 = [row["carriers"]["R_last1"]["CRR"] for row in per_h]
    r2 = gated["carriers"]["R_last2"]["CRR_values"]
    r4 = gated["carriers"]["R_last4"]["CRR_values"]
    plt.figure(figsize=(6, 4))
    for values in zip(r1, r2, r4):
        plt.plot([1, 2, 4], values, color="#4C78A8", alpha=0.3)
    plt.plot([1, 2, 4], [np.median(r1), np.median(r2), np.median(r4)], color="black", marker="o", linewidth=2)
    plt.xticks([1, 2, 4], ["last1", "last2", "last4"])
    plt.ylabel("Unclipped CRR")
    plt.title("Gated recent-reasoning recovery")
    save("09_nested_recent_R.png")

    carriers = ("R_last1", "Q", "h_pre")
    x = np.arange(len(carriers))
    a = [hetero["carrier_profiles"][carrier]["target_a"]["CRR_median"] for carrier in carriers]
    b = [hetero["carrier_profiles"][carrier]["target_b"]["CRR_median"] for carrier in carriers]
    plt.figure(figsize=(6, 4))
    plt.bar(x - 0.18, a, width=0.36, label="Target A")
    plt.bar(x + 0.18, b, width=0.36, label="Target B")
    plt.xticks(x, carriers)
    plt.ylabel("Median CRR")
    plt.title("Target-specific handoff profile")
    plt.legend()
    save("10_target_heterogeneity.png")

    plt.figure(figsize=(6, 4))
    names = ["Target T", "Mention M", "Irrelevant I"]
    values = [controls["median_loss"][key] for key in ("T", "M", "I")]
    plt.bar(names, values, color=["#E45756", "#72B7B2", "#B279A2"])
    plt.axhline(0, color="black", linewidth=0.8)
    plt.ylabel("Median P4 t_pre evidence loss")
    plt.title("Reduced target-specificity controls")
    save("11_target_vs_controls.png")

    alpha_v = [row["alphaV_T_tpre"] for row in overlap["rows"]]
    loss = [row["P4_tpre_loss"] for row in overlap["rows"]]
    rho = overlap["correlations"]["alphaV_T_tpre"]["P4_tpre_loss"]["rho"]
    plt.figure(figsize=(6, 4))
    plt.scatter(alpha_v, loss, alpha=0.8)
    plt.xlabel("Stage 3C.2 target alphaV at t_pre (descriptive)")
    plt.ylabel("Stage 3C.5 P4 evidence loss")
    plt.title(f"Prior phenotype overlap (Spearman rho={rho:.2f})")
    save("12_retrieval_phenotype_overlap.png")

    plt.figure(figsize=(10, 3.8))
    plt.axis("off")
    lines = [
        "target ROI at t_pre",
        "P4 layers 16–35 necessary",
        "R/Q/h_pre patches",
        "no clean base-aggregated carrier",
    ]
    xs = np.linspace(0.08, 0.92, len(lines))
    for index, (x_pos, label) in enumerate(zip(xs, lines)):
        plt.text(x_pos, 0.55, label, ha="center", va="center", bbox={"boxstyle": "round", "facecolor": "#E8F1FA"}, transform=plt.gca().transAxes)
        if index < len(lines) - 1:
            plt.annotate("", xy=(xs[index + 1] - 0.08, 0.55), xytext=(x_pos + 0.08, 0.55), arrowprops={"arrowstyle": "->"}, xycoords="axes fraction")
    plt.text(0.5, 0.15, f"Outcome: {classification['scientific_outcome']} | Review-only: {classification['recommendation']}", ha="center", transform=plt.gca().transAxes)
    plt.title("Stage 3C.5 handoff-mechanism summary")
    save("13_handoff_summary.png")
    print(json.dumps({"figure_count": len(list(FIG.glob("*.png"))), "figure_dir": str(FIG)}, indent=2))


if __name__ == "__main__":
    main()
