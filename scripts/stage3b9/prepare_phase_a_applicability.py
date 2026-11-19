#!/usr/bin/env python3
"""Freeze the Phase-A full-V applicability cohort before rank scoring."""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path

from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b9"
TARGETS = ("target_a", "target_b_r")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def usable(arm: dict) -> bool:
    return bool(
        math.isfinite(float(arm["BVR"]))
        and float(arm["BVR"]) > 0.0
        and arm["bidirectionally_source_consistent"]
        and arm["all_scores_finite"]
        and arm["all_query_head_selectivity_valid"]
        and arm["all_recipient_tensor_alignment_exact"]
        and arm["all_self_restorations_exact"]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--full-shard", type=Path, action="append", required=True)
    args = parser.parse_args()
    target = OUT / "phase_a_shared/applicability_gate.json"
    if target.exists():
        raise FileExistsError(f"Phase-A applicability is already frozen: {target}")
    manifest = read_jsonl(args.manifest)
    by_base = {str(row["base_problem_id"]): row for row in manifest}
    results = {}
    for shard in args.full_shard:
        for path in sorted(shard.glob("examples/*/result.json")):
            base = path.parent.name
            if base in results:
                raise RuntimeError(f"Duplicate Phase-A full-V result for base {base}")
            results[base] = read_json(path)
    if set(results) != set(by_base):
        raise RuntimeError("Phase-A full-V results do not exactly cover the frozen pre-applicability manifest")
    gates, accepted, excluded = [], [], []
    for base in sorted(by_base, key=int):
        result = results[base]
        target_status = {}
        for target_id in TARGETS:
            target_row = next(row for row in result["targets"] if row["target_id"] == target_id)
            arm = next(row for row in target_row["arms"] if row["arm_id"] == "full_V")
            target_status[target_id] = {
                "usable": usable(arm),
                "BVR": float(arm["BVR"]),
                "BVR_O": float(arm["BVR_O"]),
                "BVR_C": float(arm["BVR_C"]),
                "bidirectionally_source_consistent": bool(arm["bidirectionally_source_consistent"]),
            }
        pass_all = all(row["usable"] for row in target_status.values())
        gates.append({
            "base_problem_id": base,
            "usable_at_both_frozen_targets": pass_all,
            "targets": target_status,
            "rank_projection_outcomes_inspected": False,
        })
        if pass_all:
            accepted.append(by_base[base])
        else:
            excluded.append({
                "base_problem_id": base,
                "stage": "prospective_full_V_applicability",
                "reason": "full V-only semantic restoration was not finite, positive, and bidirectionally source-consistent at both frozen targets",
                "targets": target_status,
                "rank_projection_outcomes_inspected": False,
            })
    payload = {
        "frozen_at": datetime.now(timezone.utc).isoformat(),
        "pre_applicability_count": len(manifest),
        "accepted_count": len(accepted),
        "excluded_count": len(excluded),
        "accepted_base_problem_ids": [str(row["base_problem_id"]) for row in accepted],
        "rule": "finite positive full-V BVR with bidirectional source consistency and all v3 mechanics at both frozen targets",
        "rank_projection_outcomes_existed": False,
        "attention_used": False,
    }
    print(json.dumps(payload, indent=2))
    if len(accepted) < 24:
        ensure_directory(target.parent)
        write_json(OUT / "phase_a_shared/applicability_insufficient.json", payload)
        raise RuntimeError(f"Phase-A applicability retained {len(accepted)} bases; at least 24 required")
    ensure_directory(target.parent)
    write_jsonl(OUT / "phase_a_shared/applicability_gate.jsonl", gates)
    write_jsonl(OUT / "phase_a_shared/fresh_confirmation_manifest.jsonl", accepted)
    write_jsonl(OUT / "phase_a_shared/exclusions.jsonl", excluded)
    shard_dir = OUT / "config/phase_a_scoring/eligible_shards"
    ensure_directory(shard_dir)
    write_jsonl(shard_dir / "shard_00.jsonl", accepted[::2])
    write_jsonl(shard_dir / "shard_01.jsonl", accepted[1::2])
    write_json(target, payload)


if __name__ == "__main__":
    main()
