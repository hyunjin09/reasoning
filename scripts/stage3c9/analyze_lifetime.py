#!/usr/bin/env python3
"""Aggregate Stage 3C.9 checkpoint lifetimes and freeze the Phase-D gate."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from visual_reasoning.stage0.io import write_json, write_jsonl
from visual_reasoning.stage3c8.analysis import inferential_summary
from visual_reasoning.stage3c9.analysis import lifetime_phenotype, source_and_rescue_effects
from visual_reasoning.stage3c9.protocol import first_route_pair, phase_d_route_gate


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
    parser.add_argument("--classification", type=Path, required=True)
    parser.add_argument("--span-results", type=Path, required=True)
    return parser.parse_args()


def mean_gain(conditions: dict[str, Any]) -> tuple[float, dict[str, float]]:
    gains = {}
    for condition in ("O", "C"):
        row = conditions[condition]
        effect = source_and_rescue_effects(
            condition=condition,
            native_D=float(row["native"]["D"]),
            suppressed_D=float(row["suppressed"]["D"]),
            rescue_D=float(row["event_span_rescue"]["D"]),
        )
        gains[condition] = float(effect["rescue_gain"])
    return float(np.mean(list(gains.values()))), gains


def main() -> None:
    args = parse_args()
    manifest = {str(row["base_problem_id"]): row for row in read_jsonl(args.manifest)}
    classification = read_json(args.classification)["bases"]
    class_by_base = {str(row["base_problem_id"]): row for row in classification}
    span_rows = {
        (str(row["base_problem_id"]), int(row["event_id"]), row["window"]): row
        for row in read_jsonl(args.span_results)
    }
    raw = {
        str(row["base_problem_id"]): row
        for path in sorted(args.raw_root.glob("**/examples/*/result.json"))
        for row in [read_json(path)]
    }
    if set(raw) != set(manifest):
        raise RuntimeError(f"Lifetime result bases mismatch: {len(raw)}/{len(manifest)}")
    lifetime_rows, reinstatement_rows, repeated_rows, pair_rows = [], [], [], []
    phenotype_rank = {"NOT_APPLICABLE": 0, "L-Short": 1, "L-Medium": 2, "L-Persistent": 3}
    for base, item in manifest.items():
        class_row = class_by_base[base]
        raw_events = {int(row["event_id"]): row for row in raw[base]["events"]}
        event_annotations = {int(row["event_id"]): row for row in item["events"]}
        event_lifetimes = []
        for classified in class_row["events"]:
            if classified["classification"] not in {"C2", "C3"}:
                continue
            event_id = int(classified["event_id"])
            per_window = {}
            for window in classified["qualifying_windows"]:
                local = span_rows[(base, event_id, window)]
                local_gain = float(local["rescue_gain_mean"])
                final_gain = (
                    None if local["final_rescue_gain_mean"] is None
                    else float(local["final_rescue_gain_mean"])
                )
                downstream = []
                raw_event = raw_events.get(event_id)
                if raw_event is not None:
                    for readout in raw_event["windows"].get(window, []):
                        gain, conditions = mean_gain(readout["conditions"])
                        downstream.append({
                            "downstream_event_id": int(readout["downstream_event_id"]),
                            "distance": int(readout["distance_from_checkpoint_end"]),
                            "rescue_gain_mean": gain,
                            "rescue_gains": conditions,
                        })
                phenotype = lifetime_phenotype(
                    local_gain=local_gain,
                    downstream=[(row["distance"], row["rescue_gain_mean"]) for row in downstream],
                    final_gain=final_gain,
                )
                per_window[window] = {
                    "local_rescue_gain_mean": local_gain,
                    "downstream_semantic_readouts": downstream,
                        "final_rescue_gain_mean": final_gain,
                    "lifetime_phenotype": phenotype,
                }
            overall = max(
                (row["lifetime_phenotype"] for row in per_window.values()),
                key=phenotype_rank.__getitem__,
            )
            event_lifetimes.append({
                "event_id": event_id,
                "span_start_token": int(classified["span_start_token"]),
                "span_end_token": int(classified["span_end_token"]),
                "classification": classified["classification"],
                "evidence_relation": classified["evidence_relation"],
                "per_window": per_window,
                "lifetime_phenotype": overall,
                "pseudo_readouts_used": False,
            })
        lifetime_rows.extend({"base_problem_id": base, **row} for row in event_lifetimes)
        repeated = {
            "base_problem_id": base,
            "checkpoint_count": int(class_row["checkpoint_count"]),
            "checkpoint_count_bin": "3+" if int(class_row["checkpoint_count"]) >= 3 else str(class_row["checkpoint_count"]),
            "repeated_checkpoint": bool(class_row["repeated_checkpoint"]),
            "qualifying_pairs": class_row["qualifying_pairs"],
        }
        repeated_rows.append(repeated)
        pair = first_route_pair(class_row["events"])
        if pair is not None:
            pair_rows.append({"base_problem_id": base, "example_id": str(item["example_id"]), "route_pair": pair})
        for pair_indices in class_row["qualifying_pairs"]:
            earlier = class_row["events"][int(pair_indices[0])]
            later = class_row["events"][int(pair_indices[1])]
            if earlier["evidence_relation"] != "SAME_TARGET_EVIDENCE" or later["evidence_relation"] != "SAME_TARGET_EVIDENCE":
                continue
            early_life = next(row for row in event_lifetimes if row["event_id"] == int(earlier["event_id"]))
            later_life = next(row for row in event_lifetimes if row["event_id"] == int(later["event_id"]))
            comparisons = []
            for window, early_window in early_life["per_window"].items():
                downstream = next((row for row in early_window["downstream_semantic_readouts"] if row["downstream_event_id"] == int(later["event_id"])), None)
                later_window = later_life["per_window"].get(window)
                if downstream is None and int(event_annotations[int(later["event_id"])]["local_use_readout"]["token_index"]) == int(item["final_use_readout"]["token_index"]):
                    downstream = {
                        "downstream_event_id": int(later["event_id"]),
                        "distance": int(item["final_use_readout"]["token_index"]) - int(earlier["span_end_token"]),
                        "rescue_gain_mean": float(early_window["final_rescue_gain_mean"]),
                        "source": "frozen_final_use_readout",
                    }
                if downstream is not None and later_window is not None:
                    comparisons.append({
                        "window": window,
                        "earlier_checkpoint_gain_at_later_readout": downstream["rescue_gain_mean"],
                        "later_checkpoint_local_gain": later_window["local_rescue_gain_mean"],
                        "reinstatement_pattern": downstream["rescue_gain_mean"] < 0.05 <= later_window["local_rescue_gain_mean"],
                    })
            reinstatement_rows.append({
                "base_problem_id": base,
                "earlier_event_id": int(earlier["event_id"]),
                "later_event_id": int(later["event_id"]),
                "same_target_evidence": True,
                "comparisons": comparisons,
                "reinstatement_any_window": any(row["reinstatement_pattern"] for row in comparisons),
                "pair_lifetime_phenotype": (
                    "L-Replaced" if any(row["reinstatement_pattern"] for row in comparisons)
                    else "NOT_L_REPLACED"
                ),
            })
    gate = phase_d_route_gate(pair_rows)
    gate.update({
        "evaluated_after_checkpoint_classification_frozen": True,
        "route_pairs_selected_by_annotation_order": True,
        "attention_used": False,
    })
    write_jsonl(OUT / "phase_c_lifetime/lifetime_readouts.jsonl", lifetime_rows)
    write_json(OUT / "phase_c_lifetime/repeated_checkpoint_classification.json", {
        "bases": repeated_rows,
        "N_unique_bases": len(repeated_rows),
        "repeated_checkpoint_count": sum(row["repeated_checkpoint"] for row in repeated_rows),
        "checkpoint_count_distribution": dict(Counter(row["checkpoint_count_bin"] for row in repeated_rows)),
    })
    write_jsonl(OUT / "phase_c_lifetime/same_evidence_reinstatement.jsonl", reinstatement_rows)
    write_jsonl(OUT / "phase_d_routes/route_pair_manifest.jsonl", pair_rows)
    write_json(OUT / "phase_d_routes/gate.json", gate)
    by_base: dict[str, list[float]] = defaultdict(list)
    for row in lifetime_rows:
        for window in row["per_window"].values():
            if window["final_rescue_gain_mean"] is not None:
                by_base[row["base_problem_id"]].append(float(window["final_rescue_gain_mean"]))
    summary = {
        "N_unique_bases": len(manifest),
        "confirmed_checkpoint_count": len(lifetime_rows),
        "phenotype_distribution": dict(Counter(row["lifetime_phenotype"] for row in lifetime_rows)),
        "final_rescue_base_statistics": inferential_summary({base: float(np.mean(values)) for base, values in by_base.items()}),
        "reinstatement_pair_count": len(reinstatement_rows),
        "reinstatement_count": sum(row["reinstatement_any_window"] for row in reinstatement_rows),
        "L_Replaced_pair_count": sum(row["pair_lifetime_phenotype"] == "L-Replaced" for row in reinstatement_rows),
        "phase_d_gate": gate,
    }
    write_json(OUT / "analysis/lifetime_analysis.json", summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
