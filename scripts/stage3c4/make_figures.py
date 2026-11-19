#!/usr/bin/env python3
"""Create the thirteen required Stage 3C.4 figures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c4"
FIG = OUT / "analysis/figures"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def finish(path: Path) -> None:
    plt.tight_layout()
    plt.savefig(path, dpi=170, bbox_inches="tight")
    plt.close()


def line_summary(labels: list[str], medians: list[float], title: str, path: Path) -> None:
    plt.figure(figsize=(6.2, 4.0))
    plt.plot(labels, medians, marker="o", linewidth=2)
    plt.axhline(0.8, color="gray", linestyle="--", linewidth=1, label="0.80 descriptive threshold")
    plt.ylabel("Median evidence retention (unclipped)")
    plt.title(title)
    plt.legend(frameon=False)
    finish(path)


def main() -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    layer_stats = read_json(OUT / "phase_a_layer/layer_scope_statistics.json")
    time_stats = read_json(OUT / "phase_b_time/temporal_statistics.json")
    interaction_stats = read_json(OUT / "phase_c_interaction/interaction_statistics.json")
    necessity = read_json(OUT / "phase_b_time/temporal_necessity_summary.json")
    layer_rows = read_jsonl(OUT / "phase_a_layer/per_problem_layer_scope_results.jsonl")
    time_rows = read_jsonl(OUT / "phase_b_time/per_problem_temporal_results.jsonl")
    scopes = layer_stats["scopes"]
    windows = time_stats["windows"]

    for number, target_id, label in ((1, "target_a", "Target A"), (2, "target_b", "Target B")):
        line_summary(
            scopes,
            [layer_stats["targets"][target_id][scope]["retained_median"] for scope in scopes],
            f"{label}: current-query retention vs layer scope",
            FIG / f"{number:02d}_{target_id}_layer_scope.png",
        )

    plt.figure(figsize=(6.5, 4.3))
    for row in layer_rows:
        plt.plot(scopes, [row["base_aggregated_retention_by_scope"][scope] for scope in scopes], alpha=0.28)
    plt.plot(scopes, [layer_stats["base_aggregated"][scope]["retained_median"] for scope in scopes], color="black", marker="o", linewidth=2.5, label="cohort median")
    plt.axhline(0.8, color="gray", linestyle="--", linewidth=1)
    plt.ylabel("Base-aggregated evidence retention")
    plt.title("Per-base current-query layer-scope curves")
    plt.legend(frameon=False)
    finish(FIG / "03_per_base_layer_scope_curves.png")

    for number, target_id, label in ((4, "target_a", "Target A"), (5, "target_b", "Target B")):
        line_summary(
            windows,
            [time_stats["targets"][target_id][window]["retained_median"] for window in windows],
            f"{label}: all-layer retention vs backward window",
            FIG / f"{number:02d}_{target_id}_temporal_window.png",
        )

    plt.figure(figsize=(6.5, 4.3))
    for row in time_rows:
        plt.plot(windows, [row["base_aggregated_retention_by_window"][window] for window in windows], alpha=0.28)
    plt.plot(windows, [time_stats["base_aggregated"][window]["retained_median"] for window in windows], color="black", marker="o", linewidth=2.5, label="cohort median")
    plt.axhline(0.8, color="gray", linestyle="--", linewidth=1)
    plt.ylabel("Base-aggregated evidence retention")
    plt.title("Per-base all-layer temporal-suppression curves")
    plt.legend(frameon=False)
    finish(FIG / "06_per_base_temporal_curves.png")

    heat = np.asarray([
        [interaction_stats["base_aggregated"]["C1"]["retained_median"], interaction_stats["base_aggregated"]["C2"]["retained_median"]],
        [interaction_stats["base_aggregated"]["C3"]["retained_median"], interaction_stats["base_aggregated"]["C4"]["retained_median"]],
    ])
    plt.figure(figsize=(5.4, 4.1))
    image = plt.imshow(heat, cmap="viridis", vmin=min(0.0, float(heat.min())), vmax=max(1.0, float(heat.max())))
    plt.xticks([0, 1], ["last 4", "last 8"])
    plt.yticks([0, 1], ["layers 24–35", "layers 0–35"])
    for i in range(2):
        for j in range(2):
            plt.text(j, i, f"{heat[i, j]:.3f}", ha="center", va="center", color="white" if heat[i, j] < 0.65 else "black")
    plt.colorbar(image, label="Median evidence retention")
    plt.title("Frozen layer × time interaction cells")
    finish(FIG / "07_layer_time_heatmap.png")

    plt.figure(figsize=(5.8, 4.0))
    labels = ["W4 current\n(L0)", "All-layer current\n(L4/T0)"]
    for index, target in enumerate(("target_a", "target_b")):
        values = [
            layer_stats["targets"][target]["L0"]["retained_median"],
            layer_stats["targets"][target]["L4"]["retained_median"],
        ]
        plt.plot(labels, values, marker="o", linewidth=2, label=target.replace("_", " ").title())
    plt.axhline(0.8, color="gray", linestyle="--", linewidth=1)
    plt.ylabel("Median evidence retention")
    plt.title("W4-only vs all-layer current suppression")
    plt.legend(frameon=False)
    finish(FIG / "08_w4_vs_all_layer_current.png")

    mention = read_jsonl(OUT / "controls/mention_suppression_results.jsonl")
    irrelevant = read_jsonl(OUT / "controls/irrelevant_suppression_results.jsonl")
    control_lookup = {"M": mention, "I": irrelevant}
    bar_labels = []
    bar_values = []
    for window in ("T0", "T4"):
        target_loss = []
        for row in mention:
            target_loss.extend(row["targets"][target][window]["target_loss"] for target in ("target_a", "target_b"))
        bar_labels.append(f"T {window}")
        bar_values.append(float(np.median(target_loss)))
        for source in ("M", "I"):
            values = []
            for row in control_lookup[source]:
                values.extend(row["targets"][target][window]["control_loss"] for target in ("target_a", "target_b"))
            bar_labels.append(f"{source} {window}")
            bar_values.append(float(np.median(values)))
    plt.figure(figsize=(7.0, 4.0))
    plt.bar(bar_labels, bar_values, color=["#c44e52", "#4c72b0", "#55a868"] * 2)
    plt.ylabel("Median unnormalized evidence loss")
    plt.title("Target vs mention/irrelevant suppression")
    finish(FIG / "09_target_vs_control_suppression.png")

    comparison = read_json(OUT / "secondary/stage3b2_comparison.json")
    comp_rows = comparison["per_target_base"]
    plt.figure(figsize=(6.7, 4.1))
    x = ["3B.2 normalized\nsource switch", "3C.4 current\ndamage", "3C.4 T16\ndamage"]
    for target_id in ("target_a", "target_b"):
        selected = [row for row in comp_rows if row["target_id"] == target_id]
        values = [
            float(np.median([row["stage3b2_normalized_BRI"] for row in selected])),
            1.0 - layer_stats["targets"][target_id]["L4"]["retained_median"],
            1.0 - time_stats["targets"][target_id]["T16"]["retained_median"],
        ]
        plt.plot(x, values, marker="o", linewidth=2, label=target_id.replace("_", " ").title())
    plt.ylabel("Normalized descriptive magnitude")
    plt.title("Distinct interventions: source switch vs contribution suppression")
    plt.legend(frameon=False)
    finish(FIG / "10_stage3b2_vs_stage3c4_timing.png")

    for number, field, title in ((11, "per_base_w_80_counts", "Per-base tested w₈₀"), (12, "per_base_w_50_counts", "Per-base tested w₅₀")):
        counts = necessity[field]
        ordered = [label for label in (*windows, "None") if label in counts]
        plt.figure(figsize=(6.0, 3.9))
        plt.bar(ordered, [counts[label] for label in ordered], color="#4c72b0")
        plt.ylabel("Number of base problems")
        plt.title(title)
        finish(FIG / f"{number:02d}_{field}.png")

    phenotype_labels = ["L0 current", "L4 current", "L4 last 1", "L4 last 4", "L4 last 16"]
    phenotype_values = [
        layer_stats["base_aggregated"]["L0"]["retained_median"],
        layer_stats["base_aggregated"]["L4"]["retained_median"],
        time_stats["base_aggregated"]["T1"]["retained_median"],
        time_stats["base_aggregated"]["T4"]["retained_median"],
        time_stats["base_aggregated"]["T16"]["retained_median"],
    ]
    plt.figure(figsize=(7.0, 4.0))
    plt.bar(phenotype_labels, phenotype_values, color="#8172b2")
    plt.axhline(0.8, color="gray", linestyle="--", linewidth=1)
    plt.xticks(rotation=18, ha="right")
    plt.ylabel("Median evidence retention")
    plt.title("Stage 3C.4 temporal-redundancy phenotype")
    finish(FIG / "13_spatiotemporal_phenotype.png")

    print(json.dumps({"figure_count": len(list(FIG.glob("*.png"))), "figure_dir": str(FIG.relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()
