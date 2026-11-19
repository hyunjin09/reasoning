#!/usr/bin/env python3
"""Validate the mandatory three-base Stage 3B.2 source-switch smoke gate."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.io import write_json


ROOT = Path(__file__).resolve().parents[2]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def evaluate_smoke(rows: list[dict[str, Any]]) -> dict[str, Any]:
    ratios = [
        abs(float(row["ed_sham_switch_effect"])) / abs(float(row["ed_target_switch_effect"]))
        if float(row["ed_target_switch_effect"]) != 0.0
        else float("inf")
        for row in rows
    ]
    criteria = [
        ("three_numeric_bases", len(rows) == 3),
        ("capture_all_layers_valid", bool(rows) and all(row["capture_all_layers_valid"] for row in rows)),
        ("stage3a_divergent_tails_exact", bool(rows) and all(row["stage3a_divergent_tail_exact"] for row in rows)),
        ("all_switch_boundaries_and_layers_valid", bool(rows) and all(row["all_checkpoint_switch_audits_valid"] for row in rows)),
        ("self_switches_exact", bool(rows) and all(row["all_self_switches_exact"] for row in rows)),
        ("all_scores_finite", bool(rows) and all(row["all_finite"] for row in rows)),
        ("deterministic_O_to_C_at_Ed", bool(rows) and all(row["ed_O_to_C_deterministic_exact"] for row in rows)),
        ("condition_prompt_and_visual_layout_exact", bool(rows) and all(row["condition_prompt_visual_layout_exact"] for row in rows)),
        ("each_Ed_sham_smaller_than_target", bool(rows) and all(row["ed_sham_smaller_than_target"] for row in rows)),
        ("median_Ed_absolute_sham_to_target_ratio_at_most_0.25", bool(ratios) and statistics.median(ratios) <= 0.25),
    ]
    return {
        "status": "PASS" if all(passed for _, passed in criteria) else "FAIL",
        "criterion_count": len(criteria),
        "criteria": [{"name": name, "status": "PASS" if passed else "FAIL"} for name, passed in criteria],
        "base_problem_ids": [str(row["base_problem_id"]) for row in rows],
        "ed_absolute_sham_to_target_ratios": ratios,
        "median_ed_absolute_sham_to_target_ratio": statistics.median(ratios) if ratios else None,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, required=True)
    args = parser.parse_args()
    raw_dir = args.raw_dir.resolve()
    raw_dir.relative_to((ROOT / "outputs/stage3b2/raw/smoke").resolve())
    rows = read_jsonl(raw_dir / "smoke_results.jsonl")
    result = evaluate_smoke(rows)
    smoke_dir = ROOT / "outputs/stage3b2/smoke"
    write_json(smoke_dir / "visual_source_switch_validation.json", result)
    integrity = {
        "status": result["status"],
        "all_36_layers_captured_and_switched": all(row["capture_all_layers_valid"] and row["all_checkpoint_switch_audits_valid"] for row in rows),
        "all_nonvisual_Q_P_R_key_value_entries_unchanged_by_construction_and_audit": all(row["all_checkpoint_switch_audits_valid"] for row in rows),
        "all_self_sources_transparent": all(row["all_self_switches_exact"] for row in rows),
        "all_stage3a_divergent_suffix_scores_exact": all(row["stage3a_divergent_tail_exact"] for row in rows),
        "switch_definition": "only visual-position post-RoPE K and projected V are substituted in the eager attention input for the query predicting y_k and later queries",
        "base_problem_ids": result["base_problem_ids"],
    }
    write_json(smoke_dir / "cache_integrity_diagnostics.json", integrity)
    lines = [
        "# Stage 3B.2 visual-source switch smoke validation",
        "",
        f"Overall: **{result['status']}**",
        "",
        f"Bases: {', '.join(result['base_problem_ids'])}",
        "",
        "| Criterion | Status |",
        "|---|---|",
    ]
    lines.extend(f"| {row['name']} | {row['status']} |" for row in result["criteria"])
    lines.extend(
        [
            "",
            f"Median absolute E_d sham/target ratio: {result['median_ed_absolute_sham_to_target_ratio']:.6f}",
            "",
            "The smoke gate validates mechanics only. Target switch effects are not treated as cohort-level scientific evidence.",
        ]
    )
    (smoke_dir / "visual_source_switch_validation.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
