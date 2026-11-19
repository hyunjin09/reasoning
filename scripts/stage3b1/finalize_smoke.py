#!/usr/bin/env python3
"""Validate the mandatory Stage 3B.1 three-base timing smoke gate."""

from __future__ import annotations

import json
from pathlib import Path

from visual_reasoning.stage0.io import write_json
from visual_reasoning.stage3b1.intervention import valid_cutoff_audit


ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "outputs/stage3b1/raw/smoke/validated"
OUT = ROOT / "outputs/stage3b1/smoke"


def validate_schedule_deduplication(
    smoke_rows: list[dict], schedules: dict[str, dict]
) -> bool:
    """Validate collisions where present without requiring one in every base."""

    collision_count = 0
    for row in smoke_rows:
        schedule = schedules.get(str(row["base_problem_id"]))
        if schedule is None:
            return False
        checkpoints = schedule["checkpoints"]
        expected_collisions = sum(max(0, len(point["labels"]) - 1) for point in checkpoints)
        if int(row["checkpoint_count"]) != len(checkpoints):
            return False
        if int(row["duplicate_label_count"]) != expected_collisions:
            return False
        collision_count += expected_collisions
    return collision_count > 0


def main() -> None:
    rows = [json.loads(line) for line in (RAW / "smoke_results.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    detailed_rows = [
        json.loads(line)
        for line in (RAW / "timing_results.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    schedules = {
        str(row["base_problem_id"]): row
        for row in (
            json.loads(line)
            for line in (ROOT / "outputs/stage3b1/config/checkpoint_schedule.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        )
    }
    if [str(row["base_problem_id"]) for row in rows] != ["118", "148", "113"]:
        raise RuntimeError("Smoke results do not match the frozen short/medium/long base order")
    detailed_persistence = all(
        valid_cutoff_audit(
            score["hook_audits"][candidate],
            prompt_length=int(result["prompt_token_count"]),
            prefix_token_count=int(result["e0_start_token"]),
            candidate_token_count=int(score[candidate]["token_count"]),
            cutoff_generated_index=int(timing["cutoff_generated_index"]),
            visual_indices=[int(value) for value in result["visual_token_indices"]],
            layer_count=36,
            logical_heads=32,
        )
        for result in detailed_rows
        for timing in result["timing"]
        for score in timing["condition_scores"].values()
        for candidate in ("original_candidate", "counterfactual_candidate")
    )
    criteria = {
        "three_frozen_bases_completed": len(rows) == 3,
        "no_cutoff_reproduces_stage3a_3_of_3": all(row["no_cutoff_stage3a_exact"] for row in rows),
        "generation_start_reproduces_stage3b0_3_of_3": all(
            row["generation_start_stage3b0_exact"] for row in rows
        ),
        "timed_cutoff_boundaries_valid_3_of_3": all(row["all_timed_cutoff_audits_valid"] for row in rows),
        "cutoff_persists_through_full_evidence_probe_3_of_3": detailed_persistence,
        "frozen_schedule_deduplication_valid": validate_schedule_deduplication(rows, schedules),
        "hooked_noop_transparent_3_of_3": all(row["hooked_noop_exact"] for row in rows),
        "full_sequence_eager_path_fixed_3_of_3": all(
            row["scoring_path_fixed"] == "full-sequence eager attention" for row in rows
        ),
        "finite_3_of_3": all(row["all_finite"] for row in rows),
    }
    gate = "PASS" if all(criteria.values()) else "FAIL"
    validation = {
        "gate": gate,
        "criteria": criteria,
        "per_base": rows,
        "deduplication_note": (
            "Coordinate collisions occur for bases 118 and 148 and share one exact-index score; "
            "base 113 has no coordinate collision and therefore needs no deduplication."
        ),
        "cutoff_semantics": "index c blocks query y_c and every later generated query; c=0 reproduces Stage 3B.0",
        "cohort_scoring_authorized": gate == "PASS",
    }
    write_json(OUT / "cutoff_timing_validation.json", validation)
    lines = [
        "# Stage 3B.1 cutoff-timing validation",
        "",
        f"Status: **{gate}**.",
        "",
        "The frozen smoke bases span E0 lengths 6, 72, and 908. A cutoff index `c` permits normal visual access for generated queries before `y_c`; `y_c` is the first query blocked from every frozen visual key in all 36 language layers.",
        "",
        "| Base | E0 | Checkpoints | Stage 3A exact | Stage 3B.0 exact | Timed edges valid | No-op exact | Finite |",
        "|---:|---:|---:|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['base_problem_id']} | {row['e0_start_token']} | {row['checkpoint_count']} | "
            f"{row['no_cutoff_stage3a_exact']} | {row['generation_start_stage3b0_exact']} | "
            f"{row['all_timed_cutoff_audits_valid']} | {row['hooked_noop_exact']} | {row['all_finite']} |"
        )
    lines.extend(
        [
            "",
            "Every saved timed audit explicitly records the visual-key list, first/last modified query, layer set, logical-head edge count, and zero modifications before the cutoff or during prefill. Duplicate coordinate labels share one scored exact token index.",
        ]
    )
    (OUT / "cutoff_timing_validation.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    if gate != "PASS":
        raise RuntimeError(f"Stage 3B.1 smoke gate failed: {criteria}")
    print(json.dumps(validation, indent=2))


if __name__ == "__main__":
    main()
