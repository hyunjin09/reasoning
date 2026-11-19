#!/usr/bin/env python3
"""Freeze manually reviewed fresh Stage 3B.7-R ROI mappings before scoring."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from visual_reasoning.stage0.io import write_jsonl, write_text


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b7r/roi_audit"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decisions", type=Path, required=True)
    args = parser.parse_args()
    output = OUT / "roi_token_mapping.jsonl"
    if output.exists():
        raise FileExistsError(f"Frozen ROI mapping already exists: {output}")
    decisions = read_json(args.decisions)
    if decisions.get("causal_scores_available") is not False or decisions.get("attention_used") is not False:
        raise RuntimeError("ROI review must be causal-score- and attention-blind")
    draft = read_jsonl(OUT / "roi_token_mapping_draft.jsonl")
    irrelevant = read_jsonl(OUT / "irrelevant_roi_manifest_draft.jsonl")
    decision_rows = {str(row["base_problem_id"]): row for row in decisions["decisions"]}
    if set(decision_rows) != {str(row["base_problem_id"]) for row in draft}:
        raise RuntimeError("ROI decisions must cover the complete fresh cohort")
    if any(str(row["status"]) != "pass" for row in decision_rows.values()):
        raise RuntimeError("A rejected ROI requires cohort revision before scoring")
    reviewed_at = decisions.get("reviewed_at") or datetime.now(timezone.utc).isoformat()
    mappings = []
    for row in draft:
        base = str(row["base_problem_id"])
        decision = decision_rows[base]
        mappings.append({
            **row,
            "manual_overlay_validation": {
                "status": "pass",
                "reviewer": decisions["reviewer"],
                "reviewed_at": reviewed_at,
                "checks": decision["checks"],
                "note": decision["note"],
                "causal_scores_available": False,
                "selection_used_attention": False,
                "overrides_applied": False,
            },
        })
    irrelevant_frozen = [{**row, "manual_status": "pass", "reviewed_at": reviewed_at, "causal_scores_available": False, "attention_used": False} for row in irrelevant]
    write_jsonl(output, mappings)
    write_jsonl(OUT / "irrelevant_roi_manifest.jsonl", irrelevant_frozen)
    write_text(OUT / "roi_mapping_report.md", "\n".join([
        "# Stage 3B.7-R fresh ROI mapping audit", "",
        f"All **{len(mappings)}** fresh mappings passed full overlay review before causal scoring.", "",
        "Target regions are the attention-independent union of four-condition edited-pixel support mapped through exact preprocessing. Complements partition all visual tokens; rings use frozen radius one; irrelevant regions are cardinality-matched and disjoint.", "",
        "No raw attention or causal outcome was available during mapping or review.", "",
    ]))


if __name__ == "__main__":
    main()
