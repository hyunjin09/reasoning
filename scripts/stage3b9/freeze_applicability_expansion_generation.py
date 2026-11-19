#!/usr/bin/env python3
"""Freeze the seven-base applicability-expansion generation shards."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b9"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    target = OUT / "config/generation_applicability_expansion_shards"
    if target.exists() and any(target.iterdir()):
        raise FileExistsError(f"Expansion generation shards already exist: {target}")
    rows = read_jsonl(OUT / "phase_a_shared/blind_expansion_screen/edit_audit_v2/validated_edit_manifest.jsonl")
    if len(rows) != 7:
        raise RuntimeError("Expected seven edit-valid expansion bases")
    split = json.loads((OUT / "config/cohort_split.json").read_text(encoding="utf-8"))
    protected = set(split["historical_training"]["base_problem_ids"]) | set(split["protected_stage3b7"]["base_problem_ids"]) | set(split["protected_stage3b7r"]["base_problem_ids"])
    prior = {str(row["base_problem_id"]) for row in read_jsonl(OUT / "prospective_generation/raw_outcome_manifest.jsonl")}
    bases = {str(row["base_problem_id"]) for row in rows}
    if bases & protected or bases & prior or len(bases) != 7:
        raise RuntimeError("Applicability expansion is not disjoint from protected or earlier prospective cohorts")
    ensure_directory(target)
    write_jsonl(target / "shard_00.jsonl", rows[::2])
    write_jsonl(target / "shard_01.jsonl", rows[1::2])
    manifest = OUT / "phase_a_shared/blind_expansion_screen/edit_audit_v2/validated_edit_manifest.jsonl"
    write_json(target / "freeze.json", {
        "frozen_at": datetime.now(timezone.utc).isoformat(), "count": len(rows),
        "base_problem_ids": sorted(bases, key=int), "phase": "phase_a",
        "manifest": str(manifest.relative_to(ROOT)), "manifest_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(),
        "locked_protocol": "official Qwen-style Thinking; seed 1234; max_new_tokens 40960",
        "disjoint_from_historical_and_protected": True, "disjoint_from_prior_stage3b9_prospective": True,
        "attention_used": False, "new_base_generation_outcomes_used": False,
        "new_base_value_or_projected_rank_outcomes_used": False,
    })
    print(json.dumps({"count": len(rows), "shard_sizes": [len(rows[::2]), len(rows[1::2])]}, indent=2))


if __name__ == "__main__":
    main()
