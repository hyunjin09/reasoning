#!/usr/bin/env python3
"""Freeze score-blind manual edit geometry for the Stage 3C.9 audit prefix."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.io import write_jsonl


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c9"


# Coordinates were selected from the Stage 3C.9 coordinate-grid review images.
# Earlier validated geometry is reused only where the same source label is being
# edited; every quartet remains subject to a fresh Stage 3C.9 manual review.
SPECS: dict[str, dict[str, Any]] = {
    "3": {"roi": [343, 610, 493, 695], "font": 78, "anchor": [2, 1], "suffix": "°"},
    "9": {"roi": [175, 225, 231, 255], "font": 22, "anchor": [2, 1], "suffix": ""},
    "10": {"roi": [126, 68, 166, 93], "font": 18, "anchor": [2, 1], "suffix": "°", "renderer": "preserve_crossing_strokes"},
    "14": {"roi": [61, 108, 114, 140], "font": 17, "anchor": [2, 1], "suffix": "°", "renderer": "preserve_crossing_strokes"},
    "29": {"roi": [214, 56, 261, 88], "font": 18, "anchor": [2, 1], "suffix": "°", "renderer": "preserve_crossing_strokes"},
    "31": {"roi": [280, 18, 330, 49], "font": 20, "anchor": [2, 1], "suffix": "°"},
    "38": {"roi": [133, 65, 179, 94], "font": 18, "anchor": [2, 1], "suffix": "°"},
    "45": {"roi": [159, 75, 206, 108], "font": 16, "anchor": [2, 1], "suffix": "°", "renderer": "preserve_crossing_strokes"},
    "56": {"roi": [114, 72, 164, 106], "font": 18, "anchor": [2, 1], "suffix": "°", "renderer": "preserve_crossing_strokes"},
    "61": {"roi": [71, 44, 120, 70], "font": 19, "anchor": [2, 1], "suffix": "°", "renderer": "preserve_crossing_strokes"},
    "67": {"roi": [73, 94, 121, 124], "font": 20, "anchor": [2, 1], "suffix": "°", "renderer": "preserve_crossing_strokes"},
    "71": {"roi": [85, 55, 130, 84], "font": 19, "anchor": [2, 1], "suffix": "°", "renderer": "preserve_crossing_strokes"},
    "73": {"roi": [70, 83, 116, 114], "font": 20, "anchor": [2, 1], "suffix": "°", "renderer": "preserve_crossing_strokes"},
    "78": {"roi": [51, 88, 86, 110], "font": 15, "anchor": [2, 1], "suffix": "°"},
    "80": {"roi": [18, 63, 43, 93], "font": 20, "anchor": [2, 1], "suffix": ""},
    "104": {"roi": [138, 36, 180, 69], "font": 20, "anchor": [1, 0], "suffix": "", "renderer": "preserve_crossing_strokes"},
    "128": {"roi": [104, 90, 153, 114], "font": 14, "anchor": [2, 1], "suffix": "°", "renderer": "preserve_crossing_strokes"},
    "129": {"roi": [58, 160, 87, 193], "font": 18, "anchor": [2, 1], "suffix": "", "renderer": "preserve_crossing_strokes"},
    "136": {"roi": [115, 212, 160, 241], "font": 20, "anchor": [2, 1], "suffix": ""},
    "140": {"roi": [190, 100, 213, 124], "font": 20, "anchor": [1, 0], "suffix": ""},
    "142": {"roi": [292, 126, 315, 158], "font": 20, "anchor": [1, 0], "suffix": ""},
    "149": {"roi": [137, 150, 175, 182], "font": 22, "anchor": [1, 0], "suffix": ""},
    "161": {"roi": [108, 63, 145, 96], "font": 18, "anchor": [3, 2], "suffix": "", "renderer": "preserve_crossing_strokes"},
    "176": {"roi": [105, 445, 190, 515], "font": 48, "anchor": [1, 0], "suffix": "", "renderer": "preserve_crossing_strokes"},
    "182": {"roi": [155, 625, 275, 705], "font": 52, "anchor": [1, 0], "suffix": "°"},
    "193": {"roi": [105, 300, 148, 347], "font": 40, "anchor": [1, 0], "suffix": ""},
    "206": {"roi": [660, 710, 770, 790], "font": 64, "anchor": [1, 0], "suffix": ""},
    "208": {"roi": [445, 445, 575, 525], "font": 64, "anchor": [2, 0], "suffix": "°"},
    "226": {"roi": [213, 164, 250, 197], "font": 22, "anchor": [1, 0], "suffix": ""},
    "243": {"roi": [445, 238, 515, 286], "font": 30, "anchor": [1, 0], "suffix": ""},
    "254": {"roi": [136, 77, 164, 107], "font": 20, "anchor": [1, 0], "suffix": "", "renderer": "preserve_crossing_strokes"},
    "331": {"roi": [168, 165, 210, 192], "font": 20, "anchor": [1, 0], "suffix": "°"},
    "332": {"roi": [156, 100, 198, 130], "font": 20, "anchor": [1, 0], "suffix": "°"},
    "350": {"roi": [283, 76, 330, 101], "font": 18, "anchor": [1, 0], "suffix": "°"},
    "353": {"roi": [124, 106, 173, 137], "font": 20, "anchor": [1, 0], "suffix": "°", "renderer": "preserve_crossing_strokes"},
    "363": {"roi": [1, 77, 73, 106], "font": 18, "anchor": [1, 0], "suffix": " m"},
    "423": {"roi": [760, 650, 950, 735], "font": 55, "anchor": [1, 0], "suffix": ""},
    "425": {"roi": [78, 43, 114, 65], "font": 16, "anchor": [1, 0], "suffix": "°"},
    "672": {"roi": [151, 268, 210, 295], "font": 22, "anchor": [1, 0], "suffix": " cm"},
    "675": {"roi": [440, 180, 530, 217], "font": 24, "anchor": [1, 0], "suffix": " cm"},
    "743": {"roi": [337, 43, 356, 68], "font": 18, "anchor": [1, 0], "suffix": ""},
    "751": {"roi": [211, 15, 251, 43], "font": 20, "anchor": [3, 1], "suffix": ""},
    "752": {"roi": [347, 130, 368, 157], "font": 18, "anchor": [1, 0], "suffix": "", "renderer": "preserve_crossing_strokes"},
    "753": {"roi": [108, 18, 132, 50], "font": 22, "anchor": [1, 0], "suffix": ""},
    "758": {"roi": [408, 87, 442, 120], "font": 26, "anchor": [1, 0], "suffix": ""},
    "762": {"roi": [143, 255, 183, 285], "font": 22, "anchor": [1, 0], "suffix": ""},
    "782": {"roi": [364, 286, 394, 323], "font": 26, "anchor": [1, 0], "suffix": ""},
    "787": {"roi": [103, 212, 133, 266], "font": 36, "anchor": [1, 0], "suffix": ""},
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    needed = read_jsonl(OUT / "cohort/work/manual_edit_specs_needed.jsonl")
    expected = {str(row["base_problem_id"]) for row in needed}
    if set(SPECS) != expected or len(SPECS) != 48:
        raise RuntimeError("Manual edit specs must exactly cover the frozen requested set")
    target = OUT / "cohort/work/manual_edit_specs.jsonl"
    combined_target = OUT / "cohort/work/all_edit_specs.jsonl"
    if target.exists() or combined_target.exists():
        raise FileExistsError("Manual and combined edit specs are create-once")
    manual = []
    for item in needed:
        base = str(item["base_problem_id"])
        spec = SPECS[base]
        manual.append({
            "base_problem_id": base,
            "example_id": str(item["example_id"]),
            "original_value": str(item["original_value"]),
            "counterfactual_value": str(item["counterfactual_value"]),
            "roi_xyxy": [int(value) for value in spec["roi"]],
            "font_size": int(spec["font"]),
            "text_anchor": [int(value) for value in spec["anchor"]],
            "counterfactual_sham_anchor_delta": [1, 0],
            "render_suffix": str(spec["suffix"]),
            "renderer": str(spec.get("renderer", "rectangle")),
            "target_evidence": str(item["target_evidence"]),
            "evidence_type": str(item["evidence_type"]),
            "geometric_source": "Stage 3C.9 score-blind coordinate-grid review; prior geometry reused where noted in source history",
            "requires_stage3c9_manual_revalidation": True,
            "attention_used": False,
            "causal_scores_available": False,
        })
    reused = read_jsonl(OUT / "cohort/work/reused_edit_specs.jsonl")
    combined = sorted(reused + manual, key=lambda row: int(row["base_problem_id"]))
    if len(combined) != 71 or len({row["base_problem_id"] for row in combined}) != 71:
        raise RuntimeError("Combined edit specs must contain 71 unique bases")
    write_jsonl(target, manual)
    write_jsonl(combined_target, combined)
    print(json.dumps({
        "manual_specs": len(manual),
        "reused_specs": len(reused),
        "combined_unique_bases": len(combined),
        "attention_used": False,
        "causal_scores_available": False,
    }, indent=2))


if __name__ == "__main__":
    main()
