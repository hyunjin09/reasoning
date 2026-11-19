#!/usr/bin/env python3
"""Aggregate Stage 3C8 natural-t_pre carrier results at the base level."""

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
    parser.add_argument("--historical-root", type=Path, required=True)
    parser.add_argument("--fresh-root", type=Path, required=True)
    parser.add_argument("--annotations", type=Path, required=True)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def results(root: Path) -> list[dict[str, Any]]:
    return [read_json(path) for path in sorted(root.glob("**/examples/*/result.json"))]


def aligned(value: float, condition: str) -> float:
    return float(value) if condition == "O" else -float(value)


def exact(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return bool(
        float(left["D"]) == float(right["D"])
        and left["original_candidate"]["token_log_probabilities"] == right["original_candidate"]["token_log_probabilities"]
        and left["counterfactual_candidate"]["token_log_probabilities"] == right["counterfactual_candidate"]["token_log_probabilities"]
    )


def main() -> None:
    args = parse_args()
    annotations = read_jsonl(args.annotations)
    annotation_lookup = {
        (str(row["base_problem_id"]), str(row["coordinate"]), int(row["generated_index"])): row
        for row in annotations if row["stream"] == "PREVIOUS_REASONING"
    }
    rows = []
    for role, raw_root in (("historical", args.historical_root), ("fresh", args.fresh_root)):
        raw = results(raw_root)
        expected = 24 if role == "historical" else len(read_jsonl(OUT / "cohort/fresh_atlas_manifest.jsonl"))
        if len(raw) != expected:
            raise RuntimeError(f"Phase-A {role} result count mismatch: {len(raw)}/{expected}")
        for result in raw:
            base = str(result["base_problem_id"])
            for coordinate, target in result["coordinates"].items():
                token = annotation_lookup[(base, coordinate, int(target["tpre_generated_index"]))]
                condition_metrics = {}
                losses = []
                gains = {mode: [] for mode in ("K", "V", "KV")}
                for condition, score in target["conditions"].items():
                    native = aligned(score["native"]["D"], condition)
                    suppressed = aligned(score["suppressed"]["D"], condition)
                    loss = native - suppressed
                    condition_metrics[condition] = {"native_aligned_D": native, "suppressed_aligned_D": suppressed, "suppression_loss": loss}
                    losses.append(loss)
                    for mode in gains:
                        gain = aligned(score["arms"][mode]["D"], condition) - suppressed
                        gains[mode].append(gain)
                        condition_metrics[condition][f"{mode}_gain"] = gain
                mean_loss = float(np.mean(losses))
                row = {
                    "base_problem_id": base,
                    "example_id": str(result["example_id"]),
                    "cohort_role": role,
                    "coordinate": coordinate,
                    "tpre_generated_index": int(target["tpre_generated_index"]),
                    "tpre_token_id": int(target["tpre_token_id"]),
                    "tpre_token_text": target["tpre_token_text"],
                    "lexical_semantic_class": token["lexical_semantic_class"],
                    "visual_alignment": token["visual_alignment"],
                    "structural_role": token["structural_role"],
                    "reasoning_role": token["reasoning_role"],
                    "suppression_loss": mean_loss,
                    "condition_metrics": condition_metrics,
                    "selection_used_attention": False,
                }
                for mode, values in gains.items():
                    gain = float(np.mean(values))
                    row[f"{mode}_gain"] = gain
                    row[f"RR_{mode}"] = None if mean_loss == 0 else gain / mean_loss
                rows.append(row)
    rows.sort(key=lambda row: (row["cohort_role"], int(row["base_problem_id"]), row["coordinate"]))
    write_jsonl(OUT / "phase_a_tpre/per_base_tpre_rescue.jsonl", rows)
    for mode, filename in (("K", "k_only_results.jsonl"), ("V", "v_only_results.jsonl"), ("KV", "kv_results.jsonl")):
        write_jsonl(OUT / f"phase_a_tpre/{filename}", [
            {key: value for key, value in row.items() if key not in {"K_gain", "V_gain", "KV_gain", "RR_K", "RR_V", "RR_KV"}} | {"gain": row[f"{mode}_gain"], "RR": row[f"RR_{mode}"]}
            for row in rows
        ])

    fresh = [row for row in rows if row["cohort_role"] == "fresh"]
    type_statistics: dict[str, Any] = {"minimum_class_observations": 12, "coordinates": {}}
    for coordinate in sorted({row["coordinate"] for row in fresh}):
        coordinate_rows = [row for row in fresh if row["coordinate"] == coordinate]
        type_statistics["coordinates"][coordinate] = {}
        for mode in ("K", "V", "KV"):
            summaries = {}
            classes = sorted({row["lexical_semantic_class"] for row in coordinate_rows})
            for token_class in classes:
                selected = [row for row in coordinate_rows if row["lexical_semantic_class"] == token_class]
                values = {row["base_problem_id"]: float(row[f"{mode}_gain"]) for row in selected}
                summary = inferential_summary(values)
                summary["median_RR"] = float(np.median([row[f"RR_{mode}"] for row in selected if row[f"RR_{mode}"] is not None])) if any(row[f"RR_{mode}"] is not None for row in selected) else None
                summary["inferentially_eligible"] = len(values) >= 12
                summaries[token_class] = summary
            eligible = [name for name in classes if summaries[name]["inferentially_eligible"]]
            adjusted = holm_adjust([summaries[name]["wilcoxon_p"] for name in eligible])
            for name, p_value in zip(eligible, adjusted):
                summaries[name]["holm_p"] = p_value
                summaries[name]["robust_positive"] = robust_positive(summaries[name])
            for name in set(classes) - set(eligible):
                summaries[name]["holm_p"] = None
                summaries[name]["robust_positive"] = False
            type_statistics["coordinates"][coordinate][mode] = summaries
    type_statistics["visual_alignment_coordinates"] = {}
    for coordinate in sorted({row["coordinate"] for row in fresh}):
        coordinate_rows = [row for row in fresh if row["coordinate"] == coordinate]
        type_statistics["visual_alignment_coordinates"][coordinate] = {}
        for mode in ("K", "V", "KV"):
            summaries = {}
            alignments = sorted({row["visual_alignment"] for row in coordinate_rows})
            for alignment in alignments:
                selected = [row for row in coordinate_rows if row["visual_alignment"] == alignment]
                values = {row["base_problem_id"]: float(row[f"{mode}_gain"]) for row in selected}
                summary = inferential_summary(values)
                summary["median_RR"] = float(np.median([
                    row[f"RR_{mode}"] for row in selected if row[f"RR_{mode}"] is not None
                ])) if any(row[f"RR_{mode}"] is not None for row in selected) else None
                summary["inferentially_eligible"] = len(values) >= 12
                summaries[alignment] = summary
            eligible = [name for name in alignments if summaries[name]["inferentially_eligible"]]
            adjusted = holm_adjust([summaries[name]["wilcoxon_p"] for name in eligible])
            for name, p_value in zip(eligible, adjusted):
                summaries[name]["holm_p"] = p_value
                summaries[name]["robust_positive"] = robust_positive(summaries[name])
            for name in set(alignments) - set(eligible):
                summaries[name]["holm_p"] = None
                summaries[name]["robust_positive"] = False
            type_statistics["visual_alignment_coordinates"][coordinate][mode] = summaries
    gate_summaries = {}
    coordinate_names = sorted({row["coordinate"] for row in fresh})
    for coordinate in coordinate_names:
        values = {row["base_problem_id"]: float(row["KV_gain"]) for row in fresh if row["coordinate"] == coordinate}
        gate_summaries[coordinate] = inferential_summary(values)
    adjusted = holm_adjust([gate_summaries[name]["wilcoxon_p"] for name in coordinate_names])
    for name, p_value in zip(coordinate_names, adjusted):
        gate_summaries[name]["holm_p"] = p_value
        gate_summaries[name]["robust_positive"] = robust_positive(gate_summaries[name])
    type_statistics["overall_kv_gate"] = gate_summaries
    write_json(OUT / "phase_a_tpre/token_type_statistics.json", type_statistics)

    prior = {str(row["base_problem_id"]): row for path in sorted((ROOT / "outputs/stage3c7/raw/primary").glob("**/examples/*/result.json")) for row in [read_json(path)]}
    reproduction = []
    historical_raw = {str(row["base_problem_id"]): row for row in results(args.historical_root)}
    for base, current in historical_raw.items():
        old = prior[base]
        for coordinate, target in current["coordinates"].items():
            old_target = old["target_results"][coordinate]
            for condition in ("O", "C"):
                now = target["conditions"][condition]
                before = old_target["conditions"][condition]
                reproduction.append({
                    "base_problem_id": base,
                    "coordinate": coordinate,
                    "condition": condition,
                    "native_exact": exact(now["native"], before["native"]),
                    "suppressed_exact": exact(now["suppressed"], before["suppressed"]),
                    "K_exact": exact(now["arms"]["K"], before["arms"]["C2_K"]),
                    "V_exact": exact(now["arms"]["V"], before["arms"]["C3_V"]),
                    "KV_exact": exact(now["arms"]["KV"], before["arms"]["C4_KV"]),
                })
    write_json(OUT / "analysis/historical_vs_fresh_replication.json", {
        "historical_reproduction_rows": reproduction,
        "historical_exact": bool(reproduction) and all(all(value for key, value in row.items() if key.endswith("_exact")) for row in reproduction),
        "historical_count": len(historical_raw),
        "fresh_count": len({row["base_problem_id"] for row in fresh}),
        "fresh_overall_kv": gate_summaries,
    })
    print(json.dumps({"rows": len(rows), "fresh": len({row['base_problem_id'] for row in fresh}), "historical_exact": bool(reproduction) and all(all(value for key, value in row.items() if key.endswith('_exact')) for row in reproduction)}, indent=2))


if __name__ == "__main__":
    main()
