#!/usr/bin/env python3
"""Aggregate Stage 3C8 bidirectional prompt/question carrier results."""

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
PAIRS = ("O_to_C", "C_to_O")


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


def aggregate_patch(patches: dict[str, Any]) -> tuple[float, float, float, dict[str, Any]]:
    gains, references, ratios, details = [], [], [], {}
    for pair in PAIRS:
        row = patches[pair]
        recipient, source = float(row["recipient_D"]), float(row["source_D"])
        difference = source - recipient
        direction = 1.0 if difference >= 0 else -1.0
        gain = float(row["D_shift"]) * direction
        reference = abs(difference)
        ratio = None if reference == 0 else gain / reference
        gains.append(gain)
        references.append(reference)
        if ratio is not None:
            ratios.append(ratio)
        details[pair] = {"directional_gain": gain, "reference_gap": reference, "CRR": ratio}
    return float(np.mean(gains)), float(np.mean(references)), float(np.mean(ratios)) if ratios else float("nan"), details


def main() -> None:
    args = parse_args()
    annotations = read_jsonl(args.annotations)
    annotation_lookup = {
        (str(row["base_problem_id"]), int(row["absolute_sequence_position"])): row
        for row in annotations if row["stream"] in {"PROMPT_QUESTION", "SPECIAL_CONTROL"}
    }
    full_rows, position_rows, span_rows, group_rows = [], [], [], []
    for role, root in (("historical", args.historical_root), ("fresh", args.fresh_root)):
        raw = results(root)
        expected = 24 if role == "historical" else len(read_jsonl(OUT / "cohort/fresh_atlas_manifest.jsonl"))
        if len(raw) != expected:
            raise RuntimeError(f"Phase-C {role} result count mismatch: {len(raw)}/{expected}")
        for result in raw:
            base = str(result["base_problem_id"])
            gain, reference, ratio, details = aggregate_patch(result["full_q"])
            full_rows.append({
                "base_problem_id": base,
                "cohort_role": role,
                "gain": gain,
                "reference_gap": reference,
                "CRR": None if not np.isfinite(ratio) else ratio,
                "bidirectional_metrics": details,
            })
            for position, patches in result["per_prompt_position"].items():
                annotation = annotation_lookup[(base, int(position))]
                gain, reference, ratio, details = aggregate_patch(patches)
                position_rows.append({
                    "base_problem_id": base,
                    "cohort_role": role,
                    "position": int(position),
                    "relative_eligible_position": result["eligible_nonvisual_prompt_positions"].index(int(position)),
                    "token_id": int(annotation["token_id"]),
                    "token_text": annotation["decoded_text"],
                    "stream": annotation["stream"],
                    "token_class": annotation["lexical_semantic_class"],
                    "visual_alignment": annotation["visual_alignment"],
                    "structural_role": annotation["structural_role"],
                    "gain": gain,
                    "reference_gap": reference,
                    "CRR": None if not np.isfinite(ratio) else ratio,
                    "bidirectional_metrics": details,
                })
            span_lookup = {str(row["span_id"]): row for row in result["prompt_spans"]}
            for span_id, patches in result["prompt_span_rescue"].items():
                span = span_lookup[span_id]
                gain, reference, ratio, details = aggregate_patch(patches)
                span_rows.append({
                    "base_problem_id": base,
                    "cohort_role": role,
                    "span_id": span_id,
                    "stream": span["stream"],
                    "decoded_text": span["decoded_text"],
                    "absolute_positions": span["absolute_positions"],
                    "token_count": len(span["absolute_positions"]),
                    "token_class": span["lexical_semantic_class"],
                    "gain": gain,
                    "reference_gap": reference,
                    "CRR": None if not np.isfinite(ratio) else ratio,
                    "bidirectional_metrics": details,
                })
            for group, patches in result["prompt_type_group_rescue"].items():
                gain, reference, ratio, details = aggregate_patch(patches)
                group_rows.append({
                    "base_problem_id": base,
                    "cohort_role": role,
                    "group": group,
                    "gain": gain,
                    "reference_gap": reference,
                    "CRR": None if not np.isfinite(ratio) else ratio,
                    "bidirectional_metrics": details,
                })
    order = lambda row: (row["cohort_role"], int(row["base_problem_id"]))
    full_rows.sort(key=order)
    position_rows.sort(key=lambda row: (*order(row), row["position"]))
    span_rows.sort(key=lambda row: (*order(row), row["absolute_positions"][0]))
    group_rows.sort(key=lambda row: (*order(row), row["group"]))
    write_jsonl(OUT / "phase_c_prompt/full_q_reference.jsonl", full_rows)
    write_jsonl(OUT / "phase_c_prompt/per_prompt_position_rescue.jsonl", position_rows)
    write_jsonl(OUT / "phase_c_prompt/prompt_span_rescue.jsonl", span_rows)
    write_jsonl(OUT / "phase_c_prompt/prompt_type_group_rescue.jsonl", group_rows)

    fresh_groups = [row for row in group_rows if row["cohort_role"] == "fresh"]
    statistics = {}
    classes = sorted({row["group"] for row in fresh_groups})
    for token_class in classes:
        values = {row["base_problem_id"]: float(row["gain"]) for row in fresh_groups if row["group"] == token_class}
        summary = inferential_summary(values)
        summary["inferentially_eligible"] = len(values) >= 12
        statistics[token_class] = summary
    eligible = [name for name in classes if statistics[name]["inferentially_eligible"]]
    adjusted = holm_adjust([statistics[name]["wilcoxon_p"] for name in eligible])
    for name, p_value in zip(eligible, adjusted):
        statistics[name]["holm_p"] = p_value
        statistics[name]["robust_positive"] = robust_positive(statistics[name])
    for name in set(classes) - set(eligible):
        statistics[name]["holm_p"] = None
        statistics[name]["robust_positive"] = False
    full_summary = inferential_summary({row["base_problem_id"]: float(row["gain"]) for row in full_rows if row["cohort_role"] == "fresh"})
    full_summary["holm_p"] = full_summary["wilcoxon_p"]
    full_summary["robust_positive"] = robust_positive(full_summary)
    write_json(OUT / "phase_c_prompt/token_type_statistics.json", {
        "phase_c_prompt_type_groups": statistics,
        "full_q_positive_reference": full_summary,
    })
    gated_classes = [name for name in classes if name.startswith("lexical:") and statistics[name]["robust_positive"]]
    write_json(OUT / "config/phase_c_kv_gate.json", {
        "run": bool(gated_classes),
        "gated_token_classes": gated_classes,
        "criterion": "fresh K+V group transfer meets Holm, bootstrap-CI, and positive-fraction rule",
        "selected_before_K_or_V_group_scores": True,
    })

    fresh_positions = [row for row in position_rows if row["cohort_role"] == "fresh"]
    controls = []
    for base in sorted({row["base_problem_id"] for row in fresh_positions}, key=int):
        rows = [row for row in fresh_positions if row["base_problem_id"] == base and row["stream"] == "PROMPT_QUESTION"]
        for focal_rule, focal in (
            ("target_aligned", [row for row in rows if row["visual_alignment"] == "TARGET_ALIGNED"]),
            ("function_word", [row for row in rows if row["token_class"] == "FUNCTION_WORD"]),
            ("punctuation", [row for row in rows if row["token_class"] == "PUNCTUATION"]),
        ):
            candidates = [row for row in rows if row not in focal]
            for row in focal:
                if not candidates:
                    continue
                control = min(candidates, key=lambda other: (abs(other["position"] - row["position"]), other["position"]))
                controls.append({
                    "base_problem_id": base,
                    "comparison": focal_rule,
                    "focal_position": row["position"],
                    "focal_gain": row["gain"],
                    "control_position": control["position"],
                    "control_class": control["token_class"],
                    "control_gain": control["gain"],
                    "gain_difference": float(row["gain"] - control["gain"]),
                })
    write_jsonl(OUT / "phase_c_prompt/structural_controls.jsonl", controls)
    write_json(OUT / "analysis/visual_alignment_analysis.json", {
        "prompt_structural_controls": controls,
        "matching": "within-base nearest question position; descriptive unless class-level base N>=12",
    })
    print(json.dumps({"full_q": len(full_rows), "positions": len(position_rows), "groups": len(group_rows), "gated_kv_classes": gated_classes}, indent=2))


if __name__ == "__main__":
    main()
