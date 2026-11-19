#!/usr/bin/env python3
"""Aggregate complete Stage 1B shards into descriptive discovery artifacts."""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

import numpy as np
from scipy.stats import fisher_exact, mannwhitneyu, spearmanr

from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl, write_text
from visual_reasoning.stage0.plotting import save_visual_focus_snapshots
from visual_reasoning.stage1.plotting import save_span_timeline
from visual_reasoning.stage1.protocol import repetition_diagnostics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt-manifest", type=Path, required=True)
    parser.add_argument("--shards-root", type=Path, required=True)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--bootstrap-samples", type=int, default=5000)
    parser.add_argument("--manual-count", type=int, default=20)
    parser.add_argument("--representative-count", type=int, default=12)
    return parser.parse_args()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def directory_bytes(path: Path) -> int:
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def distribution(values: Iterable[float]) -> dict[str, float | int | None]:
    array = np.asarray(list(values), dtype=np.float64)
    if not array.size:
        return {"count": 0, "mean": None, "median": None, "p10": None, "p90": None, "maximum": None}
    return {
        "count": int(array.size),
        "mean": float(array.mean()),
        "median": float(np.median(array)),
        "p10": float(np.percentile(array, 10)),
        "p90": float(np.percentile(array, 90)),
        "maximum": float(array.max()),
    }


def bootstrap_mean_ci(values: Iterable[float], samples: int, rng: np.random.Generator) -> list[float] | None:
    array = np.asarray(list(values), dtype=np.float64)
    if not array.size:
        return None
    draws = rng.choice(array, size=(samples, array.size), replace=True).mean(axis=1)
    return [float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))]


def bootstrap_fraction_ci(flags: Iterable[bool], samples: int, rng: np.random.Generator) -> list[float] | None:
    return bootstrap_mean_ci((float(value) for value in flags), samples, rng)


def weighted_mean(values: list[float], weights: list[int]) -> float:
    return float(np.average(np.asarray(values, dtype=np.float64), weights=np.asarray(weights, dtype=np.float64)))


def safe_spearman(left: list[float], right: list[float]) -> dict[str, float | int | None]:
    if len(left) < 3 or np.std(left) == 0 or np.std(right) == 0:
        return {"n": len(left), "rho": None, "p_value": None}
    result = spearmanr(left, right)
    return {"n": len(left), "rho": float(result.statistic), "p_value": float(result.pvalue)}


def two_by_two(rows: list[dict[str, Any]], flag_name: str) -> dict[str, Any]:
    a = sum(bool(row["is_peak"]) and bool(row[flag_name]) for row in rows)
    b = sum(bool(row["is_peak"]) and not bool(row[flag_name]) for row in rows)
    c = sum(not bool(row["is_peak"]) and bool(row[flag_name]) for row in rows)
    d = sum(not bool(row["is_peak"]) and not bool(row[flag_name]) for row in rows)
    odds_ratio, p_value = fisher_exact([[a, b], [c, d]])
    return {
        "table": {"peak_and_flag": a, "peak_without_flag": b, "nonpeak_and_flag": c, "nonpeak_without_flag": d},
        "odds_ratio": None if not math.isfinite(float(odds_ratio)) else float(odds_ratio),
        "fisher_exact_p_value": float(p_value),
    }


def trajectory_metrics(spans: list[dict[str, Any]], peaks: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    weights = [int(span["end_token"]) - int(span["start_token"]) for span in spans]
    visual = [float(span["attention"]["visual_mass"]["mean"]) for span in spans]
    visual_density = [float(span["attention"]["visual_density"]["mean"]) for span in spans]
    prompt = [float(span["attention"]["prompt_mass"]["mean"]) for span in spans]
    prompt_density = [float(span["attention"]["prompt_density"]["mean"]) for span in spans]
    reasoning = [float(span["attention"]["reasoning_mass"]["mean"]) for span in spans]
    reasoning_density = [float(span["attention"]["reasoning_density"]["mean"]) for span in spans]
    entropy = [float(span["uncertainty"]["entropy"]["mean"]) for span in spans]
    turnover = [span["visual_focus_metrics"].get("turnover_from_previous_span") for span in spans]
    finite_turnover = [float(value) for value in turnover if value is not None and math.isfinite(float(value))]
    prefill_similarity = [float(span["visual_focus_metrics"]["similarity_to_prefill"]) for span in spans if span["visual_focus_metrics"].get("similarity_to_prefill") is not None]
    spatial_entropy = [float(span["visual_focus_metrics"]["spatial_entropy"]) for span in spans]
    topk_overlap = [float(span["visual_focus_metrics"]["topk_overlap_previous_span"]) for span in spans if span["visual_focus_metrics"].get("topk_overlap_previous_span") is not None]
    total_tokens = sum(weights)
    midpoints = [((int(span["start_token"]) + int(span["end_token"])) / 2) / max(1, total_tokens) for span in spans]
    early = [index for index, midpoint in enumerate(midpoints) if midpoint <= 0.25] or [0]
    late = [index for index, midpoint in enumerate(midpoints) if midpoint >= 0.75] or [len(spans) - 1]
    peak_ids = {int(row["span_id"]) for row in peaks.get("peaks", [])}
    event_rows: list[dict[str, Any]] = []
    last_peak: int | None = None
    for index, span in enumerate(spans):
        is_peak = index in peak_ids
        if is_peak:
            elapsed = None if last_peak is None else index - last_peak
            last_peak = index
        else:
            elapsed = None if last_peak is None else index - last_peak
        label = str(span["semantic_label"])
        event_rows.append(
            {
                "span_id": index,
                "semantic_label": label,
                "is_peak": is_peak,
                "visual_read": label == "VISUAL_READ",
                "visual_reference": bool(span["lexical_context"]["has_visual_reference"]),
                "semantic_transition": index > 0 and label != str(spans[index - 1]["semantic_label"]),
                "visual_mass": visual[index],
                "entropy": entropy[index],
                "entropy_change": None if index == 0 else entropy[index] - entropy[index - 1],
                "focus_turnover": None if turnover[index] is None else float(turnover[index]),
                "elapsed_spans_since_peak": elapsed,
            }
        )
    early_visual = weighted_mean([visual[index] for index in early], [weights[index] for index in early])
    late_visual = weighted_mean([visual[index] for index in late], [weights[index] for index in late])
    return (
        {
            "span_count": len(spans),
            "visual_mass_mean": weighted_mean(visual, weights),
            "visual_mass_sum_over_generated_tokens": float(sum(value * weight for value, weight in zip(visual, weights))),
            "visual_density_mean": weighted_mean(visual_density, weights),
            "prompt_mass_mean": weighted_mean(prompt, weights),
            "prompt_density_mean": weighted_mean(prompt_density, weights),
            "reasoning_mass_mean": weighted_mean(reasoning, weights),
            "reasoning_density_mean": weighted_mean(reasoning_density, weights),
            "entropy_mean": weighted_mean(entropy, weights),
            "early_visual_mass": early_visual,
            "late_visual_mass": late_visual,
            "early_minus_late_visual_mass": early_visual - late_visual,
            "focus_turnover_mean": float(np.mean(finite_turnover)) if finite_turnover else 0.0,
            "focus_turnover_max": float(np.max(finite_turnover)) if finite_turnover else 0.0,
            "focus_similarity_to_prefill_mean": float(np.mean(prefill_similarity)) if prefill_similarity else 0.0,
            "focus_spatial_entropy_mean": float(np.mean(spatial_entropy)) if spatial_entropy else 0.0,
            "focus_topk_overlap_mean": float(np.mean(topk_overlap)) if topk_overlap else 0.0,
            "peak_count": len(peak_ids),
            "peak_rate_per_100_spans": 100.0 * len(peak_ids) / max(1, len(spans)),
            "peak_rate_per_1000_tokens": 1000.0 * len(peak_ids) / max(1, total_tokens),
            "peak_positions": [float(row["normalized_generation_position"]) for row in peaks.get("peaks", [])],
            "semantic_label_counts": dict(sorted(Counter(str(span["semantic_label"]) for span in spans).items())),
        },
        event_rows,
    )


def locate_results(shards_root: Path) -> dict[str, Path]:
    located: dict[str, Path] = {}
    for path in sorted(shards_root.glob("shard_*/examples/*/result.json")):
        example_id = path.parent.name
        if example_id in located:
            raise RuntimeError(f"Duplicate discovery result for {example_id}")
        located[example_id] = path
    return located


def select_evenly(rows: list[dict[str, Any]], count: int) -> list[dict[str, Any]]:
    variants = sorted({str(row["variant"]) for row in rows})
    if len(rows) <= count or not variants:
        return sorted(rows, key=lambda row: (int(row["generated_token_count"]), int(row["example_id"])))
    selected: list[dict[str, Any]] = []
    for variant_index, variant in enumerate(variants):
        ordered = sorted(
            (row for row in rows if row["variant"] == variant),
            key=lambda row: (int(row["generated_token_count"]), int(row["example_id"])),
        )
        allocation = count // len(variants) + (1 if variant_index < count % len(variants) else 0)
        indices = np.linspace(0, len(ordered) - 1, min(allocation, len(ordered))).round().astype(int)
        selected.extend(ordered[index] for index in indices)
    return sorted(selected, key=lambda row: (str(row["variant"]), int(row["generated_token_count"])))


def select_representatives(rows: list[dict[str, Any]], count: int) -> list[tuple[dict[str, Any], str]]:
    axes = [
        ("early-heavy visual attention", lambda row: row["metrics"]["early_minus_late_visual_mass"], True),
        ("recurrent candidate visual peaks", lambda row: row["metrics"]["peak_count"], True),
        ("persistent visual attention", lambda row: row["metrics"]["visual_mass_mean"] - abs(row["metrics"]["early_minus_late_visual_mass"]), True),
        ("low visual attention", lambda row: row["metrics"]["visual_mass_mean"], False),
        ("large visual-focus shift", lambda row: row["metrics"]["focus_turnover_max"], True),
        ("small visual-focus shift", lambda row: row["metrics"]["focus_turnover_mean"], False),
    ]
    selected: list[tuple[dict[str, Any], str]] = []
    seen: set[str] = set()
    rank = 0
    while len(selected) < count:
        added = False
        for reason, key, reverse in axes:
            candidates = sorted(rows, key=lambda row: (key(row), -int(row["example_id"])), reverse=reverse)
            if rank < len(candidates):
                candidate = candidates[rank]
                if candidate["example_id"] not in seen:
                    selected.append((candidate, reason))
                    seen.add(candidate["example_id"])
                    added = True
                    if len(selected) >= count:
                        break
        if not added and rank >= len(rows):
            break
        rank += 1
    return selected


def create_example_links(output_dir: Path, records: list[dict[str, Any]]) -> None:
    links = ensure_directory(output_dir / "examples")
    for record in records:
        link = links / str(record["example_id"])
        if link.exists() or link.is_symlink():
            continue
        target = Path(record["artifact_dir"])
        link.symlink_to(os.path.relpath(target, links), target_is_directory=True)


def write_manual_packet(output_dir: Path, selected: list[dict[str, Any]]) -> None:
    lines = [
        "# Stage 1B Semantic Segmentation Review Packet",
        "",
        "Twenty completed-correct trajectories were selected evenly across reasoning length within each MathVerse variant. Labels are text-derived; attention was not used for labeling or sample selection.",
        "",
    ]
    selection_rows = []
    for row in selected:
        spans = read_json(Path(row["artifact_dir"]) / "spans.json")
        input_record = read_json(Path(row["artifact_dir"]) / "input.json")
        indices = sorted(set(np.linspace(0, len(spans) - 1, min(30, len(spans))).round().astype(int).tolist()))
        label_counts = dict(sorted(Counter(str(span["semantic_label"]) for span in spans).items()))
        lines.extend(
            [
                f"## Example {row['example_id']} — {row['mathverse_variant']} — {row['generated_token_count']} tokens",
                "",
                f"Question: {input_record['question']}",
                "",
                f"Span count / label counts: {len(spans)} / `{json.dumps(label_counts, sort_keys=True)}`",
                "",
                f"Review sample: {len(indices)} spans evenly spaced from the first through final span.",
                "",
                f"Full spans: `{Path(row['artifact_dir']) / 'spans.json'}`",
                "",
            ]
        )
        for index in indices:
            span = spans[index]
            text = " ".join(str(span["span_text"]).split())
            lines.append(f"- `{span['span_id']}` `{span['semantic_label']}` [{span['start_token']}:{span['end_token']}]: {text[:260]}")
        lines.append("")
        selection_rows.append({"example_id": row["example_id"], "generated_token_count": row["generated_token_count"], "variant": row["mathverse_variant"], "artifact_dir": row["artifact_dir"]})
    write_text(output_dir / "manual_review" / "segmentation_review_packet.md", "\n".join(lines))
    write_json(output_dir / "manual_review" / "segmentation_review_selection.json", {"count": len(selection_rows), "selection": selection_rows})


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir.resolve()
    allowed = (Path.cwd() / "outputs" / "stage1" / "discovery").resolve()
    if output_dir != allowed:
        raise ValueError(f"Final discovery output must be exactly {allowed}")
    attempt_rows = read_jsonl(args.attempt_manifest)
    rebuild_audits = []
    for shard_dir in sorted(args.shards_root.resolve().glob("shard_*")):
        if not (shard_dir / "examples").is_dir():
            continue
        audit_path = shard_dir / "derived_span_rebuild.json"
        if not audit_path.is_file():
            raise RuntimeError(f"Derived Stage 1 text-rule rebuild is missing: {audit_path}")
        audit = read_json(audit_path)
        if audit.get("semantic_label_definition") != "stage1_text_rules_v2":
            raise RuntimeError(f"Unexpected span-label version in {audit_path}")
        if audit.get("candidate_peak_definition") != "stage1_prominence_v2_token_midpoint":
            raise RuntimeError(f"Unexpected candidate-peak version in {audit_path}")
        rebuild_audits.append({"shard": shard_dir.name, "audit": str(audit_path), "rebuilt_examples": len(audit["rebuilt_examples"])})
    located = locate_results(args.shards_root)
    expected_ids = {str(row["example_id"]) for row in attempt_rows}
    if set(located) != expected_ids:
        missing = sorted(expected_ids - set(located), key=int)
        extra = sorted(set(located) - expected_ids, key=int)
        raise RuntimeError(f"Discovery is incomplete: missing={missing}, extra={extra}")

    manifest_by_id = {str(row["example_id"]): row for row in attempt_rows}
    records: list[dict[str, Any]] = []
    enriched: list[dict[str, Any]] = []
    all_events: list[dict[str, Any]] = []
    for example_id in sorted(expected_ids, key=lambda value: int(manifest_by_id[value]["order"])):
        result_path = located[example_id]
        result = read_json(result_path)
        artifact_dir = result_path.parent.resolve()
        manifest = manifest_by_id[example_id]
        repetition = None
        if str(result["status"]) == "truncated":
            generation = read_json(artifact_dir / "generation.json")
            repetition = repetition_diagnostics(str(generation["full_generated_response"]))
            write_json(artifact_dir / "repetition_diagnostics.json", repetition)
        record = {
            **manifest,
            "mathverse_variant": str(result["mathverse_variant"]),
            "status": str(result["status"]),
            "termination_reason": "safety_cap" if str(result["status"]) == "truncated" else "EOS",
            "normal_termination": str(result["status"]) != "truncated",
            "completed": bool(result["complete"]),
            "correct": bool(result["correct"]),
            "reasoning_length": int(result["generated_token_count"]),
            "generated_token_count": int(result["generated_token_count"]),
            "span_count": int(result["span_count"]),
            "candidate_visual_peak_count": int(result["candidate_visual_peak_count"]),
            "latency_seconds": float(result["runtime"]["elapsed_seconds"]),
            "peak_gpu_allocated_bytes": int(result["runtime"]["peak_gpu_allocated_bytes"]),
            "inference_bundle_bytes_before_derived_rebuild": int(result["output_bytes"]),
            "artifact_bytes": directory_bytes(artifact_dir),
            "artifact_dir": str(artifact_dir),
            "example_view": str((output_dir / "examples" / example_id).resolve()),
            "instrumentation_validation_passed": bool(result["validation"]["passed"]),
            "repetition_pathology_flag": None if repetition is None else bool(repetition["any_pathology_flag"]),
            "repetition_diagnostics_file": None if repetition is None else str(artifact_dir / "repetition_diagnostics.json"),
        }
        records.append(record)
        if record["completed"] and record["correct"]:
            spans = read_json(artifact_dir / "spans.json")
            peaks = read_json(artifact_dir / "candidate_visual_peaks.json")
            metrics, events = trajectory_metrics(spans, peaks)
            row = {**record, "metrics": metrics}
            enriched.append(row)
            for event in events:
                all_events.append({"example_id": example_id, **event})

    raw_manifest = output_dir / "raw_outcome_manifest.jsonl"
    cohort_manifest = output_dir / "cohort_manifest.jsonl"
    write_jsonl(raw_manifest, records)
    write_jsonl(cohort_manifest, [{key: value for key, value in row.items() if key != "metrics"} | {"descriptive_metrics": row["metrics"]} for row in enriched])
    create_example_links(output_dir, records)

    pairing_rows = [
        {
            "base_problem_id": row["base_problem_id"],
            "variant": row["variant"],
            "example_id": row["example_id"],
            "image_id": row["image_id"],
            "question_id": row["question_id"],
            "completed": row["completed"],
            "correct": row["correct"],
            "status": row["status"],
            "reasoning_length": row["reasoning_length"],
            "artifact_dir": row["artifact_dir"],
        }
        for row in records
    ]
    paired_dir = ensure_directory(output_dir / "paired_variants")
    write_jsonl(paired_dir / "pairing_manifest.jsonl", pairing_rows)

    by_variant = defaultdict(list)
    for row in records:
        by_variant[row["variant"]].append(row)
    pairing_lines = [
        "# Stage 1B Paired-Variant Availability",
        "",
        "Pairing key is MathVerse `problem_index`. This report prepares later controlled work; it does not perform a causal paired-variant experiment.",
        "",
        f"- Base problems with both selected variants: {len({row['base_problem_id'] for row in records})}",
        f"- Available variant combination: Vision Intensive + Vision Dominant ({len(records) // 2} pairs)",
        "",
        "| Variant | Attempts | Complete | Completion rate | Correct | Accuracy | Median length | p90 length |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for variant in sorted(by_variant):
        rows = by_variant[variant]
        complete = sum(row["completed"] for row in rows)
        correct = sum(row["correct"] for row in rows)
        lengths = distribution(row["reasoning_length"] for row in rows)
        pairing_lines.append(
            f"| {variant} | {len(rows)} | {complete} | {complete / len(rows):.1%} | {correct} | {correct / len(rows):.1%} | {lengths['median']:.1f} | {lengths['p90']:.1f} |"
        )
    write_text(paired_dir / "pairing_report.md", "\n".join(pairing_lines))

    outcome_counts = dict(sorted(Counter(row["status"] for row in records).items()))
    preliminary = {
        "raw_attempts": len(records),
        "outcomes": outcome_counts,
        "completed_correct": len(enriched),
        "minimum_required": 80,
        "target": 100,
        "cohort_gate_passed": len(enriched) >= 80,
        "derived_span_rebuilds": rebuild_audits,
    }
    write_json(output_dir / "cohort_gate.json", preliminary)
    if len(enriched) < 80:
        write_json(output_dir.parent / "summaries" / "stage1_statistics.json", {"status": "insufficient_discovery_cohort", **preliminary})
        print(json.dumps(preliminary, indent=2))
        return

    rng = np.random.default_rng(1234)
    peak_counts = [int(row["metrics"]["peak_count"]) for row in enriched]
    lengths = [int(row["generated_token_count"]) for row in enriched]
    peak_positions = [position for row in enriched for position in row["metrics"]["peak_positions"]]
    pooled_visual = [float(event["visual_mass"]) for event in all_events]
    high_threshold = float(np.percentile(pooled_visual, 75))
    for row in enriched:
        spans = read_json(Path(row["artifact_dir"]) / "spans.json")
        row["metrics"]["high_visual_span_fraction"] = sum(float(span["attention"]["visual_mass"]["mean"]) >= high_threshold for span in spans) / len(spans)
        peaks = read_json(Path(row["artifact_dir"]) / "candidate_visual_peaks.json")
        save_span_timeline(spans, peaks, Path(row["artifact_dir"]) / "plots" / "span_timeline.png", f"Stage 1B example {row['example_id']} — descriptive span timeline")
        write_json(
            Path(row["artifact_dir"]) / "plots" / "descriptive_timeline.json",
            {
                "semantic_labels": [span["semantic_label"] for span in spans],
                "span_ranges": [[span["start_token"], span["end_token"]] for span in spans],
                "visual_attention_mass": [span["attention"]["visual_mass"]["mean"] for span in spans],
                "previous_reasoning_attention_mass": [span["attention"]["reasoning_mass"]["mean"] for span in spans],
                "predictive_entropy": [span["uncertainty"]["entropy"]["mean"] for span in spans],
                "candidate_peak_span_ids": [peak["span_id"] for peak in peaks["peaks"]],
                "scientific_boundary": "descriptive candidate patterns; not causal LOOK/THINK states",
            },
        )

    peak_flags = [count for count in peak_counts]
    position_hist, position_edges = np.histogram(peak_positions, bins=np.linspace(0, 1, 11))
    entropy_values = [float(row["entropy"]) for row in all_events]
    turnover_pairs = [(float(row["visual_mass"]), float(row["focus_turnover"])) for row in all_events if row["focus_turnover"] is not None]
    variant_dynamics = {}
    for variant in sorted(by_variant):
        eligible_variant = [row for row in enriched if row["variant"] == variant]
        variant_dynamics[variant] = {
            "eligible_count": len(eligible_variant),
            "peak_count": distribution(row["metrics"]["peak_count"] for row in eligible_variant),
            "visual_mass_mean": distribution(row["metrics"]["visual_mass_mean"] for row in eligible_variant),
            "focus_turnover_mean": distribution(row["metrics"]["focus_turnover_mean"] for row in eligible_variant),
            "reasoning_length": distribution(row["generated_token_count"] for row in eligible_variant),
        }
    variants = sorted(variant_dynamics)
    variant_tests: dict[str, Any] = {}
    if len(variants) == 2:
        for metric in ("peak_count", "visual_mass_mean", "focus_turnover_mean", "generated_token_count"):
            left = [float(row["metrics"].get(metric, row.get(metric))) for row in enriched if row["variant"] == variants[0]]
            right = [float(row["metrics"].get(metric, row.get(metric))) for row in enriched if row["variant"] == variants[1]]
            test = mannwhitneyu(left, right, alternative="two-sided")
            variant_tests[metric] = {"variants": variants, "n": [len(left), len(right)], "mann_whitney_u": float(test.statistic), "p_value": float(test.pvalue)}

    peak_events = [row for row in all_events if row["is_peak"]]
    nonpeak_events = [row for row in all_events if not row["is_peak"]]
    semantic_dynamics = {}
    for label in sorted({str(row["semantic_label"]) for row in all_events}):
        label_rows = [row for row in all_events if row["semantic_label"] == label]
        semantic_dynamics[label] = {
            "span_count": len(label_rows),
            "trajectory_count": len({row["example_id"] for row in label_rows}),
            "candidate_peak_fraction": sum(bool(row["is_peak"]) for row in label_rows) / len(label_rows),
            "visual_mass": distribution(row["visual_mass"] for row in label_rows),
            "entropy": distribution(row["entropy"] for row in label_rows),
        }
    statistics = {
        "status": "stage1b_descriptive_analysis_complete",
        "protocol": read_json(output_dir.parent / "protocol_pilot" / "protocol_40960_selection.json"),
        "cohort": preliminary,
        "generation_length": {"all_outcomes": distribution(row["generated_token_count"] for row in records), "completed_correct": distribution(lengths)},
        "runtime_storage": {
            "latency_seconds": distribution(row["latency_seconds"] for row in records),
            "peak_gpu_allocated_bytes": max(row["peak_gpu_allocated_bytes"] for row in records),
            "artifact_bytes": distribution(row["artifact_bytes"] for row in records),
            "total_artifact_bytes": sum(row["artifact_bytes"] for row in records),
        },
        "attention": {
            "definitions": {
                "mass": "attention mass summed over source positions then averaged across recorded layers/heads",
                "density": "source mass divided by the number of source tokens before averaging",
                "high_span": "span visual mass at or above the pooled completed-correct 75th percentile",
            },
            "high_visual_span_threshold": high_threshold,
            "visual_mass_mean": distribution(row["metrics"]["visual_mass_mean"] for row in enriched),
            "visual_mass_mean_bootstrap_95ci": bootstrap_mean_ci((row["metrics"]["visual_mass_mean"] for row in enriched), args.bootstrap_samples, rng),
            "visual_mass_sum_over_generated_tokens": distribution(row["metrics"]["visual_mass_sum_over_generated_tokens"] for row in enriched),
            "visual_density_mean": distribution(row["metrics"]["visual_density_mean"] for row in enriched),
            "prompt_mass_mean": distribution(row["metrics"]["prompt_mass_mean"] for row in enriched),
            "prompt_density_mean": distribution(row["metrics"]["prompt_density_mean"] for row in enriched),
            "reasoning_mass_mean": distribution(row["metrics"]["reasoning_mass_mean"] for row in enriched),
            "reasoning_density_mean": distribution(row["metrics"]["reasoning_density_mean"] for row in enriched),
            "high_visual_span_fraction": distribution(row["metrics"]["high_visual_span_fraction"] for row in enriched),
            "early_minus_late_visual_mass": distribution(row["metrics"]["early_minus_late_visual_mass"] for row in enriched),
        },
        "visual_focus": {
            "prefill_reference_definition": "visual-focus distribution from the final prompt query in the initial prefill forward (the first recorded next-token decision)",
            "turnover_mean": distribution(row["metrics"]["focus_turnover_mean"] for row in enriched),
            "turnover_max": distribution(row["metrics"]["focus_turnover_max"] for row in enriched),
            "similarity_to_prefill_mean": distribution(row["metrics"]["focus_similarity_to_prefill_mean"] for row in enriched),
            "spatial_entropy_mean": distribution(row["metrics"]["focus_spatial_entropy_mean"] for row in enriched),
            "topk_overlap_previous_span_mean": distribution(row["metrics"]["focus_topk_overlap_mean"] for row in enriched),
            "visual_mass_vs_turnover_spearman": safe_spearman([row[0] for row in turnover_pairs], [row[1] for row in turnover_pairs]),
        },
        "candidate_peaks": {
            "detector": "three-span [0.25,0.5,0.25] smoothing; per-example prominence 0.5*SD; minimum distance 2 spans",
            "peak_count": distribution(peak_counts),
            "peak_rate_per_100_spans": distribution(row["metrics"]["peak_rate_per_100_spans"] for row in enriched),
            "peak_rate_per_1000_tokens": distribution(row["metrics"]["peak_rate_per_1000_tokens"] for row in enriched),
            "zero_peak_fraction": sum(count == 0 for count in peak_flags) / len(peak_flags),
            "zero_peak_fraction_bootstrap_95ci": bootstrap_fraction_ci((count == 0 for count in peak_flags), args.bootstrap_samples, rng),
            "one_peak_fraction": sum(count == 1 for count in peak_flags) / len(peak_flags),
            "one_peak_fraction_bootstrap_95ci": bootstrap_fraction_ci((count == 1 for count in peak_flags), args.bootstrap_samples, rng),
            "two_or_more_peak_fraction": sum(count >= 2 for count in peak_flags) / len(peak_flags),
            "two_or_more_peak_fraction_bootstrap_95ci": bootstrap_fraction_ci((count >= 2 for count in peak_flags), args.bootstrap_samples, rng),
            "normalized_position_histogram": {"edges": position_edges.tolist(), "counts": position_hist.tolist(), "total_peaks": len(peak_positions)},
            "trace_length_vs_peak_count_spearman": safe_spearman(lengths, peak_counts),
            "trace_length_vs_peak_rate_per_100_spans_spearman": safe_spearman(lengths, [float(row["metrics"]["peak_rate_per_100_spans"]) for row in enriched]),
            "trace_length_vs_peak_rate_per_1000_tokens_spearman": safe_spearman(lengths, [float(row["metrics"]["peak_rate_per_1000_tokens"]) for row in enriched]),
        },
        "when_why_alignment": {
            "peak_vs_visual_read": two_by_two(all_events, "visual_read"),
            "peak_vs_visual_reference_language": two_by_two(all_events, "visual_reference"),
            "peak_vs_semantic_transition": two_by_two(all_events, "semantic_transition"),
            "visual_mass_vs_entropy_spearman": safe_spearman([float(row["visual_mass"]) for row in all_events], entropy_values),
            "peak_entropy": distribution(row["entropy"] for row in peak_events),
            "nonpeak_entropy": distribution(row["entropy"] for row in nonpeak_events),
            "peak_entropy_change": distribution(row["entropy_change"] for row in peak_events if row["entropy_change"] is not None),
            "nonpeak_entropy_change": distribution(row["entropy_change"] for row in nonpeak_events if row["entropy_change"] is not None),
            "peak_focus_turnover": distribution(row["focus_turnover"] for row in peak_events if row["focus_turnover"] is not None),
            "nonpeak_focus_turnover": distribution(row["focus_turnover"] for row in nonpeak_events if row["focus_turnover"] is not None),
            "inter_peak_elapsed_spans": distribution(peak["inter_peak_distance"] for row in enriched for peak in read_json(Path(row["artifact_dir"]) / "candidate_visual_peaks.json")["peaks"] if peak["inter_peak_distance"] is not None),
            "inter_peak_elapsed_tokens": distribution(peak["inter_peak_token_distance"] for row in enriched for peak in read_json(Path(row["artifact_dir"]) / "candidate_visual_peaks.json")["peaks"] if peak["inter_peak_token_distance"] is not None),
            "inter_peak_elapsed_normalized_generation": distribution(peak["inter_peak_normalized_distance"] for row in enriched for peak in read_json(Path(row["artifact_dir"]) / "candidate_visual_peaks.json")["peaks"] if peak["inter_peak_normalized_distance"] is not None),
            "boundary": "hypothesis-generating association only; no causal trigger claim",
        },
        "semantic_span_dynamics": semantic_dynamics,
        "variant_dynamics": variant_dynamics,
        "variant_exploratory_tests": variant_tests,
        "exploratory_inference_caveat": "Span rows within a trajectory are not independent, and the two selected variants from one base problem are not independent. Pooled-span and unpaired variant p-values/associations are descriptive screens, not confirmatory or causal tests; no paired-variant causal comparison is performed in Stage 1.",
        "bootstrap": {"samples": args.bootstrap_samples, "seed": 1234, "interval": "percentile 95% over trajectories"},
        "scientific_boundary": "raw attention and candidate peaks are descriptive evidence, not causal visual usage",
    }
    summaries_dir = ensure_directory(output_dir.parent / "summaries")
    write_json(summaries_dir / "stage1_statistics.json", statistics)
    write_jsonl(output_dir / "trajectory_metrics.jsonl", [{"example_id": row["example_id"], "variant": row["variant"], **row["metrics"]} for row in enriched])

    manual_rows = select_evenly(enriched, args.manual_count)
    write_manual_packet(output_dir, manual_rows)
    representatives = select_representatives(enriched, args.representative_count)
    representative_rows = []
    representative_review_lines = [
        "# Representative Qualitative Review Packet",
        "",
        "These completed-correct examples were selected deterministically across six descriptive axes, including high and low visual engagement and large and small focus shifts. Attention is descriptive, not causal usage.",
        "",
    ]
    for row, reason in representatives:
        source = Path(row["artifact_dir"])
        destination = ensure_directory(output_dir / "representative" / str(row["example_id"]))
        input_record = read_json(source / "input.json")
        generation = read_json(source / "generation.json")
        shutil.copy2(source / "spans.json", destination / "spans.json")
        shutil.copy2(source / "plots" / "span_timeline.png", destination / "attention_uncertainty_timeline.png")
        image_source = Path(input_record["resolved_image_path"])
        image_destination = destination / ("input_image" + image_source.suffix.lower())
        shutil.copy2(image_source, image_destination)
        write_text(destination / "question.md", f"# Question\n\n{input_record['question']}")
        write_text(destination / "reasoning.md", f"# Complete generated response\n\n{generation['full_generated_response']}")
        with np.load(source / "attention_summary.npz", allow_pickle=False) as attention:
            visual_focus = attention["visual_focus"]
        token_rows = read_jsonl(source / "tokens.jsonl")
        focus_files = save_visual_focus_snapshots(
            image_source,
            visual_focus,
            input_record["visual_mapping"]["merged_grid_shape"],
            token_rows,
            destination / "visual_focus",
        )
        selection = {
            "example_id": row["example_id"],
            "variant": row["variant"],
            "selection_reason": reason,
            "descriptive_metrics": row["metrics"],
            "source_artifact_dir": row["artifact_dir"],
            "visual_focus_files": [str(path.relative_to(destination)) for path in focus_files],
            "boundary": "selected for descriptive diversity, not causal interpretation",
        }
        write_json(destination / "selection.json", selection)
        representative_rows.append(selection)
        response = str(generation["full_generated_response"])
        middle = max(0, len(response) // 2 - 600)
        representative_review_lines.extend(
            [
                f"## Example {row['example_id']} — {reason}",
                "",
                f"- Variant: {row['variant']}",
                f"- Length: {row['generated_token_count']} tokens",
                f"- Peaks: {row['metrics']['peak_count']}",
                f"- Mean visual mass: {row['metrics']['visual_mass_mean']:.6f}",
                f"- Mean / max focus turnover: {row['metrics']['focus_turnover_mean']:.6f} / {row['metrics']['focus_turnover_max']:.6f}",
                f"- Timeline: `{destination / 'attention_uncertainty_timeline.png'}`",
                "",
                "Beginning:",
                "",
                response[:1200],
                "",
                "Middle:",
                "",
                response[middle : middle + 1200],
                "",
                "Ending:",
                "",
                response[-1200:],
                "",
            ]
        )
    write_json(output_dir / "representative" / "representative_selection.json", {"count": len(representative_rows), "examples": representative_rows})
    write_text(output_dir / "manual_review" / "representative_review_packet.md", "\n".join(representative_review_lines))
    print(json.dumps({**preliminary, "timelines": len(enriched), "manual_review_packet": len(manual_rows), "representatives": len(representative_rows)}, indent=2))


if __name__ == "__main__":
    main()
