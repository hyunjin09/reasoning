#!/usr/bin/env python3
"""Aggregate Stage 3C.9 W8/W16 source effects by independent base."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from visual_reasoning.stage0.io import write_json, write_jsonl
from visual_reasoning.stage3c8.analysis import holm_adjust, inferential_summary, robust_positive
from visual_reasoning.stage3c9.analysis import summarize_source_window


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c9"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--role", choices=("validation", "primary"), required=True)
    return parser.parse_args()


def raw_results(root: Path) -> list[dict[str, Any]]:
    return [read_json(path) for path in sorted(root.glob("**/examples/*/result.json"))]


def readout_summary(event: dict[str, Any], readout: str, window: str) -> dict[str, Any] | None:
    scores = {}
    for condition, condition_row in event["conditions"].items():
        arm = condition_row[readout]["windows"][window]
        if not arm["available"]:
            return None
        scores[condition] = {
            "native_D": float(arm["native"]["D"]),
            "suppressed_D": float(arm["suppressed"]["D"]),
        }
    return summarize_source_window(scores)


def main() -> None:
    args = parse_args()
    expected = {str(row["base_problem_id"]) for row in read_jsonl(args.manifest)}
    raw = raw_results(args.raw_root)
    observed = {str(row["base_problem_id"]) for row in raw}
    if observed != expected:
        raise RuntimeError(f"Source result bases mismatch: observed={len(observed)} expected={len(expected)}")
    rows = {"W8": [], "W16": []}
    sensitive = []
    for result in raw:
        base = str(result["base_problem_id"])
        for event in result["events"]:
            sensitive_windows = []
            for window in ("W8", "W16"):
                local = readout_summary(event, "local_use", window)
                final = readout_summary(event, "final_use", window)
                if local is None:
                    continue
                if local["source_sensitive"]:
                    sensitive_windows.append(window)
                rows[window].append({
                    "base_problem_id": base,
                    "example_id": str(result["example_id"]),
                    "cohort_role": args.role,
                    "event_id": int(event["event_id"]),
                    "event_role": event["event_role"],
                    "evidence_relation": event["evidence_relation"],
                    "temporal_location": event["temporal_location"],
                    "span_start_token": int(event["span_start_token"]),
                    "span_end_token": int(event["span_end_token"]),
                    "span_text": event["span_text"],
                    "window": window,
                    "local_use": local,
                    "final_use": final,
                    "local_use_primary": True,
                    "final_use_secondary": True,
                    "selection_used_attention": False,
                })
            sensitive.append({
                "base_problem_id": base,
                "event_id": int(event["event_id"]),
                "span_start_token": int(event["span_start_token"]),
                "span_end_token": int(event["span_end_token"]),
                "source_sensitive_windows": sensitive_windows,
                "run_checkpoint_rescue": bool(sensitive_windows),
                "event_span_frozen_before_source_scoring": True,
                "selection_used_attention": False,
            })
    stats = {}
    for window in ("W8", "W16"):
        by_base: dict[str, list[float]] = defaultdict(list)
        for row in rows[window]:
            by_base[row["base_problem_id"]].append(float(row["local_use"]["source_loss_mean"]))
        summary = inferential_summary({base: float(np.mean(values)) for base, values in by_base.items()})
        summary.update({
            "event_count": len(rows[window]),
            "source_sensitive_event_count": sum(row["local_use"]["source_sensitive"] for row in rows[window]),
            "aggregation": "mean within base before inference",
        })
        stats[window] = summary
    adjusted = holm_adjust([stats[window]["wilcoxon_p"] for window in ("W8", "W16")])
    for window, p_value in zip(("W8", "W16"), adjusted):
        stats[window]["holm_p"] = p_value
        stats[window]["robust_positive"] = robust_positive(stats[window])
    output = {
        "cohort_role": args.role,
        "N_unique_bases": len(expected),
        "window_statistics": stats,
        "source_sensitive_event_count_any_window": sum(row["run_checkpoint_rescue"] for row in sensitive),
        "source_insensitive_interpretation": "source-insensitive under tested W8/W16 windows; not evidence of non-visuality",
        "primary_statistical_unit": "base_problem_id",
        "attention_used": False,
    }
    if args.role == "primary":
        write_jsonl(OUT / "phase_a_source/w8_source_sensitivity.jsonl", rows["W8"])
        write_jsonl(OUT / "phase_a_source/w16_source_sensitivity.jsonl", rows["W16"])
        write_json(OUT / "phase_a_source/source_statistics.json", output)
        write_jsonl(OUT / "phase_b_checkpoint/source_sensitive_events.jsonl", sensitive)
    else:
        write_jsonl(OUT / "audit/validation_source_sensitivity.jsonl", rows["W8"] + rows["W16"])
        write_json(OUT / "audit/validation_source_summary.json", output)
        write_jsonl(OUT / "audit/validation_source_sensitive_events.jsonl", sensitive)
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
