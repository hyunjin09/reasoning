#!/usr/bin/env python3
"""Create compact calibration-v2 figures from frozen derived tables."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/a6000_calibration_v2"
FIG = OUT / "analysis/figures"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    stress = read_jsonl(OUT / "phase1_path_feasibility/fixed_streaming_memory_stress.jsonl")
    bridge = read_json(OUT / "phase4_contrast_bridge/causal_contrast_agreement.json")["base_rows"]
    thresholds = read_json(OUT / "phase4_contrast_bridge/threshold_sensitivity.json")["rows"]
    devices = read_json(OUT / "phase5_devices/device_acceptance.json")["per_device"]

    plt.figure(figsize=(6.2, 4.0))
    plt.scatter([row["prefix_tokens"] for row in stress], [100 * row["peak_reserved_vram_fraction"] for row in stress])
    for row in stress:
        plt.annotate(row["base_problem_id"], (row["prefix_tokens"], 100 * row["peak_reserved_vram_fraction"]), fontsize=8)
    plt.axhline(90, color="firebrick", linestyle="--", label="frozen 90% ceiling")
    plt.xlabel("Generated prefix tokens")
    plt.ylabel("Peak reserved A6000 VRAM (%)")
    plt.title("Fixed 2,048-token streaming memory stress")
    plt.legend(frameon=False)
    plt.tight_layout()
    plt.savefig(FIG / "01_memory_stress.png", dpi=180)
    plt.close()

    families = ("suppression_loss", "kv_rescue_gain", "residual_rescue_gain")
    fig, axes = plt.subplots(1, 3, figsize=(11.0, 3.6))
    for axis, family in zip(axes, families):
        historical = [row[family]["historical"] for row in bridge]
        canonical = [row[family]["canonical"] for row in bridge]
        low = min(historical + canonical)
        high = max(historical + canonical)
        margin = max((high - low) * 0.08, 0.02)
        axis.scatter(historical, canonical)
        axis.plot([low - margin, high + margin], [low - margin, high + margin], color="0.5", linestyle="--")
        for row, x, y in zip(bridge, historical, canonical):
            axis.annotate(row["base_problem_id"], (x, y), fontsize=7)
        axis.set_xlabel("Historical cached effect")
        axis.set_ylabel("Canonical A6000 effect")
        axis.set_title(family.replace("_", " "))
    fig.suptitle("Strong/medium causal-contrast continuity (8 bases)")
    fig.tight_layout()
    fig.savefig(FIG / "02_causal_contrast_continuity.png", dpi=180)
    plt.close(fig)

    plt.figure(figsize=(6.2, 4.0))
    labels = [f"{row['threshold_nats_per_token']:.3f}" for row in thresholds]
    values = [row["classified_positive"] for row in thresholds]
    colors = ["#d95f02" if row["primary"] else "#7570b3" for row in thresholds]
    plt.bar(labels, values, color=colors)
    plt.ylim(0, 12.8)
    plt.xlabel("Suppression-loss threshold (nats/token)")
    plt.ylabel("Positive bases / 12")
    plt.title("Prospective threshold sensitivity")
    plt.tight_layout()
    plt.savefig(FIG / "03_threshold_sensitivity.png", dpi=180)
    plt.close()

    fig, axes = plt.subplots(1, 2, figsize=(9.0, 3.8))
    probe_bases = [row["base_problem_id"] for row in devices[0]["short_results"]]
    for device in devices:
        axes[0].plot(
            probe_bases,
            [row["suppression_interaction"] for row in device["short_results"]],
            marker="o", label=f"device {device['device_index']}",
        )
    axes[0].set_xlabel("Bridge base")
    axes[0].set_ylabel("Suppression interaction")
    axes[0].set_title("Cross-device replay")
    axes[0].legend(frameon=False, fontsize=8)
    axes[1].bar(
        [str(row["device_index"]) for row in devices],
        [100 * row["long_stress"]["peak_reserved_vram_fraction"] for row in devices],
    )
    axes[1].axhline(90, color="firebrick", linestyle="--")
    axes[1].set_xlabel("A6000 device index")
    axes[1].set_ylabel("Base-351 peak reserved VRAM (%)")
    axes[1].set_title("Long-prefix stress")
    fig.tight_layout()
    fig.savefig(FIG / "04_cross_device_validation.png", dpi=180)
    plt.close(fig)


if __name__ == "__main__":
    main()
