#!/usr/bin/env python3
"""Aggregate primary Stage 3C.3 query-only interventions and evaluate its gate."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import wilcoxon

from visual_reasoning.stage3c2.metrics import holm_adjust
from visual_reasoning.stage3c3.protocol import phase_a_target_passes


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c3"
TARGETS = ("target_a", "target_b")
DIRECTIONS = ("necessity", "sufficiency")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=OUT / "phase_a_query/raw")
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, allow_nan=False) + "\n" for row in rows), encoding="utf-8")


def summary(values: list[float], *, seed: int = 20260903, draws: int = 10_000) -> dict[str, Any]:
    data = np.asarray(values, dtype=np.float64)
    if data.size == 0 or not np.isfinite(data).all():
        raise ValueError("Statistics require nonempty finite values")
    rng = np.random.default_rng(seed)
    boot = data[rng.integers(0, data.size, size=(draws, data.size))].mean(axis=1)
    try:
        p = float(wilcoxon(data, alternative="greater").pvalue) if np.any(data != 0) else 1.0
    except ValueError:
        p = 1.0
    return {
        "N": int(data.size),
        "mean": float(data.mean()),
        "median": float(np.median(data)),
        "bootstrap_mean_95_CI": [float(np.quantile(boot, 0.025)), float(np.quantile(boot, 0.975))],
        "positive_count": int(np.sum(data > 0)),
        "positive_fraction": float(np.mean(data > 0)),
        "wilcoxon_one_sided_greater_p": p,
        "values": data.tolist(),
    }


def group_metrics(routing: dict[str, Any], group: str) -> dict[str, float]:
    row = routing["groups"][group]
    return {
        "qk_cosine": float(row["mean_qk_cosine"]),
        "raw_qk_dot": float(row["mean_raw_qk_dot"]),
        "scaled_logit": float(row["mean_scaled_logit"]),
        "attention_mass": float(row["mean_attention_mass"]),
        "attention_density": float(row["mean_attention_density"]),
        "alpha_v_norm": float(row["mean_alpha_v_norm"]),
        "post_wo_norm": float(row["mean_post_wo_norm"]),
        "head_set_post_wo_sum_norm": float(row["head_set_post_wo_sum_norm"]),
    }


def signed_pair(
    target: dict[str, Any], form: str, role: str, direction: str
) -> tuple[dict[str, Any], dict[str, Any], float, float]:
    if direction == "necessity":
        native = target["native"]["R"]
        patched = target["forms"][form][role]["Q_R_to_Q_M"]
        sign = -1.0
    else:
        native = target["native"]["M"]
        patched = target["forms"][form][role]["Q_M_to_Q_R"]
        sign = 1.0
    # effect = native-patched for necessity and patched-native for sufficiency.
    evidence_effect = sign * (float(patched["preference"]["D"]) - float(native["preference"]["D"]))
    return native, patched, sign, evidence_effect


def main() -> None:
    args = parse_args()
    paths = sorted(args.input_dir.glob("shard_*/examples/*/result.json"))
    rows = [read_json(path) for path in paths]
    manifest = read_jsonl(OUT / "cohort/primary_manifest.jsonl")
    expected = {str(row["base_problem_id"]) for row in manifest}
    observed = {str(row["base_problem_id"]) for row in rows}
    if observed != expected or len(rows) != 24:
        raise RuntimeError(f"Primary Phase A incomplete: expected={sorted(expected)} observed={sorted(observed)}")
    formulation = read_json(OUT / "config/rope_query_formulation.json")
    form = str(formulation["selected_form"])
    if formulation["status"] != "frozen_before_primary_scoring" or not formulation["primary_scoring_started"]:
        raise RuntimeError("Query formulation was not frozen before primary scoring")

    lexical = {str(row["base_problem_id"]): bool(row["strong_lexical_match"]) for row in read_jsonl(OUT / "cohort/lexical_match_subset.jsonl")}
    routing_rows: list[dict[str, Any]] = []
    value_rows: list[dict[str, Any]] = []
    evidence_rows: list[dict[str, Any]] = []
    control_rows: list[dict[str, Any]] = []
    sink_rows: list[dict[str, Any]] = []
    per_problem: list[dict[str, Any]] = []
    effects: dict[str, dict[str, dict[str, list[float]]]] = {
        target: {
            direction: {metric: [] for metric in ("RDS_T_vs_M", "ADG_T_vs_M", "alpha_v_T", "evidence")}
            for direction in DIRECTIONS
        }
        for target in TARGETS
    }
    control_difference: dict[str, list[float]] = {target: [] for target in TARGETS}
    self_exact: dict[str, list[bool]] = {target: [] for target in TARGETS}

    for row in sorted(rows, key=lambda item: int(item["base_problem_id"])):
        base = str(row["base_problem_id"])
        problem_row: dict[str, Any] = {
            "base_problem_id": base,
            "example_id": str(row["example_id"]),
            "lexical_match_subset": lexical.get(base, False),
            "targets": {},
        }
        for target_id in TARGETS:
            target = row["target_results"][target_id]["O"]
            target_problem: dict[str, Any] = {"roles": {}}
            for state in ("M", "R"):
                arm = target["forms"][form]["causal"][f"self_{state}"]
                native = target["native"][state]["preference"]
                exact = bool(
                    arm["preference"]["D"] == native["D"]
                    and all(audit["selected_head_max_abs_delta"] == 0.0 for audit in arm["query_patch_audits"])
                )
                self_exact[target_id].append(exact)
            role_rds: dict[str, list[float]] = {"causal": [], "noncausal": []}
            for role in ("causal", "noncausal"):
                target_problem["roles"][role] = {}
                for direction in DIRECTIONS:
                    native, patched, sign, evidence_effect = signed_pair(target, form, role, direction)
                    native_routing = native["routing"][role]
                    patched_routing = patched["routing"]
                    routing_effects = {
                        "RDS_T_vs_M": sign * (float(patched_routing["RDS_T_vs_M"]) - float(native_routing["RDS_T_vs_M"])),
                        "ADG_T_vs_M": sign * (float(patched_routing["ADG_T_vs_M"]) - float(native_routing["ADG_T_vs_M"])),
                        "RDS_T_vs_I": sign * (float(patched_routing["RDS_T_vs_I"]) - float(native_routing["RDS_T_vs_I"])),
                        "ADG_T_vs_I": sign * (float(patched_routing["ADG_T_vs_I"]) - float(native_routing["ADG_T_vs_I"])),
                    }
                    role_rds[role].append(routing_effects["RDS_T_vs_M"])
                    routing_rows.append({
                        "base_problem_id": base,
                        "target_id": target_id,
                        "head_role": role,
                        "direction": direction,
                        "form": form,
                        "effect_sign_definition": "native_minus_patch" if direction == "necessity" else "patch_minus_native",
                        "native": {key: float(native_routing[key]) for key in ("RDS_T_vs_M", "ADG_T_vs_M", "RDS_T_vs_I", "ADG_T_vs_I")},
                        "patched": {key: float(patched_routing[key]) for key in ("RDS_T_vs_M", "ADG_T_vs_M", "RDS_T_vs_I", "ADG_T_vs_I")},
                        "effect": routing_effects,
                        "per_head_native": native_routing["per_head"],
                        "per_head_patched": patched_routing["per_head"],
                    })
                    group_effects: dict[str, Any] = {}
                    for group in ("T", "M", "I", "sink"):
                        native_group = group_metrics(native_routing, group)
                        patched_group = group_metrics(patched_routing, group)
                        group_effects[group] = {
                            key: sign * (patched_group[key] - native_group[key]) for key in native_group
                        }
                        value_rows.append({
                            "base_problem_id": base,
                            "target_id": target_id,
                            "head_role": role,
                            "direction": direction,
                            "group": group,
                            "native": native_group,
                            "patched": patched_group,
                            "effect": group_effects[group],
                        })
                    evidence_rows.append({
                        "base_problem_id": base,
                        "target_id": target_id,
                        "head_role": role,
                        "direction": direction,
                        "native_D": float(native["preference"]["D"]),
                        "patched_D": float(patched["preference"]["D"]),
                        "effect": evidence_effect,
                    })
                    sink_rows.append({
                        "base_problem_id": base,
                        "target_id": target_id,
                        "head_role": role,
                        "direction": direction,
                        "native": group_metrics(native_routing, "sink"),
                        "patched": group_metrics(patched_routing, "sink"),
                        "effect": group_effects["sink"],
                        "sink_directly_intervened": False,
                    })
                    target_problem["roles"][role][direction] = {
                        "routing_effect": routing_effects,
                        "value_effect": group_effects,
                        "evidence_effect": evidence_effect,
                    }
                    if role == "causal":
                        effects[target_id][direction]["RDS_T_vs_M"].append(routing_effects["RDS_T_vs_M"])
                        effects[target_id][direction]["ADG_T_vs_M"].append(routing_effects["ADG_T_vs_M"])
                        effects[target_id][direction]["alpha_v_T"].append(group_effects["T"]["alpha_v_norm"])
                        effects[target_id][direction]["evidence"].append(evidence_effect)
            causal_mean = float(statistics.mean(role_rds["causal"]))
            noncausal_mean = float(statistics.mean(role_rds["noncausal"]))
            difference = causal_mean - noncausal_mean
            control_difference[target_id].append(difference)
            control_rows.append({
                "base_problem_id": base,
                "target_id": target_id,
                "causal_reciprocal_mean_RDS_effect": causal_mean,
                "noncausal_reciprocal_mean_RDS_effect": noncausal_mean,
                "causal_minus_noncausal": difference,
            })
            target_problem["causal_minus_noncausal_reciprocal_RDS"] = difference
            target_problem["self_query_exact"] = all(self_exact[target_id][-2:])
            problem_row["targets"][target_id] = target_problem
        per_problem.append(problem_row)

    primary_stats: dict[str, Any] = {
        "primary_unit": "base_problem_id",
        "N_unique_bases": len(rows),
        "condition": "O",
        "query_form": form,
        "effect_orientation": "positive is the prospectively expected necessity/sufficiency direction",
        "targets": {},
    }
    hypothesis_names: list[str] = []
    raw_p: list[float] = []
    gate_rows: dict[str, Any] = {}
    for target_id in TARGETS:
        target_stats: dict[str, Any] = {}
        for direction in DIRECTIONS:
            target_stats[direction] = {}
            for metric, values in effects[target_id][direction].items():
                stat = summary(values)
                target_stats[direction][metric] = stat
                hypothesis_names.append(f"{target_id}__{direction}__{metric}")
                raw_p.append(float(stat["wilcoxon_one_sided_greater_p"]))
        control_stat = summary(control_difference[target_id])
        target_stats["causal_minus_noncausal_reciprocal_RDS"] = control_stat
        hypothesis_names.append(f"{target_id}__causal_minus_noncausal_reciprocal_RDS")
        raw_p.append(float(control_stat["wilcoxon_one_sided_greater_p"]))
        gate_input = {
            "necessity": {
                "routing_median": target_stats["necessity"]["RDS_T_vs_M"]["median"],
                "routing_positive_fraction": target_stats["necessity"]["RDS_T_vs_M"]["positive_fraction"],
                "alpha_v_median": target_stats["necessity"]["alpha_v_T"]["median"],
                "evidence_median": target_stats["necessity"]["evidence"]["median"],
            },
            "sufficiency": {
                "routing_median": target_stats["sufficiency"]["RDS_T_vs_M"]["median"],
                "routing_positive_fraction": target_stats["sufficiency"]["RDS_T_vs_M"]["positive_fraction"],
                "alpha_v_median": target_stats["sufficiency"]["alpha_v_T"]["median"],
                "evidence_median": target_stats["sufficiency"]["evidence"]["median"],
            },
            "causal_minus_noncausal_median": control_stat["median"],
            "self_exact": all(self_exact[target_id]),
        }
        gate_rows[target_id] = {**gate_input, "pass": phase_a_target_passes(gate_input)}
        primary_stats["targets"][target_id] = target_stats

    # The frozen family has 26 target-specific hypotheses; gated Phase-B slots
    # are p=1 until/unless Phase B runs, so primary multiplicity is not relaxed.
    phase_b_placeholders = [f"phase_b_gated_placeholder_{index + 1}" for index in range(8)]
    adjusted = holm_adjust([*raw_p, *([1.0] * len(phase_b_placeholders))])
    primary_stats["holm_family"] = {
        "scope": "26 frozen target-specific Phase-A/Phase-B hypotheses; eight gated Phase-B placeholders currently p=1",
        "hypotheses": {
            name: {
                "raw_p": raw,
                "holm_adjusted_p": float(adj),
                "rejected_0.05": bool(adj < 0.05),
            }
            for name, raw, adj in zip(hypothesis_names, raw_p, adjusted[:len(raw_p)])
        },
        "phase_b_placeholders": phase_b_placeholders,
    }
    gate = {
        "phase_a_status": "pass" if any(row["pass"] for row in gate_rows.values()) else "fail",
        "targets": gate_rows,
        "at_least_one_target_passes": any(row["pass"] for row in gate_rows.values()),
        "phase_b_authorized": any(row["pass"] for row in gate_rows.values()),
        "phase_c_authorized": False,
        "attention_is_not_primary_evidence_acquisition_measure": True,
    }
    primary_stats["phase_a_gate"] = gate

    write_jsonl(OUT / "phase_a_query/per_problem_query_patch_results.jsonl", per_problem)
    write_jsonl(OUT / "phase_a_query/routing_metrics.jsonl", routing_rows)
    write_jsonl(OUT / "phase_a_query/value_influx_metrics.jsonl", value_rows)
    write_jsonl(OUT / "phase_a_query/evidence_results.jsonl", evidence_rows)
    write_jsonl(OUT / "phase_a_query/noncausal_head_controls.jsonl", control_rows)
    write_jsonl(OUT / "observational_sink/sink_under_query_intervention.jsonl", sink_rows)
    write_json(OUT / "analysis/relevant_vs_mention_routing_statistics.json", {
        "targets": {
            target: {
                direction: primary_stats["targets"][target][direction]["RDS_T_vs_M"]
                for direction in DIRECTIONS
            }
            for target in TARGETS
        }
    })
    write_json(OUT / "analysis/query_causality_statistics.json", primary_stats)
    write_json(OUT / "analysis/causal_vs_noncausal_comparison.json", {
        "targets": {
            target: primary_stats["targets"][target]["causal_minus_noncausal_reciprocal_RDS"]
            for target in TARGETS
        }
    })
    write_json(OUT / "phase_a_query/phase_a_gate.json", gate)
    print(json.dumps(gate, indent=2))


if __name__ == "__main__":
    main()
