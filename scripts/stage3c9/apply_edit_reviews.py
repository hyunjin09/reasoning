#!/usr/bin/env python3
"""Apply score-blind manual validation to Stage 3C.9 edit quartets."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.io import write_json, write_jsonl


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c9"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reviews", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    accepted_path = OUT / "cohort/edit_manifest_reviewed.jsonl"
    rejection_path = OUT / "cohort/edit_rejections.jsonl"
    if accepted_path.exists() or rejection_path.exists():
        raise FileExistsError("Final edit review outputs are create-once")
    pending = read_jsonl(OUT / "cohort/edit_manifest_pending.jsonl")
    reviews = {str(row["base_problem_id"]): row for row in read_jsonl(args.reviews)}
    expected = {str(row["base_problem_id"]) for row in pending}
    if set(reviews) != expected:
        raise RuntimeError(f"Edit reviews must exactly cover pending manifest; missing={sorted(expected-set(reviews), key=int)} extra={sorted(set(reviews)-expected, key=int)}")
    accepted, rejected = [], []
    reviewed_at = datetime.now(timezone.utc).isoformat()
    for item in pending:
        base = str(item["base_problem_id"])
        review = reviews[base]
        if review.get("attention_used") is not False or review.get("causal_scores_available") is not False:
            raise RuntimeError(f"Edit review was not score-blind for base {base}")
        decision = str(review.get("decision", "")).upper()
        metadata_path = ROOT / item["edit_metadata"]
        metadata = read_json(metadata_path)
        if decision == "ACCEPT":
            checks = review.get("checks", {})
            required = ("full_image", "roi_crop", "target_semantics_exact", "sham_semantics_exact", "unrelated_content_unchanged", "legible", "counterfactual_problem_valid")
            if not all(checks.get(key) is True for key in required):
                raise RuntimeError(f"Manual edit checks failed for accepted base {base}")
            metadata["manual_validation"] = {
                "status": "pass",
                "reviewer": "primary research agent",
                "reviewed_at": reviewed_at,
                **{key: True for key in required},
                "reason": str(review.get("reason", "")),
                "causal_scores_available": False,
            }
            write_json(metadata_path, metadata)
            (metadata_path.parent / "validation.md").write_text(
                f"# Stage 3C.9 edit validation — base {base}\n\nAutomatic containment/dimension validation: **PASS**\n\nManual review: **PASS**\n\n{review.get('reason','')}\n",
                encoding="utf-8",
            )
            accepted.append({**item, "manual_edit_status": "pass", "manual_review": review})
        elif decision == "REJECT":
            metadata["manual_validation"] = {"status": "reject", "reviewed_at": reviewed_at, "reason": str(review.get("reason", "")), "causal_scores_available": False}
            write_json(metadata_path, metadata)
            (metadata_path.parent / "validation.md").write_text(
                f"# Stage 3C.9 edit validation — base {base}\n\nAutomatic containment/dimension validation: **PASS**\n\nManual review: **REJECT**\n\n{review.get('reason','')}\n",
                encoding="utf-8",
            )
            rejected.append({**item, "manual_edit_status": "reject", "rejection_reason": str(review.get("reason", ""))})
        else:
            raise ValueError(f"Unknown edit decision for base {base}: {decision}")
    write_jsonl(accepted_path, accepted)
    write_jsonl(rejection_path, rejected)
    print(json.dumps({"reviewed": len(pending), "accepted": len(accepted), "rejected": len(rejected)}, indent=2))


if __name__ == "__main__":
    main()
