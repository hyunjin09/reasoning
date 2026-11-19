#!/usr/bin/env python3
"""Assemble base-level Stage 3C.9 long-horizon checkpoint analyses."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from visual_reasoning.stage0.io import write_json
from visual_reasoning.stage3c8.analysis import inferential_summary


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c9"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    manifest = {str(row["base_problem_id"]): row for row in read_jsonl(OUT / "cohort/primary_manifest.jsonl")}
    classification = read_json(OUT / "phase_b_checkpoint/checkpoint_classification.json")
    class_by_base = {str(row["base_problem_id"]): row for row in classification["bases"]}
    spans = read_jsonl(OUT / "phase_b_checkpoint/event_span_rescue.jsonl")
    lifetime = read_jsonl(OUT / "phase_c_lifetime/lifetime_readouts.jsonl")
    repeated = read_json(OUT / "phase_c_lifetime/repeated_checkpoint_classification.json")
    source_stats = read_json(OUT / "phase_a_source/source_statistics.json")
    route_gate = read_json(OUT / "phase_d_routes/gate.json")
    span_by_base: dict[str, list[dict[str, Any]]] = defaultdict(list)
    lifetime_by_base: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in spans:
        span_by_base[str(row["base_problem_id"])].append(row)
    for row in lifetime:
        lifetime_by_base[str(row["base_problem_id"])].append(row)
    base_rows = []
    for base, item in manifest.items():
        classes = class_by_base[base]
        base_spans = span_by_base.get(base, [])
        local = [float(row["rescue_gain_mean"]) for row in base_spans]
        final = [
            float(row["final_rescue_gain_mean"])
            for row in base_spans
            if row["final_rescue_gain_mean"] is not None
        ]
        source_sensitive = sum(
            any(window["source_sensitive"] for window in event["window_classifications"].values())
            for event in classes["events"]
        )
        base_rows.append({
            "base_problem_id": base,
            "example_id": str(item["example_id"]),
            "evidence_type": str(item["evidence_type"]),
            "source": str(item["source"]),
            "variant": str(item["variant"]),
            "reasoning_length": int(item["generated_token_count"]),
            "annotated_event_count": len(classes["events"]),
            "source_sensitive_event_count": source_sensitive,
            "checkpoint_count": int(classes["checkpoint_count"]),
            "repeated_checkpoint": bool(classes["repeated_checkpoint"]),
            "median_local_checkpoint_rescue": None if not local else float(np.median(local)),
            "median_final_checkpoint_rescue": None if not final else float(np.median(final)),
            "checkpoint_lifetime_distribution": dict(Counter(row["lifetime_phenotype"] for row in lifetime_by_base.get(base, []))),
        })
    checkpoint_values = {row["base_problem_id"]: float(row["checkpoint_count"]) for row in base_rows}
    repeated_values = {row["base_problem_id"]: float(row["repeated_checkpoint"]) for row in base_rows}
    local_values = {row["base_problem_id"]: float(row["median_local_checkpoint_rescue"]) for row in base_rows if row["median_local_checkpoint_rescue"] is not None}
    final_values = {row["base_problem_id"]: float(row["median_final_checkpoint_rescue"]) for row in base_rows if row["median_final_checkpoint_rescue"] is not None}
    summary = {
        "N_unique_bases": len(base_rows),
        "primary_statistical_unit": "base_problem_id",
        "per_base": base_rows,
        "checkpoint_count_statistics": inferential_summary(checkpoint_values),
        "repeated_checkpoint_fraction_statistics": inferential_summary(repeated_values),
        "local_rescue_statistics": inferential_summary(local_values),
        "final_rescue_statistics": inferential_summary(final_values),
        "source_statistics": source_stats,
        "phase_d_gate": route_gate,
        "attention_used_for_selection_or_intervention": False,
        "necessity_null_interpretation": "A weak suppression or rescue effect is limited to the tested windows/spans and is not proof of irrelevance or non-visual reasoning.",
    }
    write_json(OUT / "analysis/long_horizon_checkpoint_summary.json", summary)
    write_json(OUT / "analysis/repeated_checkpoint_analysis.json", {
        "N_unique_bases": len(base_rows),
        "checkpoint_count_distribution": repeated["checkpoint_count_distribution"],
        "repeated_checkpoint_count": repeated["repeated_checkpoint_count"],
        "repeated_checkpoint_fraction": repeated["repeated_checkpoint_count"] / len(base_rows) if base_rows else None,
        "definition": "at least two nonoverlapping C2/C3 checkpoints separated by at least 24 reasoning tokens",
        "base_rows": [{key: row[key] for key in ("base_problem_id", "checkpoint_count", "repeated_checkpoint")} for row in base_rows],
    })
    type_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in base_rows:
        type_groups[row["evidence_type"]].append(row)
    write_json(OUT / "analysis/target_heterogeneity.json", {
        "evidence_types": {
            name: {
                "N_unique_bases": len(rows),
                "checkpoint_count_mean": float(np.mean([row["checkpoint_count"] for row in rows])),
                "repeated_checkpoint_fraction": float(np.mean([row["repeated_checkpoint"] for row in rows])),
                "median_reasoning_length": float(np.median([row["reasoning_length"] for row in rows])),
            }
            for name, rows in sorted(type_groups.items())
        },
        "source_distribution": dict(Counter(row["source"] for row in base_rows)),
        "variant_distribution": dict(Counter(row["variant"] for row in base_rows)),
        "descriptive_only": True,
    })
    print(json.dumps({"N_unique_bases": len(base_rows), "repeated": repeated["repeated_checkpoint_count"], "phase_d": route_gate["run_phase_d"]}, indent=2))


if __name__ == "__main__":
    main()
