#!/usr/bin/env python3
"""Freeze the manually reviewed strong lexical-match subset before intervention."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c3/cohort"
STRONG = {
    "119": "same high-level sector referent remains active across M and R",
    "141": "same high-level building referent remains active across M and R",
    "751": "same high-level tube referent remains active across M and R",
    "80": "same high-level cylinder referent remains active across M and R",
    "120": "same high-level cone referent remains active across M and R",
}


def main() -> None:
    frozen_at = datetime.now(timezone.utc).isoformat()
    rows = [json.loads(line) for line in (OUT / "lexical_review_draft.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    reviewed = []
    for row in rows:
        base = str(row["base_problem_id"])
        strong = base in STRONG
        reviewed.append({
            **row,
            "strong_lexical_match": strong,
            "manual_reason": STRONG.get(base, "M and R do not share a sufficiently specific active entity phrase or close paraphrase"),
            "manual_review_status": "pass",
            "frozen_at": frozen_at,
        })
    subset = [row for row in reviewed if row["strong_lexical_match"]]
    (OUT / "lexical_review.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in reviewed), encoding="utf-8")
    (OUT / "lexical_match_subset.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in subset), encoding="utf-8")
    print(json.dumps({"reviewed_pairs": len(reviewed), "strong_pairs": len(subset), "strong_bases": sorted(STRONG, key=int)}, indent=2))


if __name__ == "__main__":
    main()
