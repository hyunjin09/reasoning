#!/usr/bin/env python3
"""Freeze an outcome/attention-blind Stage 3B.8 discovery expansion batch."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from visual_reasoning.stage0.data import load_mathverse_rows
from visual_reasoning.stage0.io import write_json, write_jsonl


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b8/discovery_cohort"


SPECS = {
    "361": ("observer separation is 29 m", "observer separation is 39 m", "12", "two-angle tangent equations remain valid"),
    "362": ("aircraft altitude is 12 m", "aircraft altitude is 18 m", "344", "right-triangle tangent relation remains valid"),
    "363": ("left flag-pole height is 13 m", "left flag-pole height is 10 m", "22.5", "string spans the unchanged 21 m separation and changed height difference"),
    "364": ("tower height is 35.5 m", "tower height is 45.5 m", "80.08", "right-triangle cable problem remains valid"),
    "365": ("aircraft altitude is 10369 m", "aircraft altitude is 12000 m", "27.1", "right-triangle inverse-tangent problem remains valid"),
    "366": ("longer sight line is 37 m", "longer sight line is 40 m", "8.8 m", "nested right triangles remain valid"),
    "367": ("mountain base width is 10.6 m", "mountain base width is 12 m", "5.0", "symmetric mountain tangent construction remains valid"),
    "371": ("short leg is 11", "short leg is 8", "16", "30-60-90 triangle remains valid"),
    "373": ("side opposite 30 degrees is 8.5", "side opposite 30 degrees is 6", "12", "30-60-90 triangle remains valid"),
    "377": ("hypotenuse is 9", "hypotenuse is 12", "6\\sqrt{3}", "30-60-90 triangle remains valid"),
    "379": ("slanted side is 8", "slanted side is 6", "4+3\\sqrt{3}", "rectangle-plus-right-triangle decomposition remains valid"),
    "387": ("circle radius is 8 cm", "circle radius is 12 cm", "75.40 cm", "circle remains valid"),
    "389": ("circle diameter is 13 cm", "circle diameter is 16 cm", "50.27 cm", "circle remains valid"),
    "390": ("circumference is 44 cm", "circumference is 66 cm", "10.50", "radius-from-circumference problem remains valid"),
    "392": ("sector radius is 10 mm", "sector radius is 12 mm", "42.8 mm", "same sector geometry remains valid"),
    "393": ("circle radius is 6 cm", "circle radius is 8 cm", "201.1 cm^2", "circle remains valid"),
    "394": ("sector radius is 2 cm", "sector radius is 4 cm", "37.7 cm^2", "same sector geometry remains valid"),
    "395": ("circle radius is 3 cm", "circle radius is 5 cm", "25\\pi cm^2", "circle remains valid"),
    "396": ("circle radius is 11 cm", "circle radius is 7 cm", "49\\pi cm^2", "circle remains valid"),
    "397": ("circle radius is 50 cm", "circle radius is 25 cm", "625\\pi cm^2", "circle remains valid"),
}


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, required=True)
    args = parser.parse_args()
    sentinels = [OUT / "candidate_screening_batch2.jsonl", OUT / "prospective_generation_manifest_batch2.jsonl"]
    if any(path.exists() for path in sentinels):
        raise FileExistsError("Stage 3B.8 discovery batch 2 is already frozen")
    split = json.loads((ROOT / "outputs/stage3b8/config/discovery_confirmation_split.json").read_text(encoding="utf-8"))
    protected = set(split["primary_confirmation"]["base_problem_ids"])
    protected.update(split["protected_diagnostic"]["old_stage3b7_base_problem_ids"])
    protected.update(split["protected_diagnostic"]["stage3b7r_base_problem_ids"])
    protected.update(str(row["base_problem_id"]) for row in read_jsonl(OUT / "initial_generation_manifest.jsonl"))
    selected = set(SPECS)
    if selected & protected:
        raise RuntimeError("Stage 3B.8 batch 2 overlaps a protected or prior discovery base")
    vision = {
        int(row["problem_index"]): row
        for row in load_mathverse_rows(args.dataset_root)
        if str(row["problem_version"]) == "Vision Dominant"
    }
    available = [base for base in range(361, 398) if base in vision]
    if not {int(value) for value in selected} <= set(available):
        raise RuntimeError("A frozen Stage 3B.8 candidate is unavailable")
    frozen_at = datetime.now(timezone.utc).isoformat()
    screening, manifest, exclusions = [], [], []
    for base in available:
        row = vision[base]
        chosen = str(base) in selected
        item = {
            "base_problem_id": str(base),
            "example_id": str(row["sample_index"]),
            "variant": "Vision Dominant",
            "screening_range": [361, 397],
            "question": row["question"],
            "ground_truth_answer": row["answer"],
            "image_reference": row["image"],
            "selected_for_edit_validation": chosen,
            "selection_used_attention": False,
            "selection_used_generation_outcome": False,
            "selection_used_stage3b8_outcome_or_fit": False,
            "frozen_at": frozen_at,
        }
        if chosen:
            fact_o, fact_c, answer_c, validity = SPECS[str(base)]
            item.update({
                "screening_decision": "prospective_discovery_batch_2",
                "original_fact": fact_o,
                "counterfactual_fact": fact_c,
                "counterfactual_expected_answer": answer_c,
                "semantic_validity_basis": validity,
                "edit_tier": "tier1_local_numeric_label",
            })
            manifest.append({
                "base_problem_id": str(base),
                "example_id": str(row["sample_index"]),
                "variant": "Vision Dominant",
                "selection_reason": "localized numeric evidence with prospectively verified counterfactual validity",
                "selection_used_attention": False,
                "generation_outcome_inspected": False,
                "stage3b8_outcomes_inspected": False,
            })
        else:
            reason = "not selected in bounded screen: redundant or less clean single-label edit"
            item.update({"screening_decision": "not_selected_batch_2", "reason": reason})
            exclusions.append({
                "base_problem_id": str(base),
                "example_id": str(row["sample_index"]),
                "stage": "prospective_visual_screen_batch_2",
                "reason": reason,
                "attention_inspected": False,
                "generation_outcome_inspected": False,
                "stage3b8_outcomes_inspected": False,
                "frozen_at": frozen_at,
            })
        screening.append(item)
    write_jsonl(OUT / "candidate_screening_batch2.jsonl", screening)
    write_jsonl(OUT / "prospective_generation_manifest_batch2.jsonl", manifest)
    write_jsonl(OUT / "exclusion_log_batch2.jsonl", exclusions)
    write_json(ROOT / "outputs/stage3b8/config/discovery_expansion_batch2.json", {
        "frozen_at": frozen_at,
        "screening_range": [361, 397],
        "screened": len(screening),
        "selected": len(manifest),
        "selected_bases": sorted(selected, key=int),
        "selection_blinding": {
            "attention_inspected": False,
            "batch1_generation_outcomes_inspected": False,
            "stage3b8_causal_or_fit_outcomes_exist_or_were_inspected": False,
        },
    })
    print(json.dumps({"screened": len(screening), "selected": len(manifest), "bases": sorted(selected, key=int)}, indent=2))


if __name__ == "__main__":
    main()
