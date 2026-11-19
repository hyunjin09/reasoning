#!/usr/bin/env python3
"""Independently validate Stage 3C.4 raw mechanics and derived claims."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import wilcoxon


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c4"
TOLERANCE = 1e-6


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def result_map(root: Path) -> dict[str, dict[str, Any]]:
    return {
        str(row["base_problem_id"]): row
        for path in sorted(root.glob("shard_*/examples/*/result.json"))
        for row in [read_json(path)]
    }


def holm(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=values.__getitem__)
    adjusted = [1.0] * len(values)
    running = 0.0
    for rank, index in enumerate(order):
        running = max(running, min(1.0, (len(values) - rank) * values[index]))
        adjusted[index] = running
    return adjusted


def one_sided(values: list[float]) -> float:
    try:
        return float(wilcoxon(np.asarray(values), alternative="greater").pvalue)
    except ValueError:
        return 1.0


def main() -> None:
    config = read_json(OUT / "config/stage3c4_config.json")
    primary = [str(value) for value in config["primary_base_problem_ids"]]
    all_heads = list(range(32))
    layer_scopes = read_json(OUT / "config/layer_scopes.json")["scopes"]
    temporal = read_json(OUT / "config/temporal_windows.json")["backward_offsets"]
    interactions = read_json(OUT / "config/interaction_cells.json")["cells"]
    raw = {phase: result_map(OUT / f"raw/{phase}") for phase in ("phase_a", "phase_b", "phase_c")}
    schedule_errors = []
    mechanical_errors = []
    audit_count = 0
    max_partition = 0.0
    for phase, rows in raw.items():
        if set(rows) != set(primary):
            schedule_errors.append(f"{phase}: cohort mismatch")
        for base in primary:
            row = rows[base]
            if row["selection_used_attention"] or row["sink_directly_intervened"] or row["donor_state_patched"]:
                mechanical_errors.append(f"{phase}/{base}: prohibited intervention or selection flag")
            for target_id, target in row["target_results"].items():
                current = int(target["retrieval_generated_index"])
                if phase == "phase_a":
                    expected = {
                        label: {"layers": values, "queries": [current], "source": "T"}
                        for label, values in layer_scopes.items()
                    }
                elif phase == "phase_b":
                    expected = {
                        label: {
                            "layers": layer_scopes["L4"],
                            "queries": list(range(current - int(backward), current + 1)),
                            "source": "T",
                        }
                        for label, backward in temporal.items()
                    }
                else:
                    expected = {
                        label: {
                            "layers": spec["layers"],
                            "queries": list(range(current - int(spec["backward"]), current + 1)),
                            "source": "T",
                        }
                        for label, spec in interactions.items()
                    }
                    for source in ("M", "I"):
                        for label in ("T0", "T4"):
                            expected[f"{source}_{label}"] = {
                                "layers": layer_scopes["L4"],
                                "queries": list(range(current - int(temporal[label]), current + 1)),
                                "source": source,
                            }
                if set(target["arms"]) != set(expected):
                    schedule_errors.append(f"{phase}/{base}/{target_id}: arm family mismatch")
                    continue
                for arm_id, spec in expected.items():
                    arm = target["arms"][arm_id]
                    score = arm["score"]
                    if arm["layer_indices"] != spec["layers"] or arm["query_generated_indices"] != spec["queries"]:
                        schedule_errors.append(f"{phase}/{base}/{target_id}/{arm_id}: scope mismatch")
                    if arm["source_group"] != spec["source"]:
                        schedule_errors.append(f"{phase}/{base}/{target_id}/{arm_id}: source mismatch")
                    if not score["finite"] or not math.isfinite(float(score["D"])):
                        mechanical_errors.append(f"{phase}/{base}/{target_id}/{arm_id}: nonfinite score")
                    expected_absolute = score["absolute_query_positions"]
                    for candidate_audits in score["candidate_audits"].values():
                        if [int(audit["layer_index"]) for audit in candidate_audits] != spec["layers"]:
                            schedule_errors.append(f"{phase}/{base}/{target_id}/{arm_id}: layer audit mismatch")
                        for audit in candidate_audits:
                            audit_count += 1
                            max_partition = max(max_partition, float(audit["partition_max_abs_error"]))
                            if audit["selected_heads"] != all_heads:
                                mechanical_errors.append(f"{phase}/{base}/{target_id}/{arm_id}: head enumeration")
                            if audit["source_positions"] != row["source_groups"][spec["source"]]:
                                mechanical_errors.append(f"{phase}/{base}/{target_id}/{arm_id}: ROI mismatch")
                            if audit["query_positions"] != expected_absolute:
                                mechanical_errors.append(f"{phase}/{base}/{target_id}/{arm_id}: absolute queries")
                            zero_fields = (
                                "selected_head_expected_max_abs_error", "nonselected_head_max_abs_delta",
                                "outside_window_max_abs_delta", "query_max_abs_delta", "key_max_abs_delta",
                                "value_max_abs_delta", "attention_max_abs_delta",
                            )
                            if any(float(audit[field]) != 0.0 for field in zero_fields):
                                mechanical_errors.append(f"{phase}/{base}/{target_id}/{arm_id}: isolation")
                            if not audit["lambda_zero_exact"] or not audit["all_outputs_finite"]:
                                mechanical_errors.append(f"{phase}/{base}/{target_id}/{arm_id}: endpoint/finite")

    w4_exact = []
    current_exact = []
    c3_exact = []
    c4_exact = []
    historical = result_map(ROOT / "outputs/stage3c3r/raw/phase_b")
    for base in primary:
        for target in ("target_a", "target_b"):
            phase_a_target = raw["phase_a"][base]["target_results"][target]
            phase_b_target = raw["phase_b"][base]["target_results"][target]
            phase_c_target = raw["phase_c"][base]["target_results"][target]
            w4_exact.append(
                float(phase_a_target["arms"]["L0"]["score"]["D"])
                == float(historical[base]["target_results"][target]["arms"]["R3"]["lambda_results"]["0.0"]["D"])
            )
            current_exact.append(
                float(phase_a_target["arms"]["L4"]["score"]["D"])
                == float(phase_b_target["arms"]["T0"]["score"]["D"])
            )
            c3_exact.append(
                float(phase_c_target["arms"]["C3"]["score"]["D"])
                == float(phase_b_target["arms"]["T4"]["score"]["D"])
            )
            c4_exact.append(
                float(phase_c_target["arms"]["C4"]["score"]["D"])
                == float(phase_b_target["arms"]["T8"]["score"]["D"])
            )

    # Recompute every base-level confirmatory vector directly from raw scores.
    vectors: dict[str, list[float]] = {name: [] for name in read_json(OUT / "config/primary_family.json")["tests"]}
    x_layer = np.arange(5, dtype=np.float64)
    x_time = np.arange(6, dtype=np.float64)
    for base in primary:
        base_layer = {
            label: float(np.mean([
                raw["phase_a"][base]["target_results"][target]["arms"][label]["score"]["D"]
                for target in ("target_a", "target_b")
            ]))
            for label in layer_scopes
        }
        for label in ("L1", "L2", "L3", "L4"):
            vectors[f"{label}_vs_L0"].append(base_layer["L0"] - base_layer[label])
        vectors["monotonic_layer_scope_trend"].append(
            float(-np.polyfit(x_layer, [base_layer[label] for label in layer_scopes], 1)[0])
        )
        base_time = {
            label: float(np.mean([
                raw["phase_b"][base]["target_results"][target]["arms"][label]["score"]["D"]
                for target in ("target_a", "target_b")
            ]))
            for label in temporal
        }
        for label in ("T1", "T2", "T4", "T8", "T16"):
            vectors[f"{label}_vs_T0"].append(base_time["T0"] - base_time[label])
        vectors["monotonic_temporal_window_trend"].append(
            float(-np.polyfit(x_time, [base_time[label] for label in temporal], 1)[0])
        )
        for control, family_name in (("M", "T_vs_M_suppression"), ("I", "T_vs_I_suppression")):
            contrasts = []
            for target in ("target_a", "target_b"):
                native = float(raw["phase_c"][base]["target_results"][target]["native"]["D"])
                for window in ("T0", "T4"):
                    target_d = float(raw["phase_b"][base]["target_results"][target]["arms"][window]["score"]["D"])
                    control_d = float(raw["phase_c"][base]["target_results"][target]["arms"][f"{control}_{window}"]["score"]["D"])
                    contrasts.append((native - target_d) - (native - control_d))
            vectors[family_name].append(float(np.mean(contrasts)))
        interactions_per_target = []
        for target in ("target_a", "target_b"):
            target_arms = raw["phase_c"][base]["target_results"][target]["arms"]
            interactions_per_target.extend([
                float(target_arms["C1"]["score"]["D"]) - float(target_arms["C3"]["score"]["D"]),
                float(target_arms["C2"]["score"]["D"]) - float(target_arms["C4"]["score"]["D"]),
            ])
        vectors["frozen_layer_by_time_interaction"].append(float(np.mean(interactions_per_target)))
    names = list(vectors)
    raw_p = [one_sided(vectors[name]) for name in names]
    adjusted = holm(raw_p)
    persisted_family = {row["test"]: row for row in read_json(OUT / "analysis/primary_family_statistics.json")["rows"]}
    statistical_errors = []
    for name, values, p_value, adjusted_p in zip(names, vectors.values(), raw_p, adjusted):
        persisted = persisted_family[name]
        comparisons = (
            math.isclose(float(persisted["median"]), float(np.median(values)), abs_tol=1e-12),
            math.isclose(float(persisted["mean"]), float(np.mean(values)), abs_tol=1e-12),
            math.isclose(float(persisted["raw_p"]), p_value, abs_tol=1e-12),
            math.isclose(float(persisted["holm_adjusted_p"]), adjusted_p, abs_tol=1e-12),
        )
        if not all(comparisons):
            statistical_errors.append(name)

    phase_a_derived = {str(row["base_problem_id"]): row for row in read_jsonl(OUT / "phase_a_layer/per_problem_layer_scope_results.jsonl")}
    phase_b_derived = {str(row["base_problem_id"]): row for row in read_jsonl(OUT / "phase_b_time/per_problem_temporal_results.jsonl")}
    phase_c_derived = {str(row["base_problem_id"]): row for row in read_jsonl(OUT / "phase_c_interaction/interaction_results.jsonl")}
    derived_cohorts_exact = all(set(rows) == set(primary) for rows in (phase_a_derived, phase_b_derived, phase_c_derived))
    classification = read_json(OUT / "analysis/spatiotemporal_classification.json")
    class_values = classification["joint_values"]
    classification_rule_recomputed = (
        "O1_layer_redundancy" if class_values["layer_l4_retention"] < 0.8
        else "O4_earlier_nonvisual_storage" if class_values["time_t16_retention"] >= 0.8
        else "O3_spatiotemporal_redundancy" if class_values["c_late4_retention"] >= 0.8 and class_values["c_all4_retention"] < 0.8
        else "O2_temporal_redundancy"
    )
    required_outputs = [
        OUT / "phase_a_layer/layer_scope_statistics.json",
        OUT / "phase_b_time/temporal_statistics.json",
        OUT / "phase_b_time/temporal_necessity_summary.json",
        OUT / "phase_c_interaction/interaction_statistics.json",
        OUT / "controls/mention_suppression_results.jsonl",
        OUT / "controls/irrelevant_suppression_results.jsonl",
        OUT / "secondary/stage3b2_comparison.json",
        OUT / "secondary/optional_state_readout.jsonl",
        OUT / "summaries/stage3c4_summary.md",
        OUT / "summaries/stage3c4_acceptance.json",
        OUT / "summaries/next_stage_recommendation.md",
    ]
    checks = {
        "exact_primary_cohorts": all(set(rows) == set(primary) for rows in raw.values()),
        "exact_frozen_schedules": not schedule_errors,
        "all_32_heads": not any("head enumeration" in value for value in mechanical_errors),
        "target_roi_only": not any("ROI mismatch" in value for value in mechanical_errors),
        "local_qkv_attention_invariance": not any("isolation" in value for value in mechanical_errors),
        "outside_window_invariance": not any("isolation" in value for value in mechanical_errors),
        "finite_and_exact_endpoints": not mechanical_errors and max_partition <= TOLERANCE,
        "w4_historical_reproduction": all(w4_exact),
        "phase_a_b_current_reproduction": all(current_exact),
        "phase_b_c_interaction_reproduction": all(c3_exact) and all(c4_exact),
        "derived_cohorts_exact": derived_cohorts_exact,
        "primary_family_recomputed": not statistical_errors and len(persisted_family) == 14,
        "classification_recomputed": classification["classification"] == classification_rule_recomputed,
        "base_problem_is_statistical_unit": read_json(OUT / "analysis/primary_family_statistics.json")["primary_unit"] == "base_problem_id",
        "unnormalized_effect_is_primary": read_json(OUT / "config/primary_family.json")["primary_readout"].startswith("unnormalized"),
        "required_machine_outputs_exist": (
            all(path.exists() for path in required_outputs)
            and len(list((OUT / "analysis/figures").glob("*.png"))) == 13
        ),
        "no_optional_state_patching": (OUT / "secondary/optional_state_readout.jsonl").read_text(encoding="utf-8") == "",
        "no_sink_or_donor_intervention": all(
            not rows[base]["sink_directly_intervened"] and not rows[base]["donor_state_patched"]
            for rows in raw.values() for base in primary
        ),
        "no_earlier_than_16_window": min(
            min(arm["query_generated_indices"])
            - int(target["retrieval_generated_index"])
            for rows in raw.values() for base in primary
            for target in rows[base]["target_results"].values()
            for arm in target["arms"].values()
        ) >= -16,
        "exactly_one_recommendation_field": isinstance(classification.get("recommendation"), str),
    }
    validation = {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "passed": sum(checks.values()),
        "total": len(checks),
        "N_unique_primary_bases": len(primary),
        "raw_result_counts": {phase: len(rows) for phase, rows in raw.items()},
        "patched_layer_candidate_audit_count": audit_count,
        "maximum_partition_error": max_partition,
        "tolerance": TOLERANCE,
        "schedule_errors": schedule_errors,
        "mechanical_errors": mechanical_errors,
        "statistical_errors": statistical_errors,
        "w4_exact_count": sum(w4_exact),
        "current_cross_phase_exact_count": sum(current_exact),
        "interaction_cross_phase_exact_count": sum(c3_exact) + sum(c4_exact),
        "classification": classification_rule_recomputed,
    }
    write_json(OUT / "audit/artifact_validation.json", validation)
    print(json.dumps(validation, indent=2))
    if validation["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
