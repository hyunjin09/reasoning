#!/usr/bin/env python3
"""Aggregate the frozen 37-base Stage 3C.1 descriptive extraction."""

from __future__ import annotations

import glob
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable, Iterable

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import spearmanr, wilcoxon


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c1"
OFFSETS = [-16, -8, -4, -2, -1, 0]
TARGET_COORDINATE = {"target_a": 0, "target_b": -1}
SINK_NAMES = (
    "first_prompt_token",
    "template_control_and_active_query",
    "newline_formatting",
    "image_boundary_neighbor",
    "active_query_token",
)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, allow_nan=False) + "\n")


def summary(values: Iterable[float], *, bootstrap: bool = True) -> dict[str, Any]:
    array = np.asarray(list(values), dtype=np.float64)
    array = array[np.isfinite(array)]
    if not array.size:
        return {"N": 0, "mean": None, "median": None, "bootstrap_95_CI": [None, None]}
    ci: list[float | None] = [None, None]
    if bootstrap:
        rng = np.random.default_rng(1234)
        medians = np.median(rng.choice(array, size=(10_000, array.size), replace=True), axis=1)
        ci = [float(np.quantile(medians, 0.025)), float(np.quantile(medians, 0.975))]
    return {
        "N": int(array.size),
        "mean": float(array.mean()),
        "median": float(np.median(array)),
        "bootstrap_95_CI": ci,
        "minimum": float(array.min()),
        "maximum": float(array.max()),
    }


def paired_summary(left: dict[str, float], right: dict[str, float]) -> dict[str, Any]:
    bases = sorted(set(left) & set(right), key=int)
    differences = np.asarray([left[base] - right[base] for base in bases], dtype=np.float64)
    result = {
        "base_problem_count": len(bases),
        "difference_definition": "left - right",
        "difference": summary(differences),
        "positive_fraction": float(np.mean(differences > 0)) if differences.size else None,
        "per_problem": [
            {"base_problem_id": base, "left": left[base], "right": right[base], "difference": float(left[base] - right[base])}
            for base in bases
        ],
    }
    if differences.size and np.any(differences != 0):
        result["two_sided_wilcoxon_p"] = float(wilcoxon(differences, alternative="two-sided").pvalue)
    else:
        result["two_sided_wilcoxon_p"] = 1.0
    return result


def holm(p_values: dict[str, float]) -> dict[str, dict[str, Any]]:
    ordered = sorted(p_values.items(), key=lambda item: item[1])
    adjusted: dict[str, float] = {}
    running = 0.0
    count = len(ordered)
    for rank, (name, value) in enumerate(ordered):
        running = max(running, min(1.0, (count - rank) * value))
        adjusted[name] = running
    return {
        name: {"raw_p": float(p_values[name]), "holm_adjusted_p": float(adjusted[name]), "rejected_0.05": adjusted[name] < 0.05}
        for name in p_values
    }


def correlation(x: dict[str, float], y: dict[str, float]) -> dict[str, Any]:
    bases = sorted(set(x) & set(y), key=int)
    if len(bases) < 3:
        return {"N": len(bases), "spearman_rho": None, "p_value": None}
    result = spearmanr([x[b] for b in bases], [y[b] for b in bases])
    return {
        "N": len(bases),
        "spearman_rho": float(result.statistic),
        "p_value": float(result.pvalue),
        "descriptive_only": True,
    }


def metric_value(row: dict[str, Any], name: str) -> float:
    groups = row["groups"]
    lookup: dict[str, Callable[[], float]] = {
        "target_attention_mass": lambda: groups["target_roi"]["attention_mass"],
        "target_attention_density": lambda: groups["target_roi"]["attention_density"],
        "target_visual_share": lambda: row["target_roi_share_of_visual_attention"],
        "irrelevant_attention_density": lambda: groups["matched_irrelevant_roi"]["attention_density"],
        "all_visual_attention_mass": lambda: groups["all_visual"]["attention_mass"],
        "target_cosine": lambda: groups["target_roi"]["geometry"]["cosine"]["mean"],
        "irrelevant_cosine": lambda: groups["matched_irrelevant_roi"]["geometry"]["cosine"]["mean"],
        "target_k_norm": lambda: groups["target_roi"]["geometry"]["k_norm"]["mean"],
        "irrelevant_k_norm": lambda: groups["matched_irrelevant_roi"]["geometry"]["k_norm"]["mean"],
        "target_raw_dot": lambda: groups["target_roi"]["geometry"]["raw_dot"]["mean"],
        "irrelevant_raw_dot": lambda: groups["matched_irrelevant_roi"]["geometry"]["raw_dot"]["mean"],
        "target_scaled_logit": lambda: groups["target_roi"]["geometry"]["scaled_logit"]["mean"],
        "irrelevant_scaled_logit": lambda: groups["matched_irrelevant_roi"]["geometry"]["scaled_logit"]["mean"],
        "target_final_logit": lambda: groups["target_roi"]["geometry"]["final_masked_logit"]["mean"],
        "target_alpha_v_norm": lambda: groups["target_roi"]["alpha_v_norm"],
        "target_wo_norm": lambda: groups["target_roi"]["wo_residual_norm"],
        "competition_margin": lambda: row["target_competition_margin"],
        "q_norm": lambda: row["q_norm"],
        "all_entropy": lambda: row["attention_entropy_all_context"],
        "visual_entropy": lambda: row["attention_entropy_visual_only"],
    }
    value = lookup[name]()
    return float(value)


def sink_metric(row: dict[str, Any], name: str) -> dict[str, Any]:
    if name != "template_control_and_active_query":
        return row["sink_candidates"][name]
    group = row["groups"]["special_other"]
    return {
        "token_count": group["token_count"],
        "mass": group["attention_mass"],
        "density": group["attention_density"],
        "contains_top_attended_position": row["top_competing_positions"][0]["source_class"] == "special_other",
        "value_contribution_norm": group["alpha_v_norm"],
        "wo_residual_norm": group["wo_residual_norm"],
    }


def aggregate_head_rows(
    rows: list[dict[str, Any]], *, target: str, offset: int, role: str, metric: str
) -> dict[str, float]:
    values: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        if row["target_id"] == target and row["offset_from_E_d"] == offset and row["head_role"] == role:
            values[str(row["base_problem_id"])].append(metric_value(row, metric))
    return {base: float(np.mean(group)) for base, group in values.items()}


def aggregate_set_rows(
    rows: list[dict[str, Any]], *, target: str, offset: int, role: str, group: str, metric: str
) -> dict[str, float]:
    values: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        if row["target_id"] == target and row["offset_from_E_d"] == offset and row["head_set_role"] == role:
            values[str(row["base_problem_id"])].append(float(row["groups"][group][metric]))
    return {base: float(np.mean(group_values)) for base, group_values in values.items()}


def flatten_outputs(results: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    heads = []
    for result in results:
        for original in result["head_rows"]:
            row = dict(original)
            row["sink_candidates"] = {name: sink_metric(original, name) for name in SINK_NAMES}
            heads.append(row)
    sets = [row for result in results for row in result["head_set_rows"]]
    extraction = OUT / "extraction"
    write_jsonl(extraction / "per_head_per_time_metrics.jsonl", heads)
    write_jsonl(extraction / "source_attention_mass.jsonl", [
        {**{key: row[key] for key in ("base_problem_id", "example_id", "condition", "target_id", "head_role", "layer_index", "logical_query_head", "offset_from_E_d")},
         "source_groups": {name: {key: group[key] for key in ("token_count", "attention_mass", "attention_density")} for name, group in row["groups"].items()},
         "source_partition_mass_sum": row["source_mass_sum"], "source_partition_absolute_error": row["source_mass_absolute_error"]}
        for row in heads
    ])
    write_jsonl(extraction / "qk_geometry.jsonl", [
        {**{key: row[key] for key in ("base_problem_id", "example_id", "condition", "target_id", "head_role", "layer_index", "logical_query_head", "kv_head", "offset_from_E_d")},
         "q_norm": row["q_norm"], "source_geometry": {name: group["geometry"] for name, group in row["groups"].items()},
         "raw_tensor_note": "individual-token values are retained in extraction/raw_tensors/<base>/<condition>_layer<layer>.npz"}
        for row in heads
    ])
    write_jsonl(extraction / "softmax_competition.jsonl", [
        {**{key: row[key] for key in ("base_problem_id", "example_id", "condition", "target_id", "head_role", "layer_index", "logical_query_head", "offset_from_E_d")},
         "class_logsumexp": {name: group["logsumexp_final_logit"] for name, group in row["groups"].items()},
         "lse_all_non_target": row["lse_all_non_target"], "target_competition_margin": row["target_competition_margin"],
         "top_competing_positions": row["top_competing_positions"]}
        for row in heads
    ])
    write_jsonl(extraction / "entropy_metrics.jsonl", [
        {**{key: row[key] for key in ("base_problem_id", "example_id", "condition", "target_id", "head_role", "layer_index", "logical_query_head", "offset_from_E_d")},
         **{key: row[key] for key in ("attention_entropy_all_context", "attention_entropy_visual_only", "effective_visual_support", "target_roi_share_of_visual_attention", "top1_visual_token_share", "top5_visual_token_share")}}
        for row in heads
    ])
    write_jsonl(extraction / "value_contributions.jsonl", [
        {**{key: row[key] for key in ("base_problem_id", "example_id", "condition", "target_id", "head_role", "layer_index", "logical_query_head", "offset_from_E_d")},
         "source_values": {name: {key: group[key] for key in ("attention_mass", "alpha_v_norm", "alpha_v_norm_per_attention_mass")} for name, group in row["groups"].items()},
         "alpha_v_reconstruction_max_abs_error": row["alpha_v_reconstruction_max_abs_error"]}
        for row in heads
    ])
    write_jsonl(extraction / "wo_residual_contributions.jsonl", [
        {**{key: row[key] for key in ("base_problem_id", "example_id", "condition", "target_id", "head_role", "layer_index", "logical_query_head", "offset_from_E_d")},
         "source_post_wo_norms": {name: group["wo_residual_norm"] for name, group in row["groups"].items()},
         "wo_reconstruction_max_abs_error": row["wo_reconstruction_max_abs_error"]}
        for row in heads
    ])
    return heads, sets


def build_controls(heads: list[dict[str, Any]], sets: list[dict[str, Any]]) -> None:
    controls = OUT / "controls"
    retrieval = [
        row for row in heads
        if row["target_id"] in TARGET_COORDINATE
        and row["offset_from_E_d"] == TARGET_COORDINATE[row["target_id"]]
        and row["head_role"] == "causal"
    ]
    write_jsonl(controls / "irrelevant_roi_comparison.jsonl", [
        {**{key: row[key] for key in ("base_problem_id", "condition", "target_id", "logical_query_head")},
         "target_density": row["groups"]["target_roi"]["attention_density"],
         "irrelevant_density": row["groups"]["matched_irrelevant_roi"]["attention_density"],
         "density_difference": row["groups"]["target_roi"]["attention_density"] - row["groups"]["matched_irrelevant_roi"]["attention_density"],
         "target_alpha_v_norm": row["groups"]["target_roi"]["alpha_v_norm"],
         "irrelevant_alpha_v_norm": row["groups"]["matched_irrelevant_roi"]["alpha_v_norm"],
         "target_wo_norm": row["groups"]["target_roi"]["wo_residual_norm"],
         "irrelevant_wo_norm": row["groups"]["matched_irrelevant_roi"]["wo_residual_norm"]}
        for row in retrieval
    ])
    write_jsonl(controls / "noncausal_head_comparison.jsonl", [
        row for row in heads if row["target_id"] in TARGET_COORDINATE and row["offset_from_E_d"] == TARGET_COORDINATE[row["target_id"]]
    ])
    write_jsonl(controls / "upstream_state_control.jsonl", [row for row in sets if row["target_id"] in {"target_a", "target_a_w5_upstream"} and row["offset_from_E_d"] == 0])
    write_jsonl(controls / "w5_head10_secondary.jsonl", [row for row in heads if row["target_id"] == "target_b_w5_head10"])
    write_jsonl(controls / "sink_candidate_metrics.jsonl", [
        {**{key: row[key] for key in ("base_problem_id", "condition", "target_id", "head_role", "layer_index", "logical_query_head", "offset_from_E_d")},
         "sink_candidates": {name: sink_metric(row, name) for name in SINK_NAMES}}
        for row in heads if row["head_role"] == "causal"
    ])


def time_contrasts(heads: list[dict[str, Any]], sets: list[dict[str, Any]]) -> dict[str, Any]:
    metrics = ["target_attention_density", "q_norm", "target_k_norm", "target_cosine", "target_scaled_logit", "competition_margin", "target_alpha_v_norm", "target_wo_norm", "all_entropy", "visual_entropy"]
    result: dict[str, Any] = {"independent_unit": "base_problem_id", "condition_aggregation": "mean over O/O_sham/C/C_sham and frozen causal heads", "targets": {}}
    primary_p: dict[str, float] = {}
    for target, retrieval_offset in TARGET_COORDINATE.items():
        target_result: dict[str, Any] = {"retrieval_offset": retrieval_offset, "metrics": {}}
        for metric in metrics:
            current = aggregate_head_rows(heads, target=target, offset=retrieval_offset, role="causal", metric=metric)
            comparisons = {}
            for earlier in [offset for offset in OFFSETS if offset < retrieval_offset]:
                comparison = paired_summary(current, aggregate_head_rows(heads, target=target, offset=earlier, role="causal", metric=metric))
                comparisons[str(earlier)] = comparison
                if metric == "target_attention_density":
                    primary_p[f"{target}_retrieval_vs_{earlier}"] = comparison["two_sided_wilcoxon_p"]
            target_result["metrics"][metric] = comparisons
        result["targets"][target] = target_result
    w4 = aggregate_set_rows(sets, target="target_a", offset=0, role="causal", group="target_roi", metric="post_wo_head_set_sum_norm")
    w5 = aggregate_set_rows(sets, target="target_a_w5_upstream", offset=0, role="upstream_state_control", group="target_roi", metric="post_wo_head_set_sum_norm")
    result["target_a_retrieval_vs_w5_upstream"] = {
        "metric": "target-ROI post-W_O frozen-head-set sum norm",
        "comparison": paired_summary(w4, w5),
    }
    result["primary_family"] = "retrieval-vs-earlier target-attention-density contrasts only; other metrics are descriptive"
    result["holm_correction"] = holm(primary_p)
    return result


def roi_statistics(heads: list[dict[str, Any]]) -> dict[str, Any]:
    result = {"independent_unit": "base_problem_id", "targets": {}}
    for target, offset in TARGET_COORDINATE.items():
        target_values = aggregate_head_rows(heads, target=target, offset=offset, role="causal", metric="target_attention_density")
        irrelevant = aggregate_head_rows(heads, target=target, offset=offset, role="causal", metric="irrelevant_attention_density")
        comparison = paired_summary(target_values, irrelevant)
        ratios = [target_values[base] / irrelevant[base] if irrelevant[base] > 0 else None for base in sorted(set(target_values)&set(irrelevant), key=int)]
        result["targets"][target] = {
            "target_density": summary(target_values.values()),
            "irrelevant_density": summary(irrelevant.values()),
            "target_share_of_visual_attention": summary(
                aggregate_head_rows(heads, target=target, offset=offset, role="causal", metric="target_visual_share").values()
            ),
            "target_minus_irrelevant": comparison,
            "target_to_irrelevant_density_ratio": summary(value for value in ratios if value is not None),
        }
    return result


def qk_statistics(heads: list[dict[str, Any]]) -> dict[str, Any]:
    metrics = ["q_norm", "target_k_norm", "target_cosine", "target_raw_dot", "target_scaled_logit", "target_final_logit"]
    result = {"independent_unit": "base_problem_id", "targets": {}}
    for target, offset in TARGET_COORDINATE.items():
        target_result = {
            metric: summary(aggregate_head_rows(heads, target=target, offset=offset, role="causal", metric=metric).values())
            for metric in metrics
        }
        for target_metric, irrelevant_metric, label in (
            ("target_k_norm", "irrelevant_k_norm", "k_norm"),
            ("target_cosine", "irrelevant_cosine", "cosine"),
            ("target_raw_dot", "irrelevant_raw_dot", "raw_dot"),
            ("target_scaled_logit", "irrelevant_scaled_logit", "scaled_logit"),
        ):
            target_result[f"target_vs_irrelevant_{label}"] = paired_summary(
                aggregate_head_rows(heads, target=target, offset=offset, role="causal", metric=target_metric),
                aggregate_head_rows(heads, target=target, offset=offset, role="causal", metric=irrelevant_metric),
            )
        result["targets"][target] = target_result
    return result


def competition_statistics(heads: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "independent_unit": "base_problem_id",
        "targets": {
            target: {
                str(offset): summary(aggregate_head_rows(heads, target=target, offset=offset, role="causal", metric="competition_margin").values())
                for offset in OFFSETS
            }
            for target in TARGET_COORDINATE
        },
    }


def attention_value_statistics(heads: list[dict[str, Any]], sets: list[dict[str, Any]]) -> dict[str, Any]:
    result = {"independent_unit": "base_problem_id", "targets": {}}
    for target, offset in TARGET_COORDINATE.items():
        mass = aggregate_head_rows(heads, target=target, offset=offset, role="causal", metric="target_attention_mass")
        alpha = aggregate_head_rows(heads, target=target, offset=offset, role="causal", metric="target_alpha_v_norm")
        wo = aggregate_set_rows(sets, target=target, offset=offset, role="causal", group="target_roi", metric="post_wo_head_set_sum_norm")
        result["targets"][target] = {
            "attention_mass": summary(mass.values()),
            "alpha_v_norm": summary(alpha.values()),
            "post_wo_norm": summary(wo.values()),
            "attention_vs_alpha_v": correlation(mass, alpha),
            "attention_vs_post_wo": correlation(mass, wo),
        }
    return result


def source_profiles(heads: list[dict[str, Any]]) -> dict[str, Any]:
    result = {"independent_unit": "base_problem_id", "profiles": {}}
    for target, retrieval in TARGET_COORDINATE.items():
        for offset in OFFSETS:
            selected = [row for row in heads if row["target_id"] == target and row["head_role"] == "causal" and row["offset_from_E_d"] == offset]
            if not selected:
                continue
            result["profiles"][f"{target}_{offset}"] = {}
            for name in ("all_visual", "prompt_question", "previous_reasoning", "special_other"):
                by_base: dict[str, list[float]] = defaultdict(list)
                for row in selected:
                    by_base[str(row["base_problem_id"])].append(float(row["groups"][name]["attention_mass"]))
                result["profiles"][f"{target}_{offset}"][name] = summary(np.mean(values) for values in by_base.values())
    return result


def sink_summary(heads: list[dict[str, Any]]) -> dict[str, Any]:
    selected = [row for row in heads if row["target_id"] in TARGET_COORDINATE and row["head_role"] == "causal"]
    names = list(SINK_NAMES)
    candidates = {}
    for name in names:
        by_base_mass: dict[str, list[float]] = defaultdict(list)
        by_base_top: dict[str, list[float]] = defaultdict(list)
        for row in selected:
            base = str(row["base_problem_id"])
            metric = sink_metric(row, name)
            by_base_mass[base].append(float(metric["mass"]))
            by_base_top[base].append(float(metric["contains_top_attended_position"]))
        by_semantics: dict[tuple[str, str, int, int], dict[str, list[float]]] = defaultdict(lambda: {"O": [], "C": []})
        for row in selected:
            key = (row["base_problem_id"], row["target_id"], row["offset_from_E_d"], row["logical_query_head"])
            semantic = "O" if row["condition"] in {"O", "O_sham"} else "C"
            by_semantics[key][semantic].append(sink_metric(row, name)["mass"])
        semantic_by_base: dict[str, list[float]] = defaultdict(list)
        for key, value in by_semantics.items():
            if value["O"] and value["C"]:
                semantic_by_base[key[0]].append(abs(np.mean(value["O"]) - np.mean(value["C"])))
        candidates[name] = {
            "mass": summary(np.mean(values) for values in by_base_mass.values()),
            "top_attended_position_fraction_by_base": summary(np.mean(values) for values in by_base_top.values()),
            "absolute_O_vs_C_mass_difference": summary(np.mean(values) for values in semantic_by_base.values()),
            "candidate_only_not_causal_sink": True,
        }
    strongest = max(candidates, key=lambda name: candidates[name]["mass"]["median"] or -math.inf)
    return {"descriptive_only": True, "candidate_classes_defined_prospectively": True, "strongest_mass_candidate": strongest, "candidates": candidates}


def per_head_phenotypes(heads: list[dict[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {"individual_head_interpretation_secondary": True, "targets": {}}
    for target, offset in TARGET_COORDINATE.items():
        selected = [row for row in heads if row["target_id"] == target and row["head_role"] == "causal" and row["offset_from_E_d"] == offset]
        by_head: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for row in selected:
            by_head[int(row["logical_query_head"])].append(row)
        result["targets"][target] = {}
        for head, head_values in sorted(by_head.items()):
            metrics = {}
            for metric in ("target_attention_density", "all_visual_attention_mass", "target_alpha_v_norm", "target_wo_norm"):
                by_base: dict[str, list[float]] = defaultdict(list)
                for row in head_values:
                    by_base[str(row["base_problem_id"])].append(metric_value(row, metric))
                metrics[metric] = summary(np.mean(values) for values in by_base.values())
            result["targets"][target][str(head)] = metrics
        causal = aggregate_head_rows(heads, target=target, offset=offset, role="causal", metric="target_attention_density")
        control = aggregate_head_rows(heads, target=target, offset=offset, role="noncausal_control", metric="target_attention_density")
        result["targets"][target]["causal_vs_noncausal_target_density"] = paired_summary(causal, control)
    result["shared_head_6"] = {
        target: result["targets"][target].get("6") for target in TARGET_COORDINATE
    }
    return result


def condition_semantic_comparison(heads: list[dict[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "independent_unit": "base_problem_id",
        "four_frozen_conditions": ["O", "O_sham", "C", "C_sham"],
        "descriptive_only": True,
        "targets": {},
    }
    for target, offset in TARGET_COORDINATE.items():
        selected = [row for row in heads if row["target_id"] == target and row["head_role"] == "causal" and row["offset_from_E_d"] == offset]
        target_result = {}
        for metric in ("target_attention_density", "all_visual_attention_mass", "target_cosine", "target_alpha_v_norm", "target_wo_norm"):
            by_condition: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
            for row in selected:
                by_condition[row["condition"]][str(row["base_problem_id"])].append(metric_value(row, metric))
            maps = {
                condition: {base: float(np.mean(values)) for base, values in base_rows.items()}
                for condition, base_rows in by_condition.items()
            }
            o_semantic = {base: float(np.mean([maps["O"][base], maps["O_sham"][base]])) for base in maps["O"]}
            c_semantic = {base: float(np.mean([maps["C"][base], maps["C_sham"][base]])) for base in maps["C"]}
            target_result[metric] = {
                "O_vs_O_sham": paired_summary(maps["O"], maps["O_sham"]),
                "C_vs_C_sham": paired_summary(maps["C"], maps["C_sham"]),
                "O_semantic_vs_C_semantic": paired_summary(o_semantic, c_semantic),
            }
        result["targets"][target] = target_result
    return result


def load_causal_effects() -> dict[str, dict[str, dict[str, float]]]:
    effects: dict[str, dict[str, dict[str, float]]] = defaultdict(lambda: defaultdict(dict))
    for path in glob.glob(str(ROOT / "outputs/stage3b7r/scoring/raw/primary_phase_a_*/examples/*/result.json")):
        row = json.loads(Path(path).read_text())
        base = str(row["base_problem_id"])
        for target in row["targets"]:
            arm = next(value for value in target["arm_results"] if value["spatial_arm"] == "target_roi")
            target_id = "target_b" if target["target_id"] == "target_b_r" else target["target_id"]
            effects[target_id]["roi_causal_BHR"][base] = float(arm["BHR"])
    for path in glob.glob(str(ROOT / "outputs/stage3b7r/scoring/raw/primary_phase_b_*/examples/*/result.json")):
        row = json.loads(Path(path).read_text())
        base = str(row["base_problem_id"])
        for target in row["targets"]:
            arm = next(value for value in target["arm_results"] if value["spatial_arm"] == "V")
            target_id = "target_b" if target["target_id"] == "target_b_r" else target["target_id"]
            effects[target_id]["V_only_BHR"][base] = float(arm["BHR"])
    for path in glob.glob(str(ROOT / "outputs/stage3b8/scoring/raw/primary_projected_*/examples/*/result.json")):
        row = json.loads(Path(path).read_text())
        base = str(row["base_problem_id"])
        for target in row["targets"]:
            arm = next(value for value in target["arms"] if value["arm_id"] == "full_V")
            target_id = "target_b" if target["target_id"] == "target_b_r" else target["target_id"]
            effects[target_id]["full_V_BVR"][base] = float(arm["BVR"])
    return effects


def causal_correlations(heads: list[dict[str, Any]], sets: list[dict[str, Any]]) -> dict[str, Any]:
    effects = load_causal_effects()
    result: dict[str, Any] = {"post_freeze_secondary_triangulation": True, "causal_metrics_not_used_for_selection": True, "targets": {}}
    for target, offset in TARGET_COORDINATE.items():
        natural = {
            "target_attention_mass": aggregate_head_rows(heads, target=target, offset=offset, role="causal", metric="target_attention_mass"),
            "target_attention_density": aggregate_head_rows(heads, target=target, offset=offset, role="causal", metric="target_attention_density"),
            "target_alpha_v_norm": aggregate_head_rows(heads, target=target, offset=offset, role="causal", metric="target_alpha_v_norm"),
            "target_wo_head_set_sum_norm": aggregate_set_rows(sets, target=target, offset=offset, role="causal", group="target_roi", metric="post_wo_head_set_sum_norm"),
        }
        result["targets"][target] = {
            causal_name: {
                natural_name: correlation(natural_values, causal_values)
                for natural_name, natural_values in natural.items()
            }
            for causal_name, causal_values in effects[target].items()
        }
        result["targets"][target]["per_problem_causal_effects"] = effects[target]
    return result


def plot_line(heads: list[dict[str, Any]], target: str, metric: str, path: Path, ylabel: str) -> None:
    medians, lows, highs = [], [], []
    for offset in OFFSETS:
        stat = summary(aggregate_head_rows(heads, target=target, offset=offset, role="causal", metric=metric).values())
        medians.append(stat["median"])
        lows.append(stat["bootstrap_95_CI"][0])
        highs.append(stat["bootstrap_95_CI"][1])
    y = np.asarray(medians, dtype=float)
    plt.figure(figsize=(6, 4))
    plt.plot(OFFSETS, y, marker="o")
    plt.fill_between(OFFSETS, lows, highs, alpha=0.2)
    plt.axvline(TARGET_COORDINATE[target], color="black", linestyle="--", alpha=0.5, label="causal coordinate")
    plt.xlabel("offset from E_d")
    plt.ylabel(ylabel)
    plt.title(target.replace("_", " ").title())
    plt.legend()
    plt.tight_layout(); plt.savefig(path, dpi=170); plt.close()


def figures(heads: list[dict[str, Any]], analyses: dict[str, Any]) -> None:
    out = OUT / "analysis/figures"; out.mkdir(parents=True, exist_ok=True)
    plot_line(heads, "target_a", "target_attention_mass", out / "01_target_a_attention_over_time.png", "target ROI attention mass")
    plot_line(heads, "target_b", "target_attention_mass", out / "02_target_b_attention_over_time.png", "target ROI attention mass")
    for number, (name, metric, ylabel) in enumerate([
        ("05_competition_margin_over_time", "competition_margin", "target competition margin"),
        ("13_sink_proxy_visual_mass_over_time", "all_visual_attention_mass", "all visual mass"),
    ], start=5):
        del number
        plot_line(heads, "target_a", metric, out / f"{name}.png", ylabel)
    fig, axes = plt.subplots(2, 2, figsize=(9, 7))
    for axis, (metric, label) in zip(axes.flat, (
        ("target_cosine", "target QK cosine"),
        ("q_norm", "Q norm"),
        ("target_k_norm", "target K norm"),
        ("target_scaled_logit", "target scaled logit"),
    ), strict=True):
        values = [summary(aggregate_head_rows(heads, target="target_a", offset=offset, role="causal", metric=metric).values())["median"] for offset in OFFSETS]
        axis.plot(OFFSETS, values, marker="o"); axis.axvline(0, color="black", linestyle="--", alpha=.4); axis.set_title(label); axis.set_xlabel("offset from E_d")
    fig.tight_layout(); fig.savefig(out/"04_qk_norm_cosine_logit_decomposition.png", dpi=170); plt.close(fig)
    plt.figure(figsize=(7,4))
    for metric, label in (("all_entropy", "all-context"), ("visual_entropy", "visual-only")):
        values=[summary(aggregate_head_rows(heads,target="target_a",offset=offset,role="causal",metric=metric).values())["median"] for offset in OFFSETS]
        plt.plot(OFFSETS,values,marker="o",label=label)
    plt.axvline(0,color="black",linestyle="--",alpha=.4); plt.xlabel("offset from E_d"); plt.ylabel("attention entropy"); plt.legend(); plt.tight_layout(); plt.savefig(out/"06_all_and_visual_entropy_over_time.png",dpi=170); plt.close()

    def retrieval_map(target: str, metric: str, role: str = "causal") -> dict[str, float]:
        return aggregate_head_rows(heads, target=target, offset=TARGET_COORDINATE[target], role=role, metric=metric)
    pairs = [
        ("03_target_vs_irrelevant_density", retrieval_map("target_a", "target_attention_density"), retrieval_map("target_a", "irrelevant_attention_density"), "target density", "irrelevant density"),
        ("07_attention_vs_alpha_v", retrieval_map("target_a", "target_attention_mass"), retrieval_map("target_a", "target_alpha_v_norm"), "target attention mass", "target αV norm"),
        ("08_attention_vs_post_wo", retrieval_map("target_a", "target_attention_mass"), retrieval_map("target_a", "target_wo_norm"), "target attention mass", "post-W_O norm"),
        ("10_causal_vs_noncausal_heads", retrieval_map("target_a", "target_attention_density"), retrieval_map("target_a", "target_attention_density", "noncausal_control"), "causal heads", "noncausal controls"),
    ]
    for name, left, right, xlabel, ylabel in pairs:
        bases = sorted(set(left)&set(right), key=int)
        plt.figure(figsize=(5,4)); plt.scatter([left[b] for b in bases], [right[b] for b in bases], alpha=.75)
        plt.xlabel(xlabel); plt.ylabel(ylabel); plt.tight_layout(); plt.savefig(out/f"{name}.png", dpi=170); plt.close()
    profiles = analyses["source_mass_profiles"]["profiles"]
    profile = profiles["target_a_0"]
    names = ["all_visual", "prompt_question", "previous_reasoning", "special_other"]
    plt.figure(figsize=(7,4)); plt.bar(names, [profile[name]["median"] for name in names]); plt.xticks(rotation=25, ha="right"); plt.ylabel("median attention mass"); plt.tight_layout(); plt.savefig(out/"09_source_mass_composition.png", dpi=170); plt.close()
    # W4 versus W5 and per-head head-6 profiles use extraction rows directly.
    a_w4 = retrieval_map("target_a", "target_attention_mass")
    w5_rows = [row for row in heads if row["target_id"] == "target_a_w5_upstream" and row["offset_from_E_d"] == 0]
    w5_map: dict[str,list[float]] = defaultdict(list)
    for row in w5_rows: w5_map[row["base_problem_id"]].append(metric_value(row,"target_attention_mass"))
    a_w5 = {base:float(np.mean(v)) for base,v in w5_map.items()}
    bases=sorted(set(a_w4)&set(a_w5),key=int); plt.figure(figsize=(5,4)); plt.scatter([a_w4[b] for b in bases],[a_w5[b] for b in bases]); plt.xlabel("E_d/W4 target mass"); plt.ylabel("E_d/W5 target mass"); plt.tight_layout(); plt.savefig(out/"11_w4_vs_w5_upstream.png",dpi=170); plt.close()
    plt.figure(figsize=(7,4))
    for target in TARGET_COORDINATE:
        values=[]
        for off in OFFSETS:
            selected=[metric_value(r,"target_attention_mass") for r in heads if r["target_id"]==target and r["logical_query_head"]==6 and r["head_role"]=="causal" and r["offset_from_E_d"]==off]
            values.append(float(np.median(selected)) if selected else np.nan)
        plt.plot(OFFSETS,values,marker="o",label=target)
    plt.xlabel("offset from E_d"); plt.ylabel("head 6 target mass"); plt.legend(); plt.tight_layout(); plt.savefig(out/"12_shared_head6_profile.png",dpi=170); plt.close()
    # Candidate sink class mass over time.
    sink=analyses["sink_candidate_summary"]["strongest_mass_candidate"]
    plt.figure(figsize=(7,4))
    for target in TARGET_COORDINATE:
        vals=[]
        for off in OFFSETS:
            selected=[sink_metric(r, sink)["mass"] for r in heads if r["target_id"]==target and r["head_role"]=="causal" and r["offset_from_E_d"]==off]
            vals.append(float(np.median(selected)) if selected else np.nan)
        plt.plot(OFFSETS,vals,marker="o",label=target)
    plt.xlabel("offset from E_d"); plt.ylabel(f"{sink} attention mass"); plt.legend(); plt.tight_layout(); plt.savefig(out/"13_candidate_sink_mass_over_time.png",dpi=170); plt.close()
    causal = analyses["causal_effect_correlations"]["targets"]["target_a"]["per_problem_causal_effects"]["roi_causal_BHR"]
    natural=retrieval_map("target_a","target_attention_density"); bases=sorted(set(causal)&set(natural),key=int)
    plt.figure(figsize=(5,4)); plt.scatter([natural[b] for b in bases],[causal[b] for b in bases]); plt.xlabel("natural target attention density"); plt.ylabel("Stage 3B.7-R ROI causal BHR"); plt.tight_layout(); plt.savefig(out/"14_attention_vs_causal_roi_effect.png",dpi=170); plt.close()


def main() -> None:
    result_paths = sorted(glob.glob(str(OUT / "extraction/shards/shard_*/examples/*/result.json")))
    results = [json.loads(Path(path).read_text()) for path in result_paths]
    bases = [str(row["base_problem_id"]) for row in results]
    if len(results) != 37 or len(set(bases)) != 37:
        raise RuntimeError(f"Expected 37 unique full-cohort results, found {len(results)}/{len(set(bases))}")
    heads, sets = flatten_outputs(results)
    build_controls(heads, sets)
    analyses = {
        "retrieval_time_contrasts": time_contrasts(heads, sets),
        "roi_selectivity_statistics": roi_statistics(heads),
        "qk_decomposition_statistics": qk_statistics(heads),
        "softmax_competition_statistics": competition_statistics(heads),
        "attention_vs_value_statistics": attention_value_statistics(heads, sets),
        "source_mass_profiles": source_profiles(heads),
        "sink_candidate_summary": sink_summary(heads),
        "causal_effect_correlations": causal_correlations(heads, sets),
        "per_head_phenotypes": per_head_phenotypes(heads),
        "condition_semantic_comparison": condition_semantic_comparison(heads),
    }
    for name, value in analyses.items():
        write_json(OUT / "analysis" / f"{name}.json", value)
    figures(heads, analyses)
    audit_values = [audit for result in results for layers in result["audits"].values() for audit in layers.values()]
    write_json(OUT / "analysis/full_extraction_validation.json", {
        "base_problem_count": len(set(bases)),
        "condition_count": 4,
        "head_row_count": len(heads),
        "head_set_row_count": len(sets),
        "maximum_probability_reconstruction_error": max(a["eager_reconstruction"]["maximum_probability_absolute_error"] for a in audit_values),
        "maximum_head_output_reconstruction_error": max(a["eager_reconstruction"]["maximum_head_output_absolute_error"] for a in audit_values),
        "maximum_source_mass_error": max(a["maximum_source_mass_absolute_error"] for a in audit_values),
        "maximum_alpha_v_partition_error": max(a["maximum_alpha_v_reconstruction_absolute_error"] for a in audit_values),
        "maximum_wo_partition_error": max(a["maximum_wo_reconstruction_absolute_error"] for a in audit_values),
        "all_finite": all(a["all_values_finite"] for a in audit_values),
        "all_condition_layouts_exact": all(result["condition_layout_exact"] for result in results),
        "selection_used_stage3c1_attention": False,
        "attention_manipulated": False,
        "total_runtime_seconds_sum": float(sum(result["runtime_seconds"] for result in results)),
    })
    print(json.dumps({"base_problem_count": len(set(bases)), "head_rows": len(heads), "figures": len(list((OUT/'analysis/figures').glob('*.png')))}, indent=2))


if __name__ == "__main__":
    main()
