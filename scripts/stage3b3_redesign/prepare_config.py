#!/usr/bin/env python3
"""Freeze the Stage 3B.3-R split, paired estimand, gates, and validation render specs."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl
from visual_reasoning.stage3b3_redesign.split import freeze_method_validation_split


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b3_redesign"
SOURCE_MANIFEST = ROOT / "outputs/stage3b3/config/cohort_manifest.jsonl"
ANNOTATIONS = ROOT / "outputs/stage3b2/annotations/discriminative_event_annotations.jsonl"
SEED = 20_260_901


# These are the final manually accepted Stage 3A render parameters for the
# seeded validation bases. C_sham changes only the x anchor by one pixel and is
# independently rendered from O with the same deterministic renderer family.
VALIDATION_RENDER_SPECS = {
    "6": {"font_size": 22, "text_anchor": [2, 1]},
    "83": {"font_size": 18, "text_anchor": [2, 1]},
    "93": {"font_size": 13, "text_anchor": [2, 1]},
    "96": {"font_size": 16, "text_anchor": [2, 1]},
    "101": {"font_size": 16, "text_anchor": [2, 1]},
    "126": {"font_size": 18, "text_anchor": [2, 1]},
    "136": {"font_size": 20, "text_anchor": [2, 1]},
    "148": {"font_size": 16, "text_anchor": [1, 1]},
}


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    if OUT.exists() and any(OUT.iterdir()):
        raise FileExistsError(f"Refusing to overwrite non-empty redesign output: {OUT}")
    frozen_at = datetime.now(timezone.utc).isoformat()
    ensure_directory(OUT / "config")
    rows = read_jsonl(SOURCE_MANIFEST)
    annotations = {str(row["base_problem_id"]): row for row in read_jsonl(ANNOTATIONS)}
    exact = {
        base for base, row in annotations.items()
        if bool(row["baseline_trace_common_prefix_exact"])
    }
    split = freeze_method_validation_split(rows, exact_base_ids=exact, seed=SEED)
    validation_set = set(split["validation_base_problem_ids"])
    validation = [row for row in rows if str(row["base_problem_id"]) in validation_set]
    primary = [row for row in rows if str(row["base_problem_id"]) not in validation_set]
    if set(VALIDATION_RENDER_SPECS) != validation_set:
        raise RuntimeError("Declared validation render specs do not match the frozen seeded split")
    if len(validation) != 8 or len(primary) != 41:
        raise RuntimeError("The redesign requires an 8/41 split of the exact 49-base cohort")

    split.update({
        "frozen_at": frozen_at,
        "source_manifest": str(SOURCE_MANIFEST.relative_to(ROOT)),
        "validation_base_count": len(validation),
        "primary_reserved_base_count": len(primary),
        "validation_exact_baseline_count": sum(
            bool(annotations[str(row["base_problem_id"])]["baseline_trace_common_prefix_exact"])
            for row in validation
        ),
        "primary_exact_baseline_count": sum(
            bool(annotations[str(row["base_problem_id"])]["baseline_trace_common_prefix_exact"])
            for row in primary
        ),
        "selection_used_attention": False,
        "selection_used_stage3b3_redesign_scores": False,
    })
    estimand = {
        "frozen_at": frozen_at,
        "evidence_preference": "D = L_o - L_c; larger D means stronger original-fact preference",
        "recipient_histories": {
            "original_history": "fixed O input/history; default C visual source at every layer",
            "counterfactual_history": "fixed C input/history; default O visual source at every layer",
        },
        "window_variants": ["O", "O_sham", "C", "C_sham"],
        "SRC_O": "mean[D(C_outside+O_W), D(C_outside+O_sham_W)] - mean[D(C_W), D(C_outside+C_sham_W)]",
        "SRC_C": "mean[D(O_W), D(O_outside+O_sham_W)] - mean[D(O_outside+C_W), D(O_outside+C_sham_W)]",
        "BSRC": "(SRC_O + SRC_C) / 2",
        "primary_metric": "unnormalized BSRC",
        "A_render": "mean of the four within-history, within-semantic |D(render1)-D(render2)| differences",
        "coordinates": ["Ed_minus_1", "Ed"],
        "coarse_windows": "the six immutable 6-layer windows in outputs/stage3b3/config/coarse_layer_windows.json",
        "independent_unit": "base_problem_id",
    }
    gates = {
        "frozen_at": frozen_at,
        "independent_unit": "base_problem_id",
        "aggregation": (
            "identify activity per base/window/coordinate; take within-base medians across active "
            "window-coordinate rows; apply cohort medians across independent bases"
        ),
        "A_semantic_direction": {
            "required_bidirectionally_consistent_bases": 7,
            "total_bases": 8,
            "test": "one-sided exact binomial against p=0.5 must be <0.05",
            "additional_requirement": "cohort median of active-base median BSRC is >0",
        },
        "B_activity": {
            "row_definition": "abs(BSRC) >= 0.10 * abs(matching Stage 3B.2 all-layer BRI)",
            "required_active_bases": 7,
        },
        "C_relative_render": {
            "metric": "median across active bases of within-base median A_render/abs(BSRC)",
            "maximum": 0.25,
        },
        "D_absolute_render": {
            "metric": "median across active bases of within-base median A_render/abs(BRI_all-layer)",
            "maximum": 0.05,
        },
        "frozen_before_validation_scores": True,
    }
    config = {
        "frozen_at": frozen_at,
        "plan": "plan/stage3b3_redesign_plan.md",
        "source_stage3b3_failure": "outputs/stage3b3/smoke/layer_switch_validation.json",
        "source_stage3b3_failure_preserved": True,
        "source_cohort_base_count": 49,
        "validation_base_count": 8,
        "reserved_primary_base_count": 41,
        "validation_seed": SEED,
        "model": "Qwen3-VL-4B-Thinking",
        "seed": 1234,
        "required_gpu_class": "A5000",
        "attention_path": "validated eager local override",
        "validation_arms": [
            "no_switch", "all_layer_stage3b2_reproduction", "selective_six_windows",
            "paired_semantic_restoration_six_windows", "self_and_render_controls",
            "current_position_residual_patch_smoke",
        ],
        "validation_fine_localization": False,
        "structural_restoration": "omitted; eight numeric validation bases used as allowed by plan",
        "primary_status": "reserved_untouched_until_validation_decision",
        "prohibited": [
            "attention-vs-MLP decomposition", "head/path analysis", "ROI-specific switching",
            "Q/R carrier analysis", "multi-evidence analysis", "failure analysis",
        ],
    }
    render_specs = {}
    for row in validation:
        base = str(row["base_problem_id"])
        roi = [int(value) for value in row["target_evidence_roi_xyxy"]]
        spec = dict(VALIDATION_RENDER_SPECS[base])
        spec.update({
            "base_problem_id": base,
            "roi_xyxy": roi,
            "counterfactual_sham_anchor": [int(spec["text_anchor"][0]) + 1, int(spec["text_anchor"][1])],
            "text_color": [0, 0, 0],
            "background_mode": "roi_bright_median" if base not in {"136", "148"} else None,
            "background_color": [255, 255, 255],
            "source_stage3a_description": row["edit_description"],
        })
        render_specs[base] = spec

    write_json(OUT / "config/redesign_config.json", config)
    write_json(OUT / "config/validation_split.json", split)
    write_json(OUT / "config/semantic_restoration_estimand.json", estimand)
    write_json(OUT / "config/revised_gates.json", gates)
    write_json(OUT / "config/validation_render_specs.json", render_specs)
    write_jsonl(OUT / "config/validation_manifest.jsonl", validation)
    write_jsonl(OUT / "config/reserved_primary_manifest.jsonl", primary)
    print(json.dumps(split, indent=2))


if __name__ == "__main__":
    main()
