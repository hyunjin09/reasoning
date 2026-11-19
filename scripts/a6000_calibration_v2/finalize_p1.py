#!/usr/bin/env python3
"""Freeze the P1 decision after one or more stress-case processes finish."""

from __future__ import annotations

import json
from pathlib import Path

from visual_reasoning.a6000_calibration_v2.protocol import decide_p1, validate_stress_manifest


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/a6000_calibration_v2"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def main() -> None:
    manifest = [
        json.loads(line)
        for line in (OUT / "phase1_path_feasibility/stress_manifest.jsonl").read_text().splitlines()
        if line.strip()
    ]
    validate_stress_manifest(manifest)
    executed = {}
    for path in (OUT / "phase1_path_feasibility").glob("p1_stress_base*.json"):
        row = read_json(path)
        executed[str(row["base_problem_id"])] = row
    decision = decide_p1(executed.values(), expected_count=6, memory_fraction_max=0.90)
    if decision["status"] == "INCOMPLETE":
        raise RuntimeError("P1 is incomplete and has no conclusive failure")
    rows = []
    for item in manifest:
        base = str(item["base_problem_id"])
        if base in executed:
            rows.append(executed[base])
        else:
            rows.append({
                "base_problem_id": base,
                "example_id": str(item["example_id"]),
                "stress_order": int(item["stress_order"]),
                "status": "NOT_RUN_AFTER_CONCLUSIVE_P1_FAILURE",
                "reason": "P1 rejected after a legitimate frozen stress case OOM",
                "prefix_tokens": int(item["stress_prefix_token_count"]),
                "reasoning_tokens": int(item["generated_token_count"]),
                "visual_tokens": int(item["visual_token_count"]),
            })
    output = OUT / "phase1_path_feasibility/one_shot_memory_stress.jsonl"
    output.write_text("".join(json.dumps(row, allow_nan=False) + "\n" for row in rows), encoding="utf-8")
    decision.update({
        "canonical_path_status": "P2_SELECTION_REQUIRED",
        "p1_results": str(output.relative_to(ROOT)),
        "decision_basis": "memory feasibility only",
        "scientific_effects_inspected_for_decision": False,
        "stage3c9_restart_authorized": False,
    })
    write_json(OUT / "phase1_path_feasibility/path_decision.json", decision)
    write_json(OUT / "config/canonical_path_decision.json", {
        "frozen_after_p1_memory_test": True,
        "v1_status": "FAIL",
        "p1_status": decision["status"],
        "p1_failure": decision["failures"],
        "selected_branch": "P2_fixed_streaming_cached",
        "canonical_streaming_path_frozen": False,
        "selection_uses_scientific_effects": False,
        "stage3c9_restart_authorized": False,
    })


if __name__ == "__main__":
    main()
