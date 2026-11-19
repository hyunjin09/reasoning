#!/usr/bin/env python3
"""Classify Stage 3C.9 event spans from source loss and cache rescue."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from visual_reasoning.stage0.io import write_json, write_jsonl
from visual_reasoning.stage3c8.analysis import holm_adjust, inferential_summary, robust_positive
from visual_reasoning.stage3c9.analysis import (
    classify_checkpoint,
    repeated_checkpoint_status,
    source_and_rescue_effects,
)


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c9"
CONDITIONS = ("O", "C")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--w8-source", type=Path, required=True)
    parser.add_argument("--w16-source", type=Path, required=True)
    parser.add_argument("--role", choices=("validation", "primary"), required=True)
    return parser.parse_args()


def raw_results(root: Path) -> dict[str, dict[str, Any]]:
    return {
        str(row["base_problem_id"]): row
        for path in sorted(root.glob("**/examples/*/result.json"))
        for row in [read_json(path)]
    }


def condition_effects(readout: dict[str, Any], window: str, arm: str) -> dict[str, dict[str, Any]]:
    result = {}
    for condition in CONDITIONS:
        row = readout[condition]["windows"][window]
        result[condition] = source_and_rescue_effects(
            condition=condition,
            native_D=float(row["native"]["D"]),
            suppressed_D=float(row["suppressed"]["D"]),
            rescue_D=float(row[arm]["D"]),
        )
    return result


def main() -> None:
    args = parse_args()
    manifest = read_jsonl(args.manifest)
    expected = {str(row["base_problem_id"]) for row in manifest}
    raw = raw_results(args.raw_root)
    if set(raw) != expected:
        raise RuntimeError(f"Checkpoint result bases mismatch: {len(raw)}/{len(expected)}")
    source_rows = {
        (str(row["base_problem_id"]), int(row["event_id"]), row["window"]): row
        for path in (args.w8_source, args.w16_source)
        for row in read_jsonl(path)
    }
    span_rows, token_rows, neighbor_rows = [], [], []
    base_classifications = []
    class_rank = {"C0": 0, "C1": 1, "C2": 2, "C3": 3}
    for item in manifest:
        base = str(item["base_problem_id"])
        raw_events = {int(row["event_id"]): row for row in raw[base]["events"]}
        classified_events = []
        for event in item["events"]:
            event_id = int(event["event_id"])
            raw_event = raw_events[event_id]
            window_classes = {}
            for window in ("W8", "W16"):
                source = source_rows.get((base, event_id, window))
                if source is None:
                    continue
                scored = window in raw_event["conditions"]["O"]["local_use"].get("windows", {})
                if not scored:
                    classification = "C1" if source["local_use"]["source_sensitive"] else "C0"
                    window_classes[window] = {
                        "classification": classification,
                        "source_sensitive": bool(source["local_use"]["source_sensitive"]),
                        "rescue_scored": False,
                    }
                    continue
                local_readout = {condition: raw_event["conditions"][condition]["local_use"] for condition in CONDITIONS}
                event_effects = condition_effects(local_readout, window, "event_span_rescue")
                neighbor_effects = condition_effects(local_readout, window, "matched_neighbor_rescue")
                final_readout = {condition: raw_event["conditions"][condition]["final_use"] for condition in CONDITIONS}
                final_effects = condition_effects(final_readout, window, "event_span_rescue")
                local_index = int(local_readout["O"]["readout_generated_index"])
                final_index = int(final_readout["O"]["readout_generated_index"])
                final_readout_distinct = final_index > local_index
                source_losses = {condition: float(event_effects[condition]["source_loss"]) for condition in CONDITIONS}
                rescue_gains = {condition: float(event_effects[condition]["rescue_gain"]) for condition in CONDITIONS}
                rescue_ratios = {
                    condition: float(event_effects[condition]["rescue_ratio"])
                    for condition in CONDITIONS
                    if event_effects[condition]["rescue_ratio"] is not None
                }
                neighbor_gains = {condition: float(neighbor_effects[condition]["rescue_gain"]) for condition in CONDITIONS}
                final_gains = {condition: float(final_effects[condition]["rescue_gain"]) for condition in CONDITIONS}
                classification = classify_checkpoint(
                    source_losses=source_losses,
                    sham_source_effects=source["local_use"]["sham_source_effects"],
                    rescue_gains=rescue_gains,
                    rescue_ratios=rescue_ratios,
                    neighbor_gains=neighbor_gains,
                    final_rescue_gains=final_gains if final_readout_distinct else None,
                )
                window_classes[window] = {**classification, "rescue_scored": True}
                span_rows.append({
                    "base_problem_id": base,
                    "example_id": str(item["example_id"]),
                    "cohort_role": args.role,
                    "event_id": event_id,
                    "window": window,
                    "span_start_token": int(event["span_start_token"]),
                    "span_end_token": int(event["span_end_token"]),
                    "span_text": event["span_text"],
                    "source_losses": source_losses,
                    "rescue_gains": rescue_gains,
                    "rescue_gain_mean": classification["rescue_gain_mean"],
                    "rescue_ratios_unclipped": rescue_ratios,
                    "median_unclipped_rescue_ratio": classification["median_unclipped_rescue_ratio"],
                    "final_rescue_gains": final_gains,
                    "final_rescue_gain_mean": classification["final_rescue_gain_mean"],
                    "final_readout_distinct_from_local": final_readout_distinct,
                    "local_use_readout_generated_index": local_index,
                    "final_use_readout_generated_index": final_index,
                    "classification": classification["classification"],
                    "local_use_primary": True,
                    "final_use_secondary": True,
                })
                neighbor_rows.append({
                    "base_problem_id": base,
                    "event_id": event_id,
                    "window": window,
                    "event_span_rescue_gains": rescue_gains,
                    "neighbor_rescue_gains": neighbor_gains,
                    "event_gain_mean": classification["rescue_gain_mean"],
                    "neighbor_gain_mean": classification["neighbor_gain_mean"],
                    "event_minus_neighbor": float(classification["rescue_gain_mean"] - classification["neighbor_gain_mean"]),
                    "matched_by": "same tokenizer-position count within plus/minus 8 reasoning tokens",
                    "selection_used_attention": False,
                })
                per_condition = raw_event["conditions"]
                positions = list(range(int(event["span_start_token"]), int(event["span_end_token"])))
                position_gains = []
                for position in positions:
                    effects = {}
                    for condition in CONDITIONS:
                        local = per_condition[condition]["local_use"]["windows"][window]
                        effects[condition] = source_and_rescue_effects(
                            condition=condition,
                            native_D=float(local["native"]["D"]),
                            suppressed_D=float(local["suppressed"]["D"]),
                            rescue_D=float(local["constituent_token_rescue"][str(position)]["D"]),
                        )
                    mean_gain = float(np.mean([effects[condition]["rescue_gain"] for condition in CONDITIONS]))
                    position_gains.append(mean_gain)
                    token_rows.append({
                        "base_problem_id": base,
                        "event_id": event_id,
                        "window": window,
                        "generated_index": position,
                        "rescue_gain_mean": mean_gain,
                        "condition_metrics": effects,
                        "secondary_localization_only": True,
                        "event_span_redefined": False,
                    })
                span_rows[-1]["constituent_gain_sum"] = float(sum(position_gains))
                span_rows[-1]["best_constituent_generated_index"] = positions[int(np.argmax(position_gains))]
            if not window_classes:
                raise RuntimeError(f"No source-window classification exists for base {base} event {event_id}")
            overall = max(
                (row["classification"] for row in window_classes.values()),
                key=class_rank.__getitem__,
            )
            classified_events.append({
                "event_id": event_id,
                "span_start_token": int(event["span_start_token"]),
                "span_end_token": int(event["span_end_token"]),
                "event_role": event["event_role"],
                "evidence_relation": event["evidence_relation"],
                "temporal_location": event["temporal_location"],
                "classification": overall,
                "qualifying_windows": [name for name, row in window_classes.items() if row["classification"] in {"C2", "C3"}],
                "window_classifications": window_classes,
            })
        repeated = repeated_checkpoint_status(classified_events)
        base_classifications.append({
            "base_problem_id": base,
            "example_id": str(item["example_id"]),
            "events": classified_events,
            **repeated,
            "primary_statistical_unit": "base_problem_id",
        })
    family_stats = {}
    for window in ("W8", "W16"):
        selected = [row for row in span_rows if row["window"] == window]
        by_base: dict[str, list[float]] = defaultdict(list)
        contrast_by_base: dict[str, list[float]] = defaultdict(list)
        for row in selected:
            by_base[row["base_problem_id"]].append(float(row["rescue_gain_mean"]))
        for row in neighbor_rows:
            if row["window"] == window:
                contrast_by_base[row["base_problem_id"]].append(float(row["event_minus_neighbor"]))
        family_stats[window] = {
            "event_span_rescue": inferential_summary({base: float(np.mean(values)) for base, values in by_base.items()}),
            "event_minus_neighbor": inferential_summary({base: float(np.mean(values)) for base, values in contrast_by_base.items()}),
        }
    tests = [(window, metric) for window in ("W8", "W16") for metric in ("event_span_rescue", "event_minus_neighbor")]
    adjusted = holm_adjust([family_stats[window][metric]["wilcoxon_p"] for window, metric in tests])
    for (window, metric), p_value in zip(tests, adjusted):
        family_stats[window][metric]["holm_p"] = p_value
        family_stats[window][metric]["robust_positive"] = robust_positive(family_stats[window][metric])
    summary = {
        "cohort_role": args.role,
        "N_unique_bases": len(expected),
        "scored_event_windows": len(span_rows),
        "C2_C3_event_count": sum(event["classification"] in {"C2", "C3"} for row in base_classifications for event in row["events"]),
        "repeated_checkpoint_base_count": sum(row["repeated_checkpoint"] for row in base_classifications),
        "family_statistics": family_stats,
        "primary_statistical_unit": "base_problem_id",
        "rescue_ratios_clipped": False,
    }
    if args.role == "primary":
        write_jsonl(OUT / "phase_b_checkpoint/event_span_rescue.jsonl", span_rows)
        write_jsonl(OUT / "phase_b_checkpoint/single_token_localization.jsonl", token_rows)
        write_jsonl(OUT / "phase_b_checkpoint/neighbor_controls.jsonl", neighbor_rows)
        write_json(OUT / "phase_b_checkpoint/checkpoint_classification.json", {"bases": base_classifications, "summary": summary})
    else:
        write_jsonl(OUT / "audit/validation_event_span_rescue.jsonl", span_rows)
        write_jsonl(OUT / "audit/validation_single_token_localization.jsonl", token_rows)
        write_jsonl(OUT / "audit/validation_neighbor_controls.jsonl", neighbor_rows)
        write_json(OUT / "audit/validation_checkpoint_classification.json", {"bases": base_classifications, "summary": summary})
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
