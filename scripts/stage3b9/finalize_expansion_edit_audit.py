#!/usr/bin/env python3
"""Freeze the blinded Stage 3B.9 expansion edit audit and generation shards."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl, write_text


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b9"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    roots = {
        "v1": OUT / "fresh_edits/expansion_v1",
        "v2": OUT / "fresh_edits/expansion_v2",
    }
    manifests = {version: {str(row["base_problem_id"]): row for row in read_jsonl(root / "construction_manifest.jsonl")} for version, root in roots.items()}
    audits = {version: {str(row["base_problem_id"]): row for row in read_jsonl(root / "manual_audit.jsonl")} for version, root in roots.items()}
    if len(manifests["v1"]) != 34 or len(manifests["v2"]) != 24:
        raise RuntimeError("Unexpected expansion edit construction counts")
    if set(manifests["v2"]) != {base for base, row in audits["v1"].items() if row["status"] == "fail"}:
        raise RuntimeError("v2 must exactly repair v1 failures")
    selected, exclusions = [], []
    for base in sorted(manifests["v1"], key=int):
        version = "v1" if audits["v1"][base]["status"] == "pass" else "v2"
        decision = audits[version][base]
        row = manifests[version][base]
        if decision["status"] == "pass":
            selected.append({
                **row,
                "manual_edit_status": "pass",
                "manual_audit": str((roots[version] / "manual_audit.jsonl").relative_to(ROOT)),
                "selected_edit_version": version,
            })
        else:
            exclusions.append({
                "base_problem_id": base,
                "example_id": row["example_id"],
                "phase": row["phase"],
                "failed_versions": ["v1", "v2"],
                "final_reason": decision["reason"],
                "generation_outcome_inspected": False,
                "stage3b9_value_or_causal_outcome_inspected": False,
            })
    if len(selected) != 25 or sum(row["phase"] == "phase_a" for row in selected) != 19 or sum(row["phase"] == "phase_b" for row in selected) != 6:
        raise RuntimeError("Frozen expansion edit count mismatch")
    freeze = OUT / "config/expansion_validated_edits"
    ensure_directory(freeze)
    write_jsonl(freeze / "validated_edit_manifest.jsonl", selected)
    write_jsonl(freeze / "edit_exclusions.jsonl", exclusions)
    shards = [[], []]
    for index, row in enumerate(sorted(selected, key=lambda item: (item["phase"], int(item["base_problem_id"])))):
        shards[index % 2].append({
            "base_problem_id": row["base_problem_id"],
            "example_id": row["example_id"],
            "phase": row["phase"],
            "edit_version": row["edit_version"],
            "edit_metadata": row["edit_metadata"],
            "selection_used_attention": False,
            "selection_used_generation_outcomes": False,
            "selection_used_stage3b9_value_or_causal_outcomes": False,
        })
    shard_dir = OUT / "config/generation_expansion_shards"
    ensure_directory(shard_dir)
    hashes = {}
    for index, rows in enumerate(shards):
        path = shard_dir / f"shard_{index:02d}.jsonl"
        write_jsonl(path, rows)
        hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    summary = {
        "frozen_at": datetime.now(timezone.utc).isoformat(),
        "screened": 34,
        "validated": 25,
        "excluded_after_two_versions": 9,
        "phase_a_validated": 19,
        "phase_b_validated": 6,
        "shard_sizes": [len(rows) for rows in shards],
        "shard_sha256": hashes,
        "selection_used_attention": False,
        "selection_used_generation_outcomes": False,
        "selection_used_stage3b9_value_or_causal_outcomes": False,
    }
    write_json(freeze / "freeze.json", summary)
    write_text(
        freeze / "audit_report.md",
        "# Stage 3B.9 expansion edit audit\n\n"
        "The frozen 34-base expansion was audited before expansion generation or any Stage 3B.9 Value/causal scoring. "
        "Version 1 passed 10 edits. One versioned mechanical repair addressed the 24 failures; 15 repairs passed and "
        "9 remained ambiguous and were excluded.\n\n"
        "- Validated: **25** (19 Phase A, 6 Phase B)\n"
        "- Excluded: **9**\n"
        "- Attention used for selection: **no**\n"
        "- Expansion-generation outcomes inspected: **no**\n"
        "- Stage 3B.9 Value or causal outcomes inspected: **no**\n",
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
