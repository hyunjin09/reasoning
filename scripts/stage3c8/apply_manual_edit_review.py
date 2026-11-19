#!/usr/bin/env python3
"""Freeze score-blind manual edit review before ROI mapping or causal scoring."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.io import write_json, write_jsonl


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c8"
CHECKS = ("full_image", "roi_crop", "target_semantics_exact", "unrelated_content_unchanged", "legible")


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
    pending = read_jsonl(OUT / "cohort/fresh_edit_manifest_pending.jsonl")
    reviews = {str(row["base_problem_id"]): row for row in read_jsonl(args.reviews)}
    expected = {str(row["base_problem_id"]) for row in pending}
    if set(reviews) != expected:
        raise RuntimeError("Manual edit review must exactly cover every constructed edit")
    reviewed_at = datetime.now(timezone.utc).isoformat()
    accepted, rejected = [], []
    for item in pending:
        base = str(item["base_problem_id"])
        review = reviews[base]
        if review.get("carrier_scores_available") is not False or review.get("attention_used") is not False:
            raise RuntimeError(f"Invalid score-blind provenance for edit review base {base}")
        checks = review["checks"]
        if set(checks) != set(CHECKS):
            raise RuntimeError(f"Edit review checks are incomplete for base {base}")
        decision = str(review["decision"]).upper()
        if decision not in {"ACCEPT", "REJECT"}:
            raise ValueError(f"Unknown edit decision for base {base}: {decision}")
        passed = decision == "ACCEPT" and all(bool(checks[name]) for name in CHECKS)
        if decision == "ACCEPT" and not passed:
            raise RuntimeError(f"Accepted edit has a failed manual check for base {base}")
        metadata_path = ROOT / item["edit_metadata"]
        metadata = read_json(metadata_path)
        metadata["manual_validation"] = {
            "status": "pass" if passed else "fail",
            "reviewer": "primary research agent",
            "reviewed_at": reviewed_at,
            **{name: bool(checks[name]) for name in CHECKS},
            "reason": str(review.get("reason", "")),
            "attention_used": False,
            "causal_scores_available": False,
        }
        write_json(metadata_path, metadata)
        validation = metadata_path.with_name("validation.md")
        validation.write_text(
            f"# Stage 3C8 edit validation — base {base}\n\n"
            "Automatic containment/dimension validation: **PASS**\n\n"
            f"Manual review: **{'PASS' if passed else 'FAIL'}**\n\n"
            f"Reason: {review.get('reason', '')}\n",
            encoding="utf-8",
        )
        result = {**item, "manual_edit_status": "pass" if passed else "fail", "manual_review": review}
        (accepted if passed else rejected).append(result)
    write_jsonl(OUT / "cohort/fresh_edit_manifest_reviewed.jsonl", accepted)
    write_jsonl(OUT / "cohort/fresh_edit_rejections.jsonl", rejected)
    print(json.dumps({"reviewed": len(pending), "accepted": len(accepted), "rejected": len(rejected)}, indent=2))


if __name__ == "__main__":
    main()
