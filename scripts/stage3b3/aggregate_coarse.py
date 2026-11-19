#!/usr/bin/env python3
"""Aggregate Stage 3B.3 coarse shards and apply the frozen fine-scan gate."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from visual_reasoning.stage0.io import write_json, write_jsonl
from visual_reasoning.stage3b3.windows import fine_two_layer_windows


ROOT = Path(__file__).resolve().parents[2]
SEED = 1_234


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def bootstrap_ci(values: list[float], statistic: str, draws: int = 10_000) -> list[float]:
    array = np.asarray(values, dtype=np.float64)
    if not len(array):
        return [float("nan"), float("nan")]
    rng = np.random.default_rng(SEED)
    sampled = array[rng.integers(0, len(array), size=(draws, len(array)))]
    boot = np.median(sampled, axis=1) if statistic == "median" else np.mean(sampled, axis=1)
    return [float(value) for value in np.quantile(boot, [0.025, 0.975])]


def summary(values: list[float]) -> dict[str, Any]:
    finite = [float(value) for value in values if value is not None and np.isfinite(value)]
    return {
        "N": len(finite),
        "mean": float(np.mean(finite)),
        "median": float(np.median(finite)),
        "mean_bootstrap_95_ci": bootstrap_ci(finite, "mean"),
        "median_bootstrap_95_ci": bootstrap_ci(finite, "median"),
        "minimum": min(finite),
        "maximum": max(finite),
    }


def grouped_statistics(
    rows: list[dict[str, Any]],
    *,
    key_fields: tuple[str, ...],
    metrics: tuple[str, ...],
    consistency_field: str | None = None,
    sham_field: str | None = None,
) -> list[dict[str, Any]]:
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[tuple(row[field] for field in key_fields)].append(row)
    result = []
    for key, group in sorted(groups.items()):
        entry = {field: value for field, value in zip(key_fields, key)}
        entry["N"] = len(group)
        entry["statistics"] = {
            metric: summary([row[metric] for row in group if row.get(metric) is not None])
            for metric in metrics
        }
        if consistency_field:
            entry["bidirectional_consistency_count"] = sum(
                bool(row[consistency_field]) for row in group
            )
            entry["bidirectional_consistency_fraction"] = (
                entry["bidirectional_consistency_count"] / len(group)
            )
        if sham_field:
            entry["sham_effect"] = summary([float(row[sham_field]) for row in group])
        result.append(entry)
    return result


def compact(source: dict[str, Any], *, drop: tuple[str, ...] = ("controls",)) -> dict[str, Any]:
    return {key: value for key, value in source.items() if key not in drop}


def apply_fine_rule(coarse_stats: list[dict[str, Any]]) -> dict[str, Any]:
    by_key = {
        (row["coordinate"], row["name"]): row for row in coarse_stats
    }
    qualified: dict[str, list[str]] = defaultdict(list)
    audit_rows = []
    for coordinate in ("Ed_minus_1", "Ed"):
        for index in range(6):
            name = f"W{index}"
            row = by_key[(coordinate, name)]
            bws = row["statistics"]["BWS_normalized"]
            bwn = row["statistics"]["BWN_normalized"]
            threshold_bws = bws["median"] >= 0.20
            threshold_bwn = bwn["median"] >= 0.20
            separated = {}
            for metric, stats in (("BWS_normalized", bws), ("BWN_normalized", bwn)):
                candidate_low = stats["median_bootstrap_95_ci"][0]
                comparisons = []
                for other in range(6):
                    if abs(other - index) < 2:
                        continue
                    other_high = by_key[(coordinate, f"W{other}")]["statistics"][metric][
                        "median_bootstrap_95_ci"
                    ][1]
                    if candidate_low > other_high:
                        comparisons.append(f"W{other}")
                separated[metric] = comparisons
            ci_qualified = any(len(values) >= 2 for values in separated.values())
            passed = threshold_bws or threshold_bwn or ci_qualified
            if passed:
                qualified[coordinate].append(name)
            audit_rows.append(
                {
                    "coordinate": coordinate,
                    "coarse_window": name,
                    "median_normalized_BWS": bws["median"],
                    "median_normalized_BWN": bwn["median"],
                    "BWS_threshold_pass": threshold_bws,
                    "BWN_threshold_pass": threshold_bwn,
                    "CI_separated_nonadjacent_windows": separated,
                    "CI_separation_pass": ci_qualified,
                    "qualifies": passed,
                }
            )
    union = sorted({name for values in qualified.values() for name in values})
    fine = fine_two_layer_windows(union)
    return {
        "qualified_by_coordinate": dict(qualified),
        "qualifying_union": union,
        "fine_windows": fine,
        "audit": audit_rows,
        "attention_used": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-root", type=Path, required=True)
    args = parser.parse_args()
    raw_root = args.raw_root.resolve()
    raw_root.relative_to((ROOT / "outputs/stage3b3/raw/coarse").resolve())
    paths = sorted(raw_root.glob("cohort_*/results.jsonl"))
    if len(paths) != 7:
        raise RuntimeError(f"Expected seven completed coarse shards, observed {len(paths)}")
    rows = [row for path in paths for row in read_jsonl(path)]
    bases = [str(row["base_problem_id"]) for row in rows]
    if len(rows) != 49 or len(set(bases)) != 49:
        raise RuntimeError(f"Expected 49 unique bases, observed {len(rows)} rows/{len(set(bases))} unique")

    switch_rows: list[dict[str, Any]] = []
    restoration_rows: list[dict[str, Any]] = []
    cumulative_rows: list[dict[str, Any]] = []
    activation_rows: list[dict[str, Any]] = []
    positive_rows: list[dict[str, Any]] = []
    for problem in rows:
        metadata = {
            "base_problem_id": str(problem["base_problem_id"]),
            "example_id": str(problem["example_id"]),
            "evidence_type": problem["evidence_type"],
            "ed_alignment": problem["ed_alignment"],
        }
        for coordinate in problem["coordinates"]:
            coordinate_meta = {
                **metadata,
                "coordinate": coordinate["coordinate"],
                "switch_generated_index": coordinate["switch_generated_index"],
                "stage3b2_all_layer_BRI": coordinate["stage3b2_all_layer_BRI"],
            }
            switch_rows.extend(
                {**coordinate_meta, **compact(entry)} for entry in coordinate["coarse_sufficiency"]
            )
            restoration_rows.extend(
                {**coordinate_meta, **compact(entry)} for entry in coordinate["coarse_necessity"]
            )
            cumulative_rows.extend(
                {**coordinate_meta, **compact(entry)} for entry in coordinate["cumulative"]
            )
            positive_rows.append(
                {
                    **coordinate_meta,
                    **coordinate["positive_control"],
                    "all_self_exact": coordinate["all_self_exact"],
                    "all_audits_valid": coordinate["all_audits_valid"],
                    "all_finite": coordinate["all_finite"],
                }
            )
        activation_rows.extend(
            {**metadata, "coordinate": "Ed", **compact(entry)}
            for entry in problem["activation_patches"]
        )

    scoring = ROOT / "outputs/stage3b3/scoring"
    write_jsonl(scoring / "coarse_window_switch_results.jsonl", switch_rows)
    write_jsonl(scoring / "coarse_window_restoration_results.jsonl", restoration_rows)
    write_jsonl(scoring / "cumulative_layer_results.jsonl", cumulative_rows)
    write_jsonl(scoring / "activation_patch_results.jsonl", activation_rows)
    write_jsonl(scoring / "positive_control_results.jsonl", positive_rows)

    combined_by_key: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in switch_rows:
        combined_by_key[(row["base_problem_id"], row["coordinate"], row["name"])] = dict(row)
    for row in restoration_rows:
        combined_by_key[(row["base_problem_id"], row["coordinate"], row["name"])].update(
            {key: value for key, value in row.items() if key.startswith("BWN") or key.startswith("N_W") or key.startswith("sham_restoration") or key.startswith("O_restoration") or key.startswith("C_restoration") or key == "bidirectionally_source_consistent"}
        )
        combined_by_key[(row["base_problem_id"], row["coordinate"], row["name"])][
            "necessity_bidirectionally_source_consistent"
        ] = row["bidirectionally_source_consistent"]
    combined = list(combined_by_key.values())
    coarse_stats = grouped_statistics(
        combined,
        key_fields=("coordinate", "name"),
        metrics=("BWS", "BWS_normalized", "BWN", "BWN_normalized"),
    )
    # Add direction/control rates independently for clarity.
    for stat in coarse_stats:
        relevant_s = [row for row in switch_rows if row["coordinate"] == stat["coordinate"] and row["name"] == stat["name"]]
        relevant_n = [row for row in restoration_rows if row["coordinate"] == stat["coordinate"] and row["name"] == stat["name"]]
        stat["sufficiency_bidirectional_fraction"] = sum(row["bidirectionally_source_consistent"] for row in relevant_s) / len(relevant_s)
        stat["necessity_bidirectional_fraction"] = sum(row["bidirectionally_source_consistent"] for row in relevant_n) / len(relevant_n)
        stat["sufficiency_sham"] = summary([row["sham_window_shift"] for row in relevant_s])
        stat["necessity_sham"] = summary([row["sham_restoration_shift"] for row in relevant_n])

    sufficiency_stats = grouped_statistics(
        switch_rows,
        key_fields=("coordinate", "name"),
        metrics=("S_W_O_to_C", "S_W_C_to_O", "BWS", "BWS_normalized"),
        consistency_field="bidirectionally_source_consistent",
        sham_field="sham_window_shift",
    )
    necessity_stats = grouped_statistics(
        restoration_rows,
        key_fields=("coordinate", "name"),
        metrics=("N_W_O", "N_W_C", "BWN", "BWN_normalized"),
        consistency_field="bidirectionally_source_consistent",
        sham_field="sham_restoration_shift",
    )
    cumulative_stats = grouped_statistics(
        cumulative_rows,
        key_fields=("coordinate", "family", "name"),
        metrics=("BWS", "BWS_normalized"),
        consistency_field="bidirectionally_source_consistent",
        sham_field="sham_window_shift",
    )
    activation_stats = grouped_statistics(
        activation_rows,
        key_fields=("after_layer",),
        metrics=("A_O_receive_C", "A_C_receive_O", "BAP", "BAP_normalized"),
        consistency_field="bidirectionally_source_consistent",
        sham_field="sham_activation_shift",
    )
    fine_gate = apply_fine_rule(coarse_stats)

    analysis = ROOT / "outputs/stage3b3/analysis"
    write_json(analysis / "coarse_layer_statistics.json", {"base_problem_count": 49, "rows": coarse_stats})
    write_json(analysis / "window_sufficiency_statistics.json", {"rows": sufficiency_stats})
    write_json(analysis / "window_necessity_statistics.json", {"rows": necessity_stats})
    write_json(analysis / "cumulative_transfer_statistics.json", {"rows": cumulative_stats})
    write_json(analysis / "activation_patch_statistics.json", {"rows": activation_stats})
    write_json(analysis / "fine_localization_gate.json", fine_gate)
    write_json(
        ROOT / "outputs/stage3b3/config/fine_layer_windows.json",
        {
            "source_rule": "outputs/stage3b3/config/fine_localization_rule.json",
            "coarse_results_frozen_before_application": True,
            **fine_gate,
        },
    )

    exact_bases = {row["base_problem_id"] for row in rows if row["ed_alignment"] == "exact_baseline_tokens"}
    exact_switch = [row for row in switch_rows if row["base_problem_id"] in exact_bases]
    exact_restore = [row for row in restoration_rows if row["base_problem_id"] in exact_bases]
    exact_cumulative = [row for row in cumulative_rows if row["base_problem_id"] in exact_bases]
    exact_activation = [row for row in activation_rows if row["base_problem_id"] in exact_bases]
    write_json(
        analysis / "exact_baseline_robustness.json",
        {
            "N": len(exact_bases),
            "base_problem_ids": sorted(exact_bases, key=int),
            "sufficiency": grouped_statistics(exact_switch, key_fields=("coordinate", "name"), metrics=("BWS", "BWS_normalized")),
            "necessity": grouped_statistics(exact_restore, key_fields=("coordinate", "name"), metrics=("BWN", "BWN_normalized")),
            "cumulative": grouped_statistics(exact_cumulative, key_fields=("coordinate", "family", "name"), metrics=("BWS", "BWS_normalized")),
            "activation": grouped_statistics(exact_activation, key_fields=("after_layer",), metrics=("BAP", "BAP_normalized")),
        },
    )
    evidence = {}
    for evidence_type in sorted({row["evidence_type"] for row in rows}):
        selected = {row["base_problem_id"] for row in rows if row["evidence_type"] == evidence_type}
        evidence[evidence_type] = {
            "N": len(selected),
            "sufficiency": grouped_statistics([row for row in switch_rows if row["base_problem_id"] in selected], key_fields=("coordinate", "name"), metrics=("BWS", "BWS_normalized")),
            "necessity": grouped_statistics([row for row in restoration_rows if row["base_problem_id"] in selected], key_fields=("coordinate", "name"), metrics=("BWN", "BWN_normalized")),
            "activation": grouped_statistics([row for row in activation_rows if row["base_problem_id"] in selected], key_fields=("after_layer",), metrics=("BAP", "BAP_normalized")),
        }
    write_json(analysis / "evidence_type_analysis.json", evidence)
    write_json(
        analysis / "coarse_aggregation_validation.json",
        {
            "status": "PASS",
            "base_problem_count": len(rows),
            "unique_base_problem_count": len(set(bases)),
            "evidence_type_counts": dict(Counter(row["evidence_type"] for row in rows)),
            "alignment_counts": dict(Counter(row["ed_alignment"] for row in rows)),
            "switch_rows": len(switch_rows),
            "restoration_rows": len(restoration_rows),
            "cumulative_rows": len(cumulative_rows),
            "activation_rows": len(activation_rows),
            "positive_control_rows": len(positive_rows),
            "all_positive_controls_exact": all(all(value for key, value in row.items() if key.endswith("exact_stage3b2")) for row in positive_rows),
            "all_self_and_audits_valid": all(row["all_self_exact"] and row["all_audits_valid"] and row["all_finite"] for row in positive_rows),
            "selection_used_attention": False,
        },
    )
    print(json.dumps({"bases": len(rows), "fine_gate": fine_gate["qualifying_union"], "fine_windows": len(fine_gate["fine_windows"])}, indent=2))


if __name__ == "__main__":
    main()
