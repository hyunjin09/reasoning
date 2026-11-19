#!/usr/bin/env python3
"""Consolidate all frozen Stage 3A candidate screens without changing their order."""

from __future__ import annotations

import json
from pathlib import Path

from visual_reasoning.stage0.io import write_jsonl


ROOT = Path(__file__).resolve().parents[2]
COHORT = ROOT / "outputs/stage3a/cohort"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    destination = COHORT / "candidate_screening.jsonl"
    snapshot = COHORT / "candidate_screening_initial57.jsonl"
    current = read_jsonl(destination)
    if snapshot.is_file():
        initial = read_jsonl(snapshot)
    else:
        if len(current) != 57:
            raise RuntimeError("Expected the historical 57-row initial candidate screen")
        initial = current
        write_jsonl(snapshot, initial)
    rows = [
        *initial,
        *read_jsonl(COHORT / "backup_candidate_screening.jsonl"),
        *read_jsonl(COHORT / "remaining_stage1_screening.jsonl"),
        *read_jsonl(COHORT / "round3_candidate_screening.jsonl"),
    ]
    bases = [str(row["base_problem_id"]) for row in rows]
    if len(rows) != 115 or len(set(bases)) != 115:
        raise RuntimeError(f"Expected 115 unique screened bases, found {len(rows)} rows/{len(set(bases))} bases")
    write_jsonl(destination, rows)
    print(json.dumps({"screened_rows": len(rows), "unique_base_problems": len(set(bases))}, indent=2))


if __name__ == "__main__":
    main()
