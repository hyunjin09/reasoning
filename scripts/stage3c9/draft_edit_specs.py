#!/usr/bin/env python3
"""Draft score-blind Stage 3C.9 edit specs, reusing exact Stage 3C.8 geometry."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.io import write_jsonl
from visual_reasoning.stage3c9.edits import normalize_numeric_surface


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c9"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--semantic-manifest", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    reusable_path = OUT / "cohort/work/reused_edit_specs.jsonl"
    manual_path = OUT / "cohort/work/manual_edit_specs_needed.jsonl"
    if reusable_path.exists() or manual_path.exists():
        raise FileExistsError("Edit-spec drafts are create-once")
    semantic = read_jsonl(args.semantic_manifest)
    reusable, manual = [], []
    for item in semantic:
        base = str(item["base_problem_id"])
        old_path = ROOT / "outputs/stage3c8/counterfactuals" / base / "edit_metadata.json"
        reason = None
        if not old_path.is_file():
            reason = "no_stage3c8_edit"
        else:
            old = read_json(old_path)
            if str(old["example_id"]) != str(item["example_id"]):
                reason = "stage3c8_example_mismatch"
            elif normalize_numeric_surface(old["original_value"]) != normalize_numeric_surface(item["original_value"]):
                reason = "stage3c8_original_value_mismatch"
            elif normalize_numeric_surface(old["counterfactual_value"]) != normalize_numeric_surface(item["counterfactual_value"]):
                reason = "stage3c8_counterfactual_value_mismatch"
            else:
                reusable.append({
                    "base_problem_id": base,
                    "example_id": str(item["example_id"]),
                    "original_value": str(item["original_value"]),
                    "counterfactual_value": str(item["counterfactual_value"]),
                    "roi_xyxy": [int(value) for value in old["roi_xyxy"]],
                    "font_size": int(old["font_size"]),
                    "text_anchor": [int(value) for value in old["text_anchor"]],
                    "counterfactual_sham_anchor_delta": [int(value) for value in old["counterfactual_sham_anchor_delta"]],
                    "render_suffix": str(old.get("render_suffix", "")),
                    "renderer": str(old.get("renderer", "standard")),
                    "target_evidence": str(item["target_evidence"]),
                    "evidence_type": str(item["evidence_type"]),
                    "geometric_source": str(old_path.relative_to(ROOT)),
                    "requires_stage3c9_manual_revalidation": True,
                    "attention_used": False,
                    "causal_scores_available": False,
                })
        if reason is not None:
            manual.append({
                "base_problem_id": base,
                "example_id": str(item["example_id"]),
                "original_value": str(item["original_value"]),
                "counterfactual_value": str(item["counterfactual_value"]),
                "target_evidence": str(item["target_evidence"]),
                "evidence_type": str(item["evidence_type"]),
                "source_image": item.get("source_image"),
                "reason": reason,
                "required_fields": ["roi_xyxy", "font_size", "text_anchor", "counterfactual_sham_anchor_delta", "render_suffix", "renderer"],
                "attention_used": False,
                "causal_scores_available": False,
            })
    write_jsonl(reusable_path, reusable)
    write_jsonl(manual_path, manual)
    print(json.dumps({"semantic_accepted": len(semantic), "reusable_exact_geometry": len(reusable), "manual_specs_needed": len(manual)}, indent=2))


if __name__ == "__main__":
    main()
