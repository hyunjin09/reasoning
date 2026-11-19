#!/usr/bin/env python3
"""Apply frozen expansion audit decisions to the selected version metadata."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from visual_reasoning.stage0.io import write_json, write_text


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b9"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    selected = read_jsonl(OUT / "config/expansion_validated_edits/validated_edit_manifest.jsonl")
    excluded = read_jsonl(OUT / "config/expansion_validated_edits/edit_exclusions.jsonl")
    if len(selected) != 25 or len(excluded) != 9:
        raise RuntimeError("Frozen expansion edit decision count mismatch")
    frozen_at = datetime.now(timezone.utc).isoformat()
    for row in selected:
        metadata_path = ROOT / row["edit_metadata"]
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if "render_suffix" not in metadata:
            phase, base = row["phase"], str(row["base_problem_id"])
            v1 = json.loads((OUT / f"fresh_edits/expansion_v1/{phase}/{base}/edit_metadata.json").read_text(encoding="utf-8"))
            metadata["render_suffix"] = v1["render_suffix"]
        metadata["manual_validation"] = {
            "status": "pass",
            "reviewer": "primary_agent_visual_review",
            "frozen_at": frozen_at,
            "review_basis": "full rendered condition family plus enlarged target-ROI crops; no generation or Stage 3B.9 Value/causal outcome used",
            "checks": {
                "target_values_legible_and_exact": True,
                "original_value_fully_removed_in_rerenders": True,
                "crossing_diagram_strokes_preserved": True,
                "unrelated_task_relevant_content_unchanged": True,
                "dimensions_and_crop_fixed": True,
            },
        }
        write_json(metadata_path, metadata)
        write_text(
            metadata_path.parent / "validation.md",
            f"# Stage 3B.9 validated expansion edit — base {row['base_problem_id']}\n\n"
            "Automatic containment/dimension validation: **PASS**\n\n"
            "Manual semantic and geometry review: **PASS**\n\n"
            "The selected edit version was frozen before expansion generation or Stage 3B.9 Value/causal scoring.\n",
        )
    print(json.dumps({"manual_pass_metadata_updated": len(selected), "frozen_exclusions_unchanged": len(excluded)}, indent=2))


if __name__ == "__main__":
    main()
