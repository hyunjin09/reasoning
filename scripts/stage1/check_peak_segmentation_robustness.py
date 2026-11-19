#!/usr/bin/env python3
"""Check whether Stage 1 candidate-peak recurrence depends on semantic segmentation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
from scipy.signal import find_peaks
from scipy.stats import spearmanr

from visual_reasoning.stage0.io import write_json


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def distribution(values: list[float]) -> dict[str, float | int]:
    array = np.asarray(values, dtype=np.float64)
    return {
        "count": int(array.size),
        "mean": float(array.mean()),
        "median": float(np.median(array)),
        "p10": float(np.percentile(array, 10)),
        "p90": float(np.percentile(array, 90)),
        "maximum": float(array.max()),
    }


def correlation(left: list[float], right: list[float]) -> dict[str, float | int | None]:
    if len(left) < 3 or np.std(left) == 0 or np.std(right) == 0:
        return {"n": len(left), "rho": None, "p_value": None}
    result = spearmanr(left, right)
    return {"n": len(left), "rho": float(result.statistic), "p_value": float(result.pvalue)}


def fixed_window_peaks(values: np.ndarray, width: int) -> tuple[np.ndarray, np.ndarray]:
    means = np.asarray(
        [values[start : min(len(values), start + width)].mean() for start in range(0, len(values), width)],
        dtype=np.float32,
    )
    if len(means) < 3:
        return means, np.empty((0,), dtype=np.int64)
    smoothed = np.convolve(
        np.pad(means, (1, 1), mode="edge"),
        np.asarray([0.25, 0.5, 0.25], dtype=np.float32),
        mode="valid",
    )
    threshold = max(float(smoothed.std()) * 0.5, np.finfo(np.float32).eps)
    positions, _properties = find_peaks(smoothed, prominence=threshold, distance=2)
    return means, positions


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohort-manifest", type=Path, required=True)
    parser.add_argument("--trajectory-metrics", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    cohort = read_jsonl(args.cohort_manifest)
    original = {str(row["example_id"]): row for row in read_jsonl(args.trajectory_metrics)}
    widths = (32, 64, 128)
    by_width: dict[int, list[dict[str, Any]]] = {width: [] for width in widths}
    all_span_lengths: list[int] = []
    per_trajectory_short: list[float] = []
    trace_lengths: list[float] = []

    for row in cohort:
        example_id = str(row["example_id"])
        artifact = Path(row["artifact_dir"])
        tokens = read_jsonl(artifact / "tokens.jsonl")
        spans = read_json(artifact / "spans.json")
        visual = np.asarray([float(token["visual_attention_mass"]) for token in tokens], dtype=np.float32)
        span_lengths = [int(span["end_token"]) - int(span["start_token"]) for span in spans]
        all_span_lengths.extend(span_lengths)
        per_trajectory_short.append(sum(length <= 2 for length in span_lengths) / len(span_lengths))
        trace_lengths.append(float(len(tokens)))
        for width in widths:
            windows, peaks = fixed_window_peaks(visual, width)
            positions = [float(((int(position) + 0.5) * width) / len(tokens)) for position in peaks]
            by_width[width].append(
                {
                    "example_id": example_id,
                    "generated_token_count": len(tokens),
                    "window_count": len(windows),
                    "peak_count": int(len(peaks)),
                    "peak_rate_per_1000_tokens": 1000.0 * len(peaks) / len(tokens),
                    "normalized_positions": positions,
                    "semantic_peak_count": int(original[example_id]["peak_count"]),
                    "semantic_peak_rate_per_1000_tokens": float(original[example_id]["peak_rate_per_1000_tokens"]),
                }
            )

    width_reports: dict[str, Any] = {}
    for width, rows in by_width.items():
        counts = [int(row["peak_count"]) for row in rows]
        rates = [float(row["peak_rate_per_1000_tokens"]) for row in rows]
        semantic_counts = [int(row["semantic_peak_count"]) for row in rows]
        semantic_rates = [float(row["semantic_peak_rate_per_1000_tokens"]) for row in rows]
        positions = [position for row in rows for position in row["normalized_positions"]]
        histogram, edges = np.histogram(positions, bins=np.linspace(0, 1, 11))
        width_reports[str(width)] = {
            "peak_count": distribution([float(value) for value in counts]),
            "peak_rate_per_1000_tokens": distribution(rates),
            "zero_peak_fraction": sum(value == 0 for value in counts) / len(counts),
            "one_peak_fraction": sum(value == 1 for value in counts) / len(counts),
            "two_or_more_peak_fraction": sum(value >= 2 for value in counts) / len(counts),
            "trace_length_vs_peak_count_spearman": correlation(trace_lengths, [float(value) for value in counts]),
            "semantic_vs_fixed_peak_count_spearman": correlation([float(value) for value in semantic_counts], [float(value) for value in counts]),
            "semantic_vs_fixed_peak_rate_spearman": correlation(semantic_rates, rates),
            "normalized_position_histogram": {"edges": edges.tolist(), "counts": histogram.tolist(), "total_peaks": len(positions)},
        }

    report = {
        "status": "complete",
        "purpose": "single decision-changing diagnostic after manual segmentation review",
        "cohort_count": len(cohort),
        "semantic_segmentation_fragmentation": {
            "span_token_length": distribution([float(value) for value in all_span_lengths]),
            "fraction_of_spans_at_most_2_tokens": sum(value <= 2 for value in all_span_lengths) / len(all_span_lengths),
            "fraction_of_spans_at_most_5_tokens": sum(value <= 5 for value in all_span_lengths) / len(all_span_lengths),
            "per_trajectory_fraction_at_most_2_tokens": distribution(per_trajectory_short),
            "trace_length_vs_short_span_fraction_spearman": correlation(trace_lengths, per_trajectory_short),
        },
        "fixed_token_windows": width_reports,
        "detector": "non-overlapping fixed token windows; three-window [0.25,0.5,0.25] smoothing; per-example prominence=0.5*SD; minimum distance=2 windows",
        "decision_boundary": "robustness of descriptive recurrence only; fixed windows do not validate semantic labels and do not imply causal visual usage",
    }
    write_json(args.output, report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
