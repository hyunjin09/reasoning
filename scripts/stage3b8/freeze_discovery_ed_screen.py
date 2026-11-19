#!/usr/bin/env python3
"""Freeze at most 20 completed-correct discovery bases for blind E_d review."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from visual_reasoning.stage0.io import write_json, write_jsonl


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b8/discovery_cohort"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    target = OUT / "completed_correct_pending_strict_ed.jsonl"
    if target.exists():
        raise FileExistsError(f"Discovery E_d screen is already frozen: {target}")
    pool = sorted(read_jsonl(OUT / "completed_correct_pool.jsonl"), key=lambda row: int(row["base_problem_id"]))
    if len(pool) < 16:
        raise RuntimeError(f"Only {len(pool)} completed-correct bases; activate the held prospective batch")
    selected, capacity_excluded = pool[:20], pool[20:]
    write_jsonl(target, selected)
    write_jsonl(OUT / "ed_capacity_exclusions.jsonl", [{
        "base_problem_id": str(row["base_problem_id"]),
        "stage": "pre_Ed_capacity_freeze",
        "reason": "prospectively capped at 20 by ascending base_problem_id before trace/attention/causal/fit inspection",
        "attention_used": False,
        "stage3b8_causal_or_fit_scores_inspected": False,
    } for row in capacity_excluded])
    write_json(OUT / "ed_screen_freeze.json", {
        "frozen_at": datetime.now(timezone.utc).isoformat(),
        "rule": "completed-correct eligibility, then ascending base_problem_id; retain first at most 20",
        "pool_count": len(pool),
        "selected_count": len(selected),
        "selected_base_problem_ids": [str(row["base_problem_id"]) for row in selected],
        "capacity_excluded_base_problem_ids": [str(row["base_problem_id"]) for row in capacity_excluded],
        "attention_used": False,
        "generation_text_inspected": False,
        "stage3b8_causal_or_fit_scores_inspected": False,
    })
    print(json.dumps({"pool": len(pool), "selected": len(selected), "capacity_excluded": len(capacity_excluded)}, indent=2))


if __name__ == "__main__":
    main()
