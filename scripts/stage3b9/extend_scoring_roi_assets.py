#!/usr/bin/env python3
"""Add the validated expansion mappings without altering frozen bases or arms."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from visual_reasoning.stage0.io import write_json, write_jsonl


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b9"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    target = OUT / "config/phase_a_scoring/phase_a_roi_mapping_all_fresh.jsonl"
    freeze = OUT / "config/phase_a_scoring/roi_expansion_freeze.json"
    if target.exists() or freeze.exists():
        raise FileExistsError("Expanded scoring ROI assets already exist")
    all_rows = read_jsonl(OUT / "roi_validation/roi_token_mapping_all_fresh.jsonl")
    phase_a = []
    for row in all_rows:
        if row["phase"] == "phase_a":
            row["four_condition_layout_exact"] = bool(row["all_condition_layout_exact"])
            phase_a.append(row)
    if len(all_rows) != 76 or len(phase_a) != 54:
        raise RuntimeError("Combined/Phase-A ROI mapping count mismatch")
    write_jsonl(target, phase_a)
    write_json(
        freeze,
        {
            "frozen_at": datetime.now(timezone.utc).isoformat(),
            "purpose": "extend only candidate ROI compatibility after the blinded expansion edit/ROI audit",
            "phase_a_roi_count": len(phase_a),
            "initial_phase_a_roi_count": 35,
            "expansion_phase_a_roi_count": 19,
            "mapping_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
            "projectors_arms_ranks_or_targets_modified": False,
            "attention_used": False,
            "expansion_generation_outcomes_used": False,
            "fresh_value_vectors_or_causal_scores_used": False,
        },
    )
    print(json.dumps({"phase_a_roi_count": len(phase_a), "combined_roi_count": len(all_rows)}, indent=2))


if __name__ == "__main__":
    main()
