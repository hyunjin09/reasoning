#!/usr/bin/env python3
"""Materialize frozen A5000 bridge references before A6000 scoring."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from visual_reasoning.a6000_calibration.metrics import validate_calibration_cohort
from visual_reasoning.a6000_calibration.protocol import extract_a5000_reference, target_cell_id


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/a6000_calibration"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, allow_nan=False) + "\n" for row in rows), encoding="utf-8")


def unique(rows: list[dict[str, Any]], key: tuple[str, str]) -> dict[str, Any]:
    matches = [row for row in rows if (str(row["base_problem_id"]), str(row.get("target_id"))) == key]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one historical row for {key}; got {len(matches)}")
    return matches[0]


def unique_cell(rows: list[dict[str, Any]], key: tuple[str, str]) -> dict[str, Any]:
    matches = [row for row in rows if (str(row["base_problem_id"]), str(row["cell_id"])) == key]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one historical ROI row for {key}; got {len(matches)}")
    return matches[0]


def main() -> None:
    cohort = read_json(OUT / "config/calibration_cohort.json")
    audit = validate_calibration_cohort(cohort)
    if not audit["passed"]:
        raise RuntimeError(f"Frozen calibration cohort is invalid: {audit}")
    kv_rows = read_jsonl(ROOT / "outputs/stage3c7/phase_a_cache/kv_results.jsonl")
    residual_rows = read_jsonl(ROOT / "outputs/stage3c7/phase_b_joint/residual_only_results.jsonl")
    target_rows = read_jsonl(ROOT / "outputs/stage3b7r/scoring/target_roi_results.jsonl")
    irrelevant_rows = read_jsonl(ROOT / "outputs/stage3b7r/scoring/irrelevant_roi_results.jsonl")
    references = []
    for cell in cohort["cells"]:
        base, target = str(cell["base_problem_id"]), str(cell["target_id"])
        cell_id = target_cell_id(target)
        references.append(extract_a5000_reference(
            cell,
            kv_row=unique(kv_rows, (base, target)),
            residual_row=unique(residual_rows, (base, target)),
            target_roi_row=unique_cell(target_rows, (base, cell_id)),
            irrelevant_roi_row=unique_cell(irrelevant_rows, (base, cell_id)),
        ))
    write_jsonl(OUT / "layer_c_bridge/a5000_reference_scores.jsonl", references)
    tolerances = read_json(OUT / "config/tolerances.json")
    write_json(OUT / "layer_c_bridge/hardware_sensitive_band.json", {
        "frozen_before_a6000_scoring": True,
        "definition": "hardware-sensitive when absolute effect magnitude is <= the frozen band",
        "band_nats_per_token": tolerances["hardware_sensitive_effect_magnitude_max"],
        "source": tolerances["hardware_sensitive_band_source"],
        "stage3c9_classification_floor": tolerances["stage3c9_classification_floor_unchanged"],
        "changes_stage3c9_thresholds": False,
        "excludes_future_examples": False,
    })
    write_json(OUT / "config/cohort_validation.json", audit)
    print(json.dumps({"reference_rows": len(references), "cohort_validation": audit["passed"]}))


if __name__ == "__main__":
    main()
