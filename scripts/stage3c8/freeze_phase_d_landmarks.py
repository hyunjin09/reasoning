#!/usr/bin/env python3
"""Freeze manually reviewed Phase-D landmark drafts before causal scoring."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.io import write_json, write_jsonl


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c8"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reviews", type=Path, required=True)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    args = parse_args()
    cohort_gate = read_json(OUT / "phase_d_anchor/cohort_gate.json")
    final_manifest = OUT / "phase_d_anchor/long_horizon_manifest.jsonl"
    final_landmarks = OUT / "phase_d_anchor/landmark_annotations.jsonl"
    if final_manifest.exists() or final_landmarks.exists():
        raise FileExistsError("Phase-D landmark freeze already exists")
    if not cohort_gate["run"]:
        write_jsonl(final_manifest, [])
        write_jsonl(final_landmarks, [])
        return
    manifest = read_jsonl(OUT / "phase_d_anchor/long_horizon_manifest_draft.jsonl")
    landmarks = read_jsonl(OUT / "phase_d_anchor/landmark_annotations_draft.jsonl")
    reviews = {str(row["base_problem_id"]): row for row in read_jsonl(args.reviews)}
    expected = {str(row["base_problem_id"]) for row in manifest}
    if set(reviews) != expected:
        raise RuntimeError("Manual landmark review must exactly cover the drafted long-horizon bases")
    frozen_at = datetime.now(timezone.utc).isoformat()
    for base, review in reviews.items():
        if review.get("decision") != "ACCEPT" or review.get("attention_used") is not False or review.get("phase_d_scores_available") is not False:
            raise RuntimeError(f"Phase-D landmark review failed or has invalid provenance for base {base}")
        if not all(bool(review[key]) for key in ("token_indices_exact", "semantic_labels_valid", "local_windows_valid")):
            raise RuntimeError(f"Phase-D landmark review checks failed for base {base}")
    frozen_landmarks = [
        {**row, "manual_review_status": "pass", "review": reviews[str(row["base_problem_id"])], "frozen_at": frozen_at}
        for row in landmarks
    ]
    write_jsonl(final_manifest, [{**row, "manual_review_status": "pass", "frozen_at": frozen_at} for row in manifest])
    write_jsonl(final_landmarks, frozen_landmarks)
    cohort_gate.update({"manual_review_status": "pass", "frozen_at": frozen_at})
    write_json(OUT / "phase_d_anchor/cohort_gate.json", cohort_gate)
    print(json.dumps({"bases": len(manifest), "landmarks": len(frozen_landmarks)}, indent=2))


if __name__ == "__main__":
    main()
