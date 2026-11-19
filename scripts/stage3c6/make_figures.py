#!/usr/bin/env python3
"""Create the 14 prespecified Stage 3C.6 figures from frozen analyses."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c6"
FIG = OUT / "analysis/figures"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def save(name: str) -> None:
    plt.tight_layout()
    plt.savefig(FIG / name, dpi=170)
    plt.close()


def layer_rows(target: str) -> list[dict[str, Any]]:
    return read_json(OUT / f"phase_a_hpre_scan/{target}_layer_statistics.json")["sign_aligned_layers"]


def main() -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    per_a = read_jsonl(OUT / "phase_a_hpre_scan/per_problem_layer_rescue.jsonl")
    crossings = read_json(OUT / "phase_a_hpre_scan/threshold_crossings.json")
    boundary = read_json(OUT / "phase_b_boundary/boundary_statistics.json")
    per_b = read_jsonl(OUT / "phase_b_boundary/per_problem_boundary_rescue.jsonl")
    controls = read_json(OUT / "controls/control_statistics.json")
    dose = read_json(OUT / "phase_c_optional_dose/dose_statistics.json")
    secondary = read_json(OUT / "secondary/stage3c5_semantic_patch_comparison.json")

    # 1–4: target-specific broad profiles, with ratios and primary gains separated.
    for target, number in (("target_a", "01"), ("target_b", "02")):
        rows = layer_rows(target)
        layers = [row["layer"] for row in rows]
        medians = [row["median_RR"] for row in rows]
        plt.figure(figsize=(7, 4))
        plt.plot(layers, medians, marker="o", markersize=3, label="median unclipped RR")
        for threshold in (0.2, 0.5, 0.8):
            plt.axhline(threshold, color="grey", linestyle="--", linewidth=0.7)
        robust = [row for row in rows if row["robust_positive"]]
        plt.scatter([row["layer"] for row in robust], [row["median_RR"] for row in robust], color="#E45756", s=22, label="robust positive")
        plt.xlabel("Layer")
        plt.ylabel("Median rescue ratio (unclipped)")
        plt.title(f"{target.replace('_', ' ').title()}: h_pre current-residual rescue")
        plt.legend(fontsize=8)
        save(f"{number}_{target}_hpre_rescue_ratio.png")

    for target, number in (("target_a", "03"), ("target_b", "04")):
        rows = layer_rows(target)
        plt.figure(figsize=(7, 4))
        plt.plot([row["layer"] for row in rows], [row["median_gain"] for row in rows], marker="o", markersize=3, color="#4C78A8")
        plt.axhline(0, color="black", linewidth=0.8)
        plt.xlabel("Layer")
        plt.ylabel("Median unnormalized rescue gain")
        plt.title(f"{target.replace('_', ' ').title()}: primary rescue effect")
        save(f"{number}_{target}_unnormalized_gain.png")

    # 5: native, suppressed, and the target-specific peak h_pre rescue.
    labels, native, suppressed, rescued = [], [], [], []
    for target in ("target_a", "target_b"):
        peak_layer = str(crossings[target]["peak_gain_layer"])
        labels.append(target.replace("target_", "Target ").upper())
        native.append(float(np.median([row["targets"][target]["sign_aligned"]["native"] for row in per_a])))
        suppressed.append(float(np.median([row["targets"][target]["sign_aligned"]["suppressed"] for row in per_a])))
        rescued.append(float(np.median([
            row["targets"][target]["sign_aligned"]["suppressed"]
            + row["targets"][target]["sign_aligned"]["layers"][peak_layer]["rescue_gain"]
            for row in per_a
        ])))
    x = np.arange(2)
    plt.figure(figsize=(7, 4))
    plt.bar(x - 0.24, native, 0.24, label="Native")
    plt.bar(x, suppressed, 0.24, label="Suppressed P4")
    plt.bar(x + 0.24, rescued, 0.24, label="Peak h_pre rescue")
    plt.xticks(x, labels)
    plt.ylabel("Aligned evidence score")
    plt.title("Native, suppressed, and peak-rescued evidence scores")
    plt.legend()
    save("05_native_suppressed_peak_rescued.png")

    # 6–7: all base-problem curves, preserving the independent unit.
    for target, number in (("target_a", "06"), ("target_b", "07")):
        rows = layer_rows(target)
        layers = [row["layer"] for row in rows]
        plt.figure(figsize=(8, 4.5))
        for row in per_a:
            plt.plot(layers, [row["targets"][target]["sign_aligned"]["layers"][str(layer)]["rescue_ratio"] for layer in layers], alpha=0.22)
        plt.plot(layers, [row["median_RR"] for row in rows], color="black", linewidth=2, label="median")
        plt.axhline(0, color="black", linewidth=0.7)
        plt.xlabel("Layer")
        plt.ylabel("Unclipped rescue ratio")
        plt.title(f"{target.replace('_', ' ').title()}: per-base h_pre rescue curves")
        plt.legend()
        save(f"{number}_{target}_per_base_curves.png")

    # 8–9: magnitude of the suppression-induced current-state difference.
    layers = [row["layer"] for row in layer_rows("target_a")]
    plt.figure(figsize=(7, 4))
    for target, color in (("target_a", "#4C78A8"), ("target_b", "#F58518")):
        rows = layer_rows(target)
        plt.plot(layers, [row["median_residual_delta_l2"] for row in rows], marker="o", markersize=3, label=target, color=color)
    plt.xlabel("Layer")
    plt.ylabel("Median ||h_native - h_suppressed||2")
    plt.title("Suppression-induced current-residual delta")
    plt.legend()
    save("08_residual_delta_norm_vs_layer.png")

    plt.figure(figsize=(6, 4.5))
    for target, color in (("target_a", "#4C78A8"), ("target_b", "#F58518")):
        rows = layer_rows(target)
        plt.scatter([row["median_residual_delta_l2"] for row in rows], [row["median_gain"] for row in rows], label=target, color=color, alpha=0.8)
    plt.xlabel("Median residual-delta L2")
    plt.ylabel("Median unnormalized rescue gain")
    plt.title("Rescue gain versus current-state difference")
    plt.legend()
    save("09_gain_vs_residual_delta.png")

    # 10: detailed within-block boundaries in each gated region.
    active = list(boundary["targets"])
    figure, axes = plt.subplots(len(active), 1, figsize=(9, 3.8 * len(active)), squeeze=False)
    for axis, target in zip(axes[:, 0], active):
        target_data = boundary["targets"][target]
        xs = np.arange(len(target_data["rescue_rows"]))
        axis.plot(xs, [row["median_RR"] for row in target_data["rescue_rows"]], marker="o", label=target)
        axis.set_xticks(xs, [row["key"].replace("_h_", "\nh_") for row in target_data["rescue_rows"]], rotation=30, ha="right")
        axis.axhline(0, color="black", linewidth=0.7)
        axis.set_ylabel("Median unclipped RR")
        axis.set_title(f"{target.replace('_', ' ').title()}: frozen-region boundary rescue")
    figure.suptitle("Within-block current-residual decomposition", y=1.01)
    save("10_within_block_boundary_rescue.png")

    # 11: direct A/B broad-profile comparison.
    plt.figure(figsize=(7, 4))
    for target, color in (("target_a", "#4C78A8"), ("target_b", "#F58518")):
        rows = layer_rows(target)
        plt.plot([row["layer"] for row in rows], [row["median_RR"] for row in rows], label=target, color=color)
    plt.axhline(0, color="black", linewidth=0.7)
    plt.xlabel("Layer")
    plt.ylabel("Median unclipped rescue ratio")
    plt.title("Target A versus Target B residual rescue")
    plt.legend()
    save("11_target_a_vs_b_profile.png")

    # 12: target-deficit rescue versus mention/irrelevant controls.
    active_targets = list(controls["targets"])
    names = [f"{target[-1].upper()}-{source}" for target in active_targets for source in ("T", "M", "I")]
    values = [controls["targets"][target]["sources"][source]["rescue_gain"]["median"] for target in active_targets for source in ("T", "M", "I")]
    plt.figure(figsize=(8, 4))
    plt.bar(names, values, color=["#E45756", "#72B7B2", "#B279A2"] * len(active_targets))
    plt.axhline(0, color="black", linewidth=0.7)
    plt.ylabel("Median unnormalized rescue gain")
    plt.title("Target versus mention/irrelevant deficit rescue")
    save("12_target_vs_control_rescue.png")

    # 13: optional dose response at the target-specific strongest boundary.
    plt.figure(figsize=(7, 4))
    for target, color in (("target_a", "#4C78A8"), ("target_b", "#F58518")):
        if target not in dose["targets"]:
            continue
        curve = dose["targets"][target]["curve"]
        plt.plot([row["lambda"] for row in curve], [row["gain"]["median"] for row in curve], marker="o", label=target, color=color)
    plt.axhline(0, color="black", linewidth=0.7)
    plt.xlabel("Residual-delta interpolation lambda")
    plt.ylabel("Median unnormalized rescue gain")
    plt.title("Frozen current-residual dose response")
    plt.legend()
    save("13_residual_delta_dose_curve.png")

    # 14: prior semantic h_pre transfer and current within-condition rescue.
    targets = list(secondary["targets"])
    x = np.arange(len(targets))
    old = [secondary["targets"][target]["stage3c5_median_CRR"] for target in targets]
    new = [secondary["targets"][target]["stage3c6_median_RR"] for target in targets]
    plt.figure(figsize=(6, 4))
    plt.bar(x - 0.18, old, width=0.36, label="Stage 3C.5 semantic CRR")
    plt.bar(x + 0.18, new, width=0.36, label="Stage 3C.6 suppression RR")
    plt.xticks(x, [target.replace("target_", "Target ").upper() for target in targets])
    plt.ylabel("Median unclipped ratio")
    plt.title("Semantic transfer versus within-condition rescue")
    plt.legend(fontsize=8)
    save("14_stage3c5_vs_stage3c6.png")

    names = sorted(path.name for path in FIG.glob("*.png"))
    if len(names) != 14:
        raise RuntimeError(f"Expected exactly 14 figures, found {len(names)}: {names}")
    print(json.dumps({"figure_count": len(names), "figures": names}, indent=2))


if __name__ == "__main__":
    main()
