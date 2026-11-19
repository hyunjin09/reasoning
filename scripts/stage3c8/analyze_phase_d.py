#!/usr/bin/env python3
"""Aggregate Phase-D acquisition-receiving and future-supporting landmark evidence."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from visual_reasoning.stage0.io import write_json, write_jsonl
from visual_reasoning.stage3c8.analysis import holm_adjust, inferential_summary, robust_positive


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c8"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-root", type=Path, required=True)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def aligned(value: float, condition: str) -> float:
    return float(value) if condition == "O" else -float(value)


def main() -> None:
    args = parse_args()
    manifest_count = sum(1 for line in (OUT / "phase_d_anchor/long_horizon_manifest.jsonl").read_text(encoding="utf-8").splitlines() if line.strip())
    raw = [read_json(path) for path in sorted(args.raw_root.glob("**/examples/*/result.json"))]
    if len(raw) != manifest_count:
        raise RuntimeError(f"Phase-D result count mismatch: {len(raw)}/{manifest_count}")
    deficit_rows, rescue_rows = [], []
    for result in raw:
        base = str(result["base_problem_id"])
        for landmark in result["landmarks"]:
            annotation = landmark["annotation"]
            losses, gains = [], []
            state_differences = []
            per_condition = {}
            for condition, scores in landmark["conditions"].items():
                native = aligned(scores["native"]["D"], condition)
                suppressed = aligned(scores["suppressed"]["D"], condition)
                rescued = aligned(scores["rescue"]["D"], condition)
                loss = native - suppressed
                gain = rescued - suppressed
                losses.append(loss)
                gains.append(gain)
                state = scores["state_difference"]
                state_differences.extend(state.values())
                per_condition[condition] = {
                    "native_aligned_D": native,
                    "suppressed_aligned_D": suppressed,
                    "rescued_aligned_D": rescued,
                    "local_suppression_loss": loss,
                    "future_rescue_gain": gain,
                }
            loss = float(np.mean(losses))
            gain = float(np.mean(gains))
            acquisition = bool(any(row["any_difference"] for row in state_differences))
            evaluable = acquisition and abs(loss) > 1e-8
            common = {
                "base_problem_id": base,
                "example_id": str(result["example_id"]),
                "landmark_generated_index": int(annotation["landmark_generated_index"]),
                "landmark_types": annotation["landmark_types"],
                "normalized_reasoning_position": float(annotation["normalized_reasoning_position"]),
                "token_text": annotation["token_text"],
                "lexical_semantic_class": annotation["lexical_semantic_class"],
                "visual_alignment": annotation["visual_alignment"],
                "structural_role": annotation["structural_role"],
                "reasoning_role": annotation["reasoning_role"],
                "long_horizon_roles": annotation["long_horizon_roles"],
                "acquisition_receiving": acquisition,
                "locally_evaluable": evaluable,
                "state_difference": {
                    "mean_K_l2": float(np.mean([row["K_l2"] for row in state_differences])),
                    "mean_V_l2": float(np.mean([row["V_l2"] for row in state_differences])),
                    "max_K_abs": max(row["K_max_abs"] for row in state_differences),
                    "max_V_abs": max(row["V_max_abs"] for row in state_differences),
                },
                "condition_metrics": per_condition,
            }
            deficit_rows.append({**common, "local_suppression_loss": loss})
            rescue_rows.append({
                **common,
                "local_suppression_loss": loss,
                "future_rescue_gain": gain,
                "anchor_rescue_ratio": None if loss == 0 else gain / loss,
                "future_supporting_directional": bool(evaluable and gain > 0),
                "strong_checkpoint_A_plus_B": bool(evaluable and gain > 0),
            })
    order = lambda row: (int(row["base_problem_id"]), row["landmark_generated_index"])
    deficit_rows.sort(key=order)
    rescue_rows.sort(key=order)
    write_jsonl(OUT / "phase_d_anchor/local_acquisition_deficits.jsonl", deficit_rows)
    write_jsonl(OUT / "phase_d_anchor/per_landmark_anchor_rescue.jsonl", rescue_rows)
    write_jsonl(OUT / "phase_d_anchor/future_use_results.jsonl", rescue_rows)

    by_family: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for row in rescue_rows:
        if not row["locally_evaluable"]:
            continue
        families = [f"landmark:{value}" for value in row["landmark_types"]]
        families += [f"lexical:{row['lexical_semantic_class']}", f"reasoning:{row['reasoning_role']}"]
        for family in families:
            by_family[family][row["base_problem_id"]].append(float(row["future_rescue_gain"]))
    summaries = {}
    for family, bases in by_family.items():
        values = {base: float(np.mean(gains)) for base, gains in bases.items()}
        summary = inferential_summary(values)
        summary["inferentially_eligible"] = len(values) >= 12
        summaries[family] = summary
    eligible = sorted(name for name, row in summaries.items() if row["inferentially_eligible"])
    adjusted = holm_adjust([summaries[name]["wilcoxon_p"] for name in eligible])
    for name, p_value in zip(eligible, adjusted):
        summaries[name]["holm_p"] = p_value
        summaries[name]["robust_positive"] = robust_positive(summaries[name])
    for name in set(summaries) - set(eligible):
        summaries[name]["holm_p"] = None
        summaries[name]["robust_positive"] = False
    gated = sorted(name for name, row in summaries.items() if name.startswith("landmark:") and row["robust_positive"])
    write_json(OUT / "phase_d_anchor/necessity_gate.json", {
        "run": bool(gated),
        "gated_landmark_categories": gated,
        "criterion": "N>=12 and robust future-use rescue under frozen Stage3C8 rule",
        "selected_before_necessity_scores": True,
        "family_statistics": summaries,
    })
    write_json(OUT / "phase_d_anchor/route_gate.json", {
        "run": bool(gated),
        "gated_landmark_categories": gated,
        "criterion": "same predeclared robust future-use landmark-category gate; route subset must freeze before route scores",
        "selected_before_route_scores": True,
    })
    write_jsonl(OUT / "phase_d_anchor/gated_necessity_results.jsonl", [])
    write_jsonl(OUT / "phase_d_anchor/route_ablation_results.jsonl", [])
    write_json(OUT / "phase_d_anchor/anchor_classification.json", {
        "rows": rescue_rows,
        "family_statistics": summaries,
        "strong_checkpoint_definition": "acquisition-receiving plus directionally future-supporting; category claims require robust base-level inference",
        "individual_labels_are_descriptive": True,
    })
    density = defaultdict(lambda: [0, 0, 0, 0])
    for row in rescue_rows:
        if row["strong_checkpoint_A_plus_B"]:
            bucket = min(3, int(float(row["normalized_reasoning_position"]) * 4))
            density[row["base_problem_id"]][bucket] += 1
    write_json(OUT / "phase_d_anchor/anchor_density.json", {
        "quarters": ["0-25%", "25-50%", "50-75%", "75-100%"],
        "per_base_directional_checkpoint_counts": dict(density),
        "attention_used": False,
    })
    write_json(OUT / "phase_d_anchor/anchor_type_enrichment.json", {
        "family_statistics": summaries,
        "matched_phase_b_controls_are_primary_for_token_type_claims": True,
    })
    print(json.dumps({"bases": len(raw), "landmarks": len(rescue_rows), "necessity_gate": bool(gated)}, indent=2))


if __name__ == "__main__":
    main()
