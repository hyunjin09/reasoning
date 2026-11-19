#!/usr/bin/env python3
"""Post-freeze secondary comparison of ROI attention and causal Value effects."""

from __future__ import annotations

import json
import statistics
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import spearmanr

from visual_reasoning.stage0.io import ensure_directory, write_json


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b8"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def correlation(rows: list[dict[str, Any]], x: str, y: str) -> dict[str, Any]:
    usable = [row for row in rows if row.get(x) is not None and row.get(y) is not None]
    if len(usable) < 3 or len({row[x] for row in usable}) < 2 or len({row[y] for row in usable}) < 2:
        return {"N": len(usable), "spearman_rho": None, "p_value": None}
    value = spearmanr([row[x] for row in usable], [row[y] for row in usable])
    return {"N": len(usable), "spearman_rho": float(value.statistic), "p_value": float(value.pvalue)}


def main() -> None:
    primary_path = OUT / "subspace/primary_projected_results.jsonl"
    if not primary_path.is_file():
        raise RuntimeError("Primary causal subspace results must be frozen first")
    config = read_json(OUT / "config/stage3b8_config.json")
    target_to_cell = {row["target_id"]: row["cell_id"] for row in config["targets"]}
    primary = {(row["base_problem_id"], target_to_cell[row["target_id"]]): row for row in read_jsonl(primary_path)}
    historical = read_json(ROOT / "outputs/stage3b7r/analysis/attention_secondary_analysis.json")
    joined = []
    for row in historical["selected_head_rows"]:
        key = (str(row["base_problem_id"]), str(row["cell_id"]))
        causal = primary.get(key)
        if causal is None:
            continue
        joined.append({
            "base_problem_id": key[0],
            "cell_id": key[1],
            "target_id": next(target for target, cell in target_to_cell.items() if cell == key[1]),
            "selected_head_target_roi_attention_mass": float(row["selected_head_target_roi_attention_mass"]),
            "full_V_BVR": float(causal["B_full"]),
            "learned_subspace_BVR": float(causal["B_parallel"]),
            "orthogonal_complement_BVR": float(causal["B_perp"]),
        })
    if len(joined) != 74:
        raise RuntimeError(f"Expected 74 target-specific primary joins, observed {len(joined)}")
    by_base = []
    for base in sorted({row["base_problem_id"] for row in joined}, key=int):
        rows = [row for row in joined if row["base_problem_id"] == base]
        by_base.append({
            "base_problem_id": base,
            **{key: float(statistics.fmean(row[key] for row in rows)) for key in (
                "selected_head_target_roi_attention_mass", "full_V_BVR", "learned_subspace_BVR", "orthogonal_complement_BVR"
            )},
        })
    per_target = {}
    for target in config["targets"]:
        rows = [row for row in joined if row["target_id"] == target["target_id"]]
        per_target[target["target_id"]] = {
            "attention_vs_full_V": correlation(rows, "selected_head_target_roi_attention_mass", "full_V_BVR"),
            "attention_vs_learned_subspace": correlation(rows, "selected_head_target_roi_attention_mass", "learned_subspace_BVR"),
        }
    payload = {
        "secondary_only": True,
        "performed_after_primary_causal_and_subspace_freeze": True,
        "selection_used_attention": False,
        "independent_unit": "base_problem_id",
        "target_specific_row_count": len(joined),
        "base_count": len(by_base),
        "pooled_base_averaged": {
            "attention_vs_full_V": correlation(by_base, "selected_head_target_roi_attention_mass", "full_V_BVR"),
            "attention_vs_learned_subspace": correlation(by_base, "selected_head_target_roi_attention_mass", "learned_subspace_BVR"),
        },
        "per_target": per_target,
        "target_specific_rows": joined,
        "base_averaged_rows": by_base,
        "attention_is_descriptive_not_causal": True,
    }
    ensure_directory(OUT / "secondary")
    ensure_directory(OUT / "analysis/figures")
    write_json(OUT / "secondary/attention_comparison.json", payload)
    fig, axes = plt.subplots(2, 2, figsize=(10.5, 9))
    for column, target in enumerate(config["targets"]):
        rows = [row for row in joined if row["target_id"] == target["target_id"]]
        x = [row["selected_head_target_roi_attention_mass"] for row in rows]
        axes[0, column].scatter(x, [row["full_V_BVR"] for row in rows], alpha=0.68)
        axes[0, column].set(title=f"{target['target_id']}: attention vs full V", xlabel="selected-head target-ROI attention mass", ylabel="full V BVR")
        axes[1, column].scatter(x, [row["learned_subspace_BVR"] for row in rows], alpha=0.68)
        axes[1, column].set(title=f"{target['target_id']}: attention vs subspace", xlabel="selected-head target-ROI attention mass", ylabel="learned-subspace BVR")
    fig.tight_layout()
    fig.savefig(OUT / "analysis/figures/attention_vs_causal_value_subspace.png", dpi=180)
    plt.close(fig)
    print(json.dumps(payload["pooled_base_averaged"], indent=2))


if __name__ == "__main__":
    main()
