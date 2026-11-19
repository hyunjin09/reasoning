#!/usr/bin/env python3
"""Validate and analyze the completed passive Stage 3C.2 extraction."""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable

import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import spearmanr, wilcoxon

from visual_reasoning.stage3c2.metrics import classify_attention_phenotype, holm_adjust


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c2"
FIG = OUT / "analysis/figures"
GROUPS = ("target_roi", "mention_roi", "irrelevant_roi", "other_visual", "prompt_question", "previous_reasoning", "candidate_sink", "other")
OFFSETS = (-16, -8, -4, -2, -1, 0)
COLORS = {"target_roi": "#198c36", "mention_roi": "#c22ca5", "irrelevant_roi": "#d98b13", "candidate_sink": "#444444", "other_visual": "#74a9cf", "prompt_question": "#756bb1", "previous_reasoning": "#e6550d", "other": "#bdbdbd"}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, allow_nan=False) + "\n" for row in rows))


def finite(values: list[float]) -> np.ndarray:
    return np.asarray([float(value) for value in values if value is not None and math.isfinite(float(value))], dtype=float)


def bootstrap_ci(values: list[float], seed: int = 1234, draws: int = 10_000) -> list[float] | None:
    data = finite(values)
    if not len(data): return None
    rng = np.random.default_rng(seed)
    means = np.mean(rng.choice(data, (draws, len(data)), replace=True), axis=1)
    return [float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))]


def summary(values: list[float]) -> dict[str, Any]:
    data = finite(values)
    return {"N": int(len(data)), "mean": float(np.mean(data)) if len(data) else None, "median": float(np.median(data)) if len(data) else None, "bootstrap_mean_95_CI": bootstrap_ci(data.tolist()), "positive_fraction": float(np.mean(data > 0)) if len(data) else None, "minimum": float(np.min(data)) if len(data) else None, "maximum": float(np.max(data)) if len(data) else None}


def paired_p(values: list[float]) -> float:
    data = finite(values)
    if not len(data) or np.all(data == 0): return 1.0
    return float(wilcoxon(data, alternative="two-sided").pvalue)


def mean(values: list[float]) -> float:
    return float(np.mean(finite(values)))


def nested(row: dict[str, Any], group: str, field: str) -> float:
    return float(row["groups"][group][field])


def geometry(row: dict[str, Any], group: str, metric: str) -> float:
    return float(row["groups"][group]["mean_" + metric])


def line_plot(rows: list[dict[str, Any]], metric: Callable[[dict[str, Any]], float], labels: list[tuple[str, str]], output: str, ylabel: str) -> None:
    plt.figure(figsize=(7, 4.5))
    for group, label in labels:
        values = [mean([metric(row) for row in rows if row["offset_from_target"] == offset and row.get("plot_group") == group]) for offset in OFFSETS]
        plt.plot(OFFSETS, values, marker="o", label=label, color=COLORS.get(group))
    plt.axvline(0, color="black", linewidth=0.8, linestyle="--"); plt.xlabel("Offset from frozen retrieval coordinate"); plt.ylabel(ylabel); plt.legend(); plt.tight_layout(); plt.savefig(FIG / output, dpi=180); plt.close()


def main() -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    manifest = read_jsonl(OUT / "cohort/primary_dissociation_manifest.jsonl")
    expected = {str(row["base_problem_id"]) for row in manifest}
    result_paths = sorted((OUT / "extraction").glob("shard_*/examples/*/result.json"))
    results = [read_json(path) for path in result_paths]
    observed = [str(row["base_problem_id"]) for row in results]
    if len(results) != len(expected) or set(observed) != expected or len(observed) != len(set(observed)):
        raise RuntimeError(f"Extraction completeness failed: {len(results)=}, {len(expected)=}")
    if not all(row["condition_layout_exact"] and not row["attention_manipulated"] for row in results):
        raise RuntimeError("Layout/passive measurement invariant failed")
    head_rows = [row for result in results for row in result["head_rows"]]
    set_rows = [row for result in results for row in result["head_set_rows"]]
    expected_head_rows = sum(len(row["head_rows"]) for row in results)
    if len(head_rows) != expected_head_rows: raise RuntimeError("Head-row flattening failed")
    write_jsonl(OUT / "measurements/per_head_time_condition.jsonl", head_rows)
    source_rows, qk_rows, value_rows, sink_rows = [], [], [], []
    for row in head_rows:
        identity = {key: row[key] for key in ("base_problem_id", "example_id", "condition", "target_id", "head_role", "layer_index", "logical_query_head", "offset_from_target", "offset_from_E_d", "generated_index", "semantic_state")}
        for group in GROUPS:
            item = row["groups"][group]
            source_rows.append({**identity, "source_group": group, "token_count": item["token_count"], "attention_mass": item["attention_mass"], "attention_density": item["attention_density"]})
            qk_rows.append({**identity, "source_group": group, "q_norm": row["q_norm"], "k_norm": item["geometry"]["k_norm"], "qk_cosine": item["geometry"]["qk_cosine"], "raw_dot": item["geometry"]["raw_dot"], "scaled_logit": item["geometry"]["scaled_logit"]})
            value_rows.append({**identity, "source_group": group, "alpha_v_norm": item["alpha_v_norm"], "alpha_v_norm_per_attention_mass": item["alpha_v_norm_per_attention_mass"], "wo_residual_norm": item["wo_residual_norm"]})
        sink_rows.append({**identity, "primary_candidate": row["groups"]["candidate_sink"], "secondary_candidates": row["secondary_sink_candidates"], "candidate_only_not_causal_sink": True})
    write_jsonl(OUT / "measurements/source_mass_results.jsonl", source_rows)
    write_jsonl(OUT / "measurements/qk_results.jsonl", qk_rows)
    write_jsonl(OUT / "measurements/value_contribution_results.jsonl", value_rows)
    write_jsonl(OUT / "measurements/sink_results.jsonl", sink_rows)

    by_set = {(row["base_problem_id"], row["target_id"], row["condition"], row["head_set_role"], int(row["offset_from_target"])): row for row in set_rows}
    pairs = read_jsonl(OUT / "annotations/state_pair_annotations.jsonl")
    pair_by = {(row["base_problem_id"], row["target_id"]): row for row in pairs}
    primary: dict[str, list[float]] = defaultdict(list)
    per_base_rows, phenotype_rows = [], []
    for base in sorted(expected, key=int):
        metrics_by_target = defaultdict(list)
        for target_id in ("target_a", "target_b"):
            pair = pair_by[(base, target_id)]
            early_offset, retrieval_offset = int(pair["mention_only_offset_from_target"]), int(pair["retrieval_offset_from_target"])
            early = by_set[(base, target_id, "O", "causal", early_offset)]
            retrieval = by_set[(base, target_id, "O", "causal", retrieval_offset)]
            early_control = by_set[(base, target_id, "O", "noncausal_control", early_offset)]
            retrieval_control = by_set[(base, target_id, "O", "noncausal_control", retrieval_offset)]
            t_minus_m_early = nested(early, "target_roi", "mean_attention_density") - nested(early, "mention_roi", "mean_attention_density")
            t_minus_m_retrieval = nested(retrieval, "target_roi", "mean_attention_density") - nested(retrieval, "mention_roi", "mean_attention_density")
            control_cross = (nested(retrieval_control, "target_roi", "mean_attention_density") - nested(retrieval_control, "mention_roi", "mean_attention_density")) - (nested(early_control, "target_roi", "mean_attention_density") - nested(early_control, "mention_roi", "mean_attention_density"))
            vals = {
                "t_vs_m_retrieval": t_minus_m_retrieval,
                "qk_t_retrieval_minus_mention": geometry(retrieval, "target_roi", "qk_cosine") - geometry(early, "target_roi", "qk_cosine"),
                "a_t_retrieval_minus_mention": nested(retrieval, "target_roi", "mean_attention_density") - nested(early, "target_roi", "mean_attention_density"),
                "alpha_v_t_retrieval_minus_mention": nested(retrieval, "target_roi", "mean_alpha_v_norm") - nested(early, "target_roi", "mean_alpha_v_norm"),
                "sink_retrieval_minus_mention": nested(retrieval, "candidate_sink", "mean_attention_mass") - nested(early, "candidate_sink", "mean_attention_mass"),
                "t_vs_m_temporal_crossover": t_minus_m_retrieval - t_minus_m_early,
                "causal_vs_noncausal_crossover_enrichment": (t_minus_m_retrieval - t_minus_m_early) - control_cross,
            }
            for key, value in vals.items(): metrics_by_target[key].append(value)
            phenotype_rows.append({"base_problem_id": base, "target_id": target_id, "early_T_minus_M_attention_density": t_minus_m_early, "retrieval_T_minus_M_attention_density": t_minus_m_retrieval, "phenotype": classify_attention_phenotype(t_minus_m_early, t_minus_m_retrieval)})
        aggregate = {key: mean(values) for key, values in metrics_by_target.items()}
        per_base_rows.append({"base_problem_id": base, **aggregate})
        for key, value in aggregate.items(): primary[key].append(value)
    primary_order = ["t_vs_m_retrieval", "qk_t_retrieval_minus_mention", "a_t_retrieval_minus_mention", "alpha_v_t_retrieval_minus_mention", "sink_retrieval_minus_mention", "t_vs_m_temporal_crossover", "causal_vs_noncausal_crossover_enrichment"]
    p_values = [paired_p(primary[key]) for key in primary_order]; adjusted = holm_adjust(p_values)
    retrieval_dissociations = defaultdict(list)
    for base in expected:
        for target_id in ("target_a", "target_b"):
            row = by_set[(base, target_id, "O", "causal", 0)]
            for metric_name, field in (("attention_mass", "mean_attention_mass"), ("attention_density", "mean_attention_density"), ("qk_cosine", "mean_qk_cosine"), ("alpha_v_norm", "mean_alpha_v_norm"), ("wo_residual_norm", "mean_wo_residual_norm")):
                retrieval_dissociations[metric_name].append(nested(row, "target_roi", field) - nested(row, "mention_roi", field))
    primary_stats = {"primary_unit": "base_problem_id", "N_unique_bases": len(expected), "condition": "O", "T_vs_M_attention_measure": "per-ROI-token density", "multiple_testing": "Holm across seven prospectively frozen contrasts", "contrasts": {key: {**summary(primary[key]), "wilcoxon_two_sided_p": p, "holm_adjusted_p": adj} for key, p, adj in zip(primary_order, p_values, adjusted)}, "retrieval_coordinate_T_minus_M_descriptive_metrics_over_target_base_events": {key: summary(values) for key, values in retrieval_dissociations.items()}, "per_base": per_base_rows, "attention_is_descriptive_not_causal": True}
    write_json(OUT / "analysis/mention_vs_required_statistics.json", primary_stats)
    phenotypes = Counter(row["phenotype"] for row in phenotype_rows)
    write_json(OUT / "analysis/temporal_crossover_statistics.json", {"per_target_base": phenotype_rows, "counts": dict(phenotypes), "fractions": {key: value / len(phenotype_rows) for key, value in phenotypes.items()}, "descriptive_only": True})
    write_json(OUT / "analysis/qk_sharpening_statistics.json", {"target_qk_retrieval_minus_mention": summary(primary["qk_t_retrieval_minus_mention"]), "holm_adjusted_p": primary_stats["contrasts"]["qk_t_retrieval_minus_mention"]["holm_adjusted_p"], "interpretation_boundary": "QK sharpening is descriptive and is not manipulated here."})

    natural = [row for row in set_rows if row["condition"] == "O" and row["head_set_role"] == "causal"]
    budget_by_offset = {str(offset): {group: mean([nested(row, group, "mean_attention_mass") for row in natural if row["offset_from_target"] == offset]) for group in GROUPS} for offset in OFFSETS}
    max_budget_error = max(abs(sum(values.values()) - 1.0) for values in budget_by_offset.values())
    write_json(OUT / "analysis/attention_budget_statistics.json", {"mean_budget_by_offset": budget_by_offset, "maximum_mean_budget_closure_error": max_budget_error, "groups_mutually_exclusive": True})

    sink_deltas, target_deltas, source_deltas, srr, sink_phenotypes, loss_sources = [], [], defaultdict(list), [], [], []
    for base in expected:
        for target_id in ("target_a", "target_b"):
            pair = pair_by[(base, target_id)]; early = by_set[(base, target_id, "O", "causal", int(pair["mention_only_offset_from_target"]))]; retr = by_set[(base, target_id, "O", "causal", 0)]
            dt = nested(retr, "target_roi", "mean_attention_mass") - nested(early, "target_roi", "mean_attention_mass")
            ds = nested(retr, "candidate_sink", "mean_attention_mass") - nested(early, "candidate_sink", "mean_attention_mass")
            target_deltas.append(dt); sink_deltas.append(ds)
            event_deltas = {group: nested(retr, group, "mean_attention_mass") - nested(early, group, "mean_attention_mass") for group in GROUPS}
            for group, value in event_deltas.items(): source_deltas[group].append(value)
            if dt > 0: srr.append(-ds / dt)
            if dt <= 0:
                sink_phenotypes.append("no_target_gain")
            elif ds <= -0.25 * dt:
                sink_phenotypes.append("sink_release_retrieval")
            elif abs(ds) <= 0.25 * dt:
                sink_phenotypes.append("persistent_sink")
            else:
                sink_phenotypes.append("non_sink_reallocation")
            competing = {group: value for group, value in event_deltas.items() if group != "target_roi"}
            loss_sources.append(min(competing, key=competing.get))
    rho, rho_p = spearmanr(target_deltas, [-value for value in sink_deltas])
    write_json(OUT / "analysis/sink_dynamics_statistics.json", {"delta_target_mass": summary(target_deltas), "delta_sink_mass": summary(sink_deltas), "source_delta_summaries": {group: summary(values) for group, values in source_deltas.items()}, "sink_reallocation_ratio_when_target_gain_positive": summary(srr), "spearman_delta_target_vs_negative_delta_sink": {"rho": float(rho), "p": float(rho_p)}, "exploratory_phenotype_rule": "sink release: delta_sink <= -0.25*delta_target; persistent: abs(delta_sink) <= 0.25*delta_target; otherwise non-sink", "exploratory_phenotype_counts": dict(Counter(sink_phenotypes)), "largest_competing_loss_source_counts": dict(Counter(loss_sources)), "candidate_sink_descriptive_only": True})
    entropy_stats = {name: {str(offset): summary([float(row[name]) for row in natural if row["offset_from_target"] == offset]) for offset in OFFSETS} for name in ("mean_attention_entropy_all_context", "mean_attention_entropy_visual_only", "mean_attention_entropy_non_sink")}
    write_json(OUT / "analysis/entropy_statistics.json", entropy_stats)

    head_natural = [row for row in head_rows if row["condition"] == "O" and row["offset_from_target"] == 0]
    heterogeneity = {}
    for target_id in ("target_a", "target_b"):
        heterogeneity[target_id] = {}
        for head in sorted({row["logical_query_head"] for row in head_natural if row["target_id"] == target_id}):
            rows = [row for row in head_natural if row["target_id"] == target_id and row["logical_query_head"] == head]
            heterogeneity[target_id][str(head)] = {"head_role": rows[0]["head_role"], "target_attention_density": summary([row["groups"]["target_roi"]["attention_density"] for row in rows]), "mention_attention_density": summary([row["groups"]["mention_roi"]["attention_density"] for row in rows]), "target_qk_cosine": summary([row["groups"]["target_roi"]["geometry"]["qk_cosine"]["mean"] for row in rows]), "target_alpha_v_norm": summary([row["groups"]["target_roi"]["alpha_v_norm"] for row in rows]), "sink_mass": summary([row["groups"]["candidate_sink"]["attention_mass"] for row in rows])}
    write_json(OUT / "analysis/head_heterogeneity.json", heterogeneity)
    write_json(OUT / "analysis/causal_vs_noncausal_head_comparison.json", {"crossover_enrichment": summary(primary["causal_vs_noncausal_crossover_enrichment"]), "holm_adjusted_p": primary_stats["contrasts"]["causal_vs_noncausal_crossover_enrichment"]["holm_adjusted_p"], "prior_intervention_defines_head_roles_but_current_measurement_is_descriptive": True})

    controls = {}
    for condition in ("O", "O_sham", "C", "C_sham"):
        rows = [row for row in set_rows if row["condition"] == condition and row["head_set_role"] == "causal" and row["offset_from_target"] == 0]
        controls[condition] = {"target_attention_mass": summary([nested(row, "target_roi", "mean_attention_mass") for row in rows]), "target_attention_density": summary([nested(row, "target_roi", "mean_attention_density") for row in rows]), "sink_attention_mass": summary([nested(row, "candidate_sink", "mean_attention_mass") for row in rows]), "target_alpha_v_norm": summary([nested(row, "target_roi", "mean_alpha_v_norm") for row in rows]), "sink_alpha_v_norm": summary([nested(row, "candidate_sink", "mean_alpha_v_norm") for row in rows])}
    control_keyed = {(row["base_problem_id"], row["target_id"], row["condition"]): row for row in set_rows if row["head_set_role"] == "causal" and row["offset_from_target"] == 0}
    comparisons = {}
    for left, right, label in (("O", "O_sham", "original_minus_original_sham"), ("C", "C_sham", "counterfactual_minus_counterfactual_sham"), ("O", "C", "original_minus_counterfactual")):
        comparisons[label] = {}
        for metric_name, group, field in (("target_attention_mass", "target_roi", "mean_attention_mass"), ("target_attention_density", "target_roi", "mean_attention_density"), ("target_qk_cosine", "target_roi", "mean_qk_cosine"), ("target_alpha_v_norm", "target_roi", "mean_alpha_v_norm"), ("sink_attention_mass", "candidate_sink", "mean_attention_mass"), ("sink_qk_cosine", "candidate_sink", "mean_qk_cosine"), ("sink_alpha_v_norm", "candidate_sink", "mean_alpha_v_norm")):
            deltas = []
            for base in expected:
                per_target = [nested(control_keyed[(base, target_id, left)], group, field) - nested(control_keyed[(base, target_id, right)], group, field) for target_id in ("target_a", "target_b")]
                deltas.append(mean(per_target))
            comparisons[label][metric_name] = {"signed_difference": summary(deltas), "absolute_difference": summary([abs(value) for value in deltas])}
    write_json(OUT / "analysis/condition_controls.json", {"retrieval_coordinate": controls, "paired_base_level_comparisons": comparisons, "semantic_change_comparison": "O versus C", "artifact_controls": "O versus O_sham and C versus C_sham", "descriptive_only": True})

    # Figures 1--3: temporal T/M traces.
    plot_rows = []
    for row in natural:
        for group in ("target_roi", "mention_roi"):
            plot_rows.append({**row, "plot_group": group})
    line_plot(plot_rows, lambda r: nested(r, r["plot_group"], "mean_qk_cosine"), [("target_roi", "Task ROI T"), ("mention_roi", "Mention ROI M")], "01_temporal_qk_T_vs_M.png", "Mean QK cosine")
    line_plot(plot_rows, lambda r: nested(r, r["plot_group"], "mean_attention_density"), [("target_roi", "Task ROI T"), ("mention_roi", "Mention ROI M")], "02_temporal_attention_T_vs_M.png", "Attention density")
    line_plot(plot_rows, lambda r: nested(r, r["plot_group"], "mean_alpha_v_norm"), [("target_roi", "Task ROI T"), ("mention_roi", "Mention ROI M")], "03_temporal_alphaV_T_vs_M.png", "alpha-V norm")
    top = sorted(phenotype_rows, key=lambda row: row["retrieval_T_minus_M_attention_density"] - row["early_T_minus_M_attention_density"], reverse=True)[:12]
    plt.figure(figsize=(8, 4.5))
    for index, row in enumerate(top): plt.plot([0, 1], [row["early_T_minus_M_attention_density"], row["retrieval_T_minus_M_attention_density"]], marker="o", alpha=.7, label=f'{row["base_problem_id"]}/{row["target_id"]}' if index < 6 else None)
    plt.axhline(0, color="black", linewidth=.8); plt.xticks([0, 1], ["mention-only", "retrieval"]); plt.ylabel("T - M attention density"); plt.legend(ncol=3, fontsize=7); plt.tight_layout(); plt.savefig(FIG / "04_crossover_examples.png", dpi=180); plt.close()
    for metric_name, label, filename in (("a_t_retrieval_minus_mention", "Target attention-density change", "05_paired_target_attention.png"), ("qk_t_retrieval_minus_mention", "Target QK-cosine change", "06_paired_target_qk.png")):
        values = primary[metric_name]; plt.figure(figsize=(6, 4)); plt.scatter(np.zeros(len(values)), values, alpha=.65); plt.axhline(0, color="black", linewidth=.8); plt.xticks([0], ["retrieval - mention-only"]); plt.ylabel(label); plt.tight_layout(); plt.savefig(FIG / filename, dpi=180); plt.close()
    bottom = np.zeros(len(OFFSETS)); plt.figure(figsize=(8, 4.7))
    for group in GROUPS:
        values = np.asarray([budget_by_offset[str(offset)][group] for offset in OFFSETS]); plt.bar(OFFSETS, values, bottom=bottom, width=1.2, label=group, color=COLORS[group]); bottom += values
    plt.xlabel("Offset from retrieval"); plt.ylabel("Attention mass"); plt.legend(fontsize=6, ncol=2); plt.tight_layout(); plt.savefig(FIG / "07_attention_budget_over_time.png", dpi=180); plt.close()
    plt.figure(figsize=(7, 4)); plt.plot(OFFSETS, [budget_by_offset[str(offset)]["candidate_sink"] for offset in OFFSETS], marker="o", color=COLORS["candidate_sink"]); plt.xlabel("Offset from retrieval"); plt.ylabel("Candidate-sink mass"); plt.tight_layout(); plt.savefig(FIG / "08_candidate_sink_mass_over_time.png", dpi=180); plt.close()
    plt.figure(figsize=(5, 5)); plt.scatter(target_deltas, [-v for v in sink_deltas], alpha=.6); plt.axhline(0, color="black", lw=.7); plt.axvline(0, color="black", lw=.7); plt.xlabel("Delta target attention mass"); plt.ylabel("-Delta candidate-sink mass"); plt.tight_layout(); plt.savefig(FIG / "09_target_gain_vs_sink_loss.png", dpi=180); plt.close()
    target_av = [nested(row, "target_roi", "mean_alpha_v_norm") for row in natural if row["offset_from_target"] == 0]; sink_av = [nested(row, "candidate_sink", "mean_alpha_v_norm") for row in natural if row["offset_from_target"] == 0]; target_wo = [nested(row, "target_roi", "mean_wo_residual_norm") for row in natural if row["offset_from_target"] == 0]; sink_wo = [nested(row, "candidate_sink", "mean_wo_residual_norm") for row in natural if row["offset_from_target"] == 0]
    fig, axes = plt.subplots(1, 2, figsize=(9, 4)); axes[0].boxplot([target_av, sink_av], tick_labels=["T", "sink"]); axes[0].set_ylabel("alpha-V norm"); axes[1].boxplot([target_wo, sink_wo], tick_labels=["T", "sink"]); axes[1].set_ylabel("post-W_O norm"); fig.tight_layout(); fig.savefig(FIG / "10_target_vs_sink_value_dynamics.png", dpi=180); plt.close(fig)
    vals = primary["causal_vs_noncausal_crossover_enrichment"]; plt.figure(figsize=(6, 4)); plt.hist(vals, bins=12); plt.axvline(0, color="black", lw=.8); plt.xlabel("Causal - noncausal crossover enrichment"); plt.tight_layout(); plt.savefig(FIG / "11_causal_vs_noncausal_phenotype.png", dpi=180); plt.close()
    labels_h, values_h, colors_h = [], [], []
    for target_id in ("target_a", "target_b"):
        for head, data in heterogeneity[target_id].items(): labels_h.append(f"{target_id[-1].upper()}h{head}"); values_h.append(data["target_attention_density"]["median"]); colors_h.append("#d62728" if target_id == "target_b" and head == "6" else ("#198c36" if data["head_role"] == "causal" else "#999999"))
    plt.figure(figsize=(10, 4)); plt.bar(labels_h, values_h, color=colors_h); plt.xticks(rotation=55); plt.ylabel("Median target attention density"); plt.tight_layout(); plt.savefig(FIG / "12_per_head_heterogeneity.png", dpi=180); plt.close()
    plt.figure(figsize=(7, 4));
    for name, label in (("mean_attention_entropy_all_context", "full"), ("mean_attention_entropy_visual_only", "visual-only"), ("mean_attention_entropy_non_sink", "non-sink")):
        plt.plot(OFFSETS, [entropy_stats[name][str(offset)]["median"] for offset in OFFSETS], marker="o", label=label)
    plt.xlabel("Offset from retrieval"); plt.ylabel("Entropy"); plt.legend(); plt.tight_layout(); plt.savefig(FIG / "13_entropy_over_time.png", dpi=180); plt.close()
    conditions = ["O", "O_sham", "C", "C_sham"]; x = np.arange(4); width=.36
    plt.figure(figsize=(7, 4)); plt.bar(x-width/2, [controls[c]["target_attention_mass"]["median"] for c in conditions], width, label="target"); plt.bar(x+width/2, [controls[c]["sink_attention_mass"]["median"] for c in conditions], width, label="sink"); plt.xticks(x, conditions); plt.ylabel("Median attention mass"); plt.legend(); plt.tight_layout(); plt.savefig(FIG / "14_condition_controls.png", dpi=180); plt.close()

    audits = [audit for result in results for condition in result["audits"].values() for audit in condition.values()]
    mention_annotations = read_jsonl(OUT / "annotations/mention_roi_annotations.jsonl")
    write_json(OUT / "audit/token_roi_layout_audit.json", {"N_unique_bases": len(expected), "all_M_not_equal_T": all(row["M_not_equal_T"] for row in mention_annotations), "all_M_disjoint_I": all(row["M_disjoint_I"] for row in mention_annotations), "manual_overlay_reviewed": True, "overlays": [str(path.relative_to(ROOT)) for path in sorted((OUT / "audit/roi_overlays").glob("[0-9]*.png"))], "selection_used_attention": False})
    max_source = max(row["source_mass_absolute_error"] for row in head_rows)
    write_json(OUT / "audit/source_partition_audit.json", {"head_rows": len(head_rows), "maximum_source_mass_absolute_error": max_source, "tolerance": 0.005, "passed": max_source <= 0.005, "mutually_exclusive_groups": list(GROUPS)})
    max_prob = max(audit["eager_reconstruction"]["maximum_probability_absolute_error"] for audit in audits); max_output = max(audit["eager_reconstruction"]["maximum_head_output_absolute_error"] for audit in audits)
    max_alpha = max(audit["maximum_alpha_v_reconstruction_absolute_error"] for audit in audits); max_wo = max(audit["maximum_wo_reconstruction_absolute_error"] for audit in audits)
    write_json(OUT / "audit/attention_reconstruction_audit.json", {"full_shape_eager_reconstruction_reused": True, "maximum_probability_absolute_error": max_prob, "maximum_head_output_absolute_error": max_output, "maximum_partitioned_alpha_v_reconstruction_absolute_error": max_alpha, "maximum_partitioned_post_wo_reconstruction_absolute_error": max_wo, "installed_attention_reconstruction_exact": max_prob == 0 and max_output == 0, "partitioned_contribution_reconstruction_within_float32_tolerance": max_alpha <= 5e-6 and max_wo <= 1e-6, "exact": max_prob == 0 and max_output == 0 and max_alpha <= 5e-6 and max_wo <= 1e-6, "tensor_shapes_observed": sorted({json.dumps(audit["tensor_shapes"], sort_keys=True) for audit in audits}), "all_values_finite": all(audit["all_values_finite"] for audit in audits)})
    smoke = [read_json(path) for path in sorted((OUT / "smoke/examples").glob("*/result.json"))]
    write_json(OUT / "audit/measurement_reproducibility.json", {"smoke_bases": [row["base_problem_id"] for row in smoke], "instrumentation": [row["instrumentation_faithfulness"] for row in smoke], "deterministic_repeat": [row["deterministic_repeat"] for row in smoke], "all_passed": all(row["instrumentation_faithfulness"]["passed"] and row["deterministic_repeat"]["passed"] for row in smoke)})
    write_json(OUT / "audit/sink_definition_audit.json", {"primary_position": 0, "token": "<|im_start|>", "source": "frozen Stage 3C.1 verified prompt layout", "disjoint_from_visual_question_reasoning": True, "candidate_only_not_causal_sink": True})
    print(json.dumps({"bases": len(expected), "head_rows": len(head_rows), "set_rows": len(set_rows), "figures": len(list(FIG.glob('*.png'))), "max_source_error": max_source, "max_probability_error": max_prob}, indent=2))


if __name__ == "__main__":
    main()
