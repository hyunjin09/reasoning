#!/usr/bin/env python3
"""Freeze the authorized Stage 3B.3-R 41-base primary protocol before scoring."""

from __future__ import annotations

import json
import runpy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b3_redesign"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def script_constant(name: str, constant: str) -> Any:
    return runpy.run_path(str(ROOT / "scripts/stage3a" / name))[constant]


def numeric_render_specs() -> dict[str, dict[str, Any]]:
    specs: dict[str, dict[str, Any]] = {}
    for row in script_constant("prepare_existing_edits.py", "SPECS"):
        specs[str(row["base"])] = {
            "roi_xyxy": row["roi"], "font_size": row["font"],
            "text_anchor": row["anchor"], "background_mode": None,
            "background_color": [255, 255, 255], "source_spec": "prepare_existing_edits.py",
        }
    for base, row in script_constant("prepare_expansion_edits.py", "SPECS").items():
        specs[str(base)] = {
            "roi_xyxy": row["roi"], "font_size": row["font"],
            "text_anchor": [2, 1], "background_mode": "roi_bright_median",
            "background_color": [255, 255, 255], "source_spec": "prepare_expansion_edits.py",
        }
    for base, row in script_constant("repair_expansion_edits_v2.py", "REPAIRS").items():
        if str(base) in specs:
            specs[str(base)].update({
                "roi_xyxy": row["roi"], "font_size": row["font"],
                "source_spec": "repair_expansion_edits_v2.py",
            })
    for base, row in script_constant("prepare_backup_edits.py", "SPECS").items():
        specs[str(base)] = {
            "roi_xyxy": row["roi"], "font_size": row["font"],
            "text_anchor": [2, 1], "background_mode": "roi_bright_median",
            "background_color": [255, 255, 255], "source_spec": "prepare_backup_edits.py",
        }
    for base, row in script_constant("repair_backup_edits_v2.py", "REPAIRS").items():
        if str(base) in specs:
            specs[str(base)].update({
                "roi_xyxy": row["roi"], "font_size": row["font"],
                "original_text_override": row["old"],
                "counterfactual_text_override": row["new"],
                "source_spec": "repair_backup_edits_v2.py",
            })
    for base, row in script_constant("prepare_round3_edits.py", "SPECS").items():
        specs[str(base)] = {
            "roi_xyxy": row["roi"], "font_size": row["font"],
            "text_anchor": [2, 1], "background_mode": "roi_bright_median",
            "background_color": [255, 255, 255], "source_spec": "prepare_round3_edits.py",
        }
    for base, row in script_constant("repair_round3_edits_v2.py", "REPAIRS").items():
        if str(base) in specs:
            specs[str(base)].update({
                "roi_xyxy": row["roi"], "font_size": row["font"],
                "source_spec": "repair_round3_edits_v2.py",
            })
    specs["751"] = {
        "roi_xyxy": [211, 15, 251, 43], "font_size": 20,
        "text_anchor": [3, 1], "background_mode": "roi_bright_median",
        "background_color": [255, 255, 255], "source_spec": "prepare_additional_existing_edit.py",
    }
    return specs


def main() -> None:
    decision = json.loads((OUT / "validation/validation_decision.json").read_text(encoding="utf-8"))
    if decision["decision"] != "PASS" or not decision["primary_41_authorized"]:
        raise RuntimeError("Primary protocol requires a frozen validation PASS")
    primary_path = OUT / "primary/primary_41_manifest.jsonl"
    if primary_path.exists():
        raise FileExistsError(f"Refusing to overwrite frozen primary manifest: {primary_path}")
    ensure_directory(primary_path.parent)
    primary = read_jsonl(OUT / "config/reserved_primary_manifest.jsonl")
    if len(primary) != 41 or len({str(row["base_problem_id"]) for row in primary}) != 41:
        raise RuntimeError("Reserved primary manifest is not the expected 41 independent bases")
    numeric = [row for row in primary if row["edit_tier"] == "tier1_local_numeric_label"]
    structural = [row for row in primary if row["edit_tier"] == "tier3_structural_visual_edit"]
    if len(numeric) != 37 or len(structural) != 4:
        raise RuntimeError("Expected 37 numeric and 4 structural primary bases")
    all_specs = numeric_render_specs()
    numeric_ids = {str(row["base_problem_id"]) for row in numeric}
    missing = numeric_ids - set(all_specs)
    if missing:
        raise RuntimeError(f"Missing final Stage 3A render specs for primary bases: {sorted(missing)}")
    frozen_specs = {}
    for row in numeric:
        base = str(row["base_problem_id"])
        spec = dict(all_specs[base])
        roi = [int(value) for value in row["target_evidence_roi_xyxy"]]
        if [int(value) for value in spec["roi_xyxy"]] != roi:
            raise RuntimeError(f"Recovered Stage 3A ROI mismatch for base {base}: {spec['roi_xyxy']} vs {roi}")
        spec.update({
            "base_problem_id": base,
            "roi_xyxy": roi,
            "counterfactual_sham_anchor": [int(spec["text_anchor"][0]) + 1, int(spec["text_anchor"][1])],
            "text_color": [0, 0, 0],
            "source_stage3a_description": row["edit_description"],
        })
        frozen_specs[base] = spec
    frozen_at = datetime.now(timezone.utc).isoformat()
    protocol = {
        "frozen_at": frozen_at,
        "authorization": "outputs/stage3b3_redesign/validation/validation_decision.json: PASS",
        "independent_unit": "base_problem_id",
        "primary_base_count": 41,
        "numeric_base_count": 37,
        "structural_base_count": 4,
        "coordinates": ["Ed_minus_1", "Ed"],
        "seed": 1234,
        "model": "Qwen3-VL-4B-Thinking",
        "required_gpu_class": "A5000",
        "attention_path": "validated eager local override",
        "arms": [
            "no_switch and all-layer Stage 3B.2 controls",
            "six coarse selective layer-window switches",
            "paired O/O_sham/C/C_sham semantic restoration on 37 numeric bases",
            "six lower-prefix and six upper-suffix cumulative source switches",
            "current-position residual patching after layers 5,11,17,23,29,35",
        ],
        "structural_restoration": "omitted prospectively; structural bases retain selective/cumulative/residual arms",
        "coarse_windows": "outputs/stage3b3/config/coarse_layer_windows.json",
        "fine_rule": "outputs/stage3b3/config/fine_localization_rule.json",
        "fine_selection_uses_validation_results": False,
        "selection_used_attention": False,
        "validation_bases_excluded_from_primary": True,
        "necessity_claims_allowed_only_for_validated numeric restoration arm": True,
        "prohibited": [
            "attention-vs-MLP decomposition", "head/path analysis", "ROI-specific switching",
            "Q/R carrier tracing", "multi-evidence analysis", "correct-vs-wrong analysis",
        ],
    }
    write_jsonl(primary_path, primary)
    write_json(OUT / "config/primary_protocol.json", protocol)
    write_json(OUT / "config/primary_render_specs.json", frozen_specs)
    print(json.dumps({
        "frozen_at": frozen_at,
        "primary_bases": len(primary),
        "numeric_restoration_bases": len(numeric),
        "structural_without_restoration": [str(row["base_problem_id"]) for row in structural],
    }, indent=2))


if __name__ == "__main__":
    main()
