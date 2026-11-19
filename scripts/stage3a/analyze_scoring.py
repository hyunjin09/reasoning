#!/usr/bin/env python3
"""Aggregate frozen Stage 3A scoring shards and compute primary statistics."""

from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

import numpy as np
from PIL import Image, ImageDraw
from scipy.stats import spearmanr

from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl
from visual_reasoning.stage3a.metrics import bootstrap_interval, summarize_effect_values


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3a"
PRIMARY = OUT / "cohort/primary_manifest.jsonl"
SHARDS = OUT / "scoring/shards"
SCORE_OUT = OUT / "scoring"
ANALYSIS = OUT / "analysis"
FIGURES = ANALYSIS / "figures"
BOOTSTRAP_SEED = 31_415
BOOTSTRAP_RESAMPLES = 20_000


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def aggregate_shards(expected_bases: list[str]) -> tuple[list[dict], list[dict], list[dict]]:
    found: dict[str, tuple[dict, list[dict], list[dict]]] = {}
    for result_path in sorted(SHARDS.glob("primary_*/result.json")):
        shard = result_path.parent
        result = json.loads(result_path.read_text(encoding="utf-8"))
        if int(result["base_problem_count"]) <= 0:
            raise RuntimeError(f"Empty completed scoring shard: {shard}")
        facts = read_jsonl(shard / "fact_preference.jsonl")
        temporal = read_jsonl(shard / "temporal_sensitivity.jsonl")
        rollouts = read_jsonl(shard / "rollout_results.jsonl")
        for fact in facts:
            base = str(fact["base_problem_id"])
            if base in found:
                raise RuntimeError(f"Duplicate scored base_problem_id: {base}")
            found[base] = (
                fact,
                [row for row in temporal if str(row["base_problem_id"]) == base],
                [row for row in rollouts if str(row["base_problem_id"]) == base],
            )
    missing = [base for base in expected_bases if base not in found]
    extra = sorted(set(found) - set(expected_bases), key=int)
    if missing or extra:
        raise RuntimeError(f"Scoring cohort mismatch; missing={missing}, extra={extra}")
    facts = [found[base][0] for base in expected_bases]
    temporal = [row for base in expected_bases for row in found[base][1]]
    rollouts = [row for base in expected_bases for row in found[base][2]]
    if any(len(found[base][2]) != 3 for base in expected_bases):
        raise RuntimeError("Each primary base must have original/counterfactual/sham rollouts")
    return facts, temporal, rollouts


def _distinctive_values(original_fact: str, counterfactual_fact: str) -> tuple[list[str], list[str]]:
    number_pattern = r"(?<![A-Za-z0-9])\d+(?:\.\d+)?(?![A-Za-z0-9])"
    original_numbers = re.findall(number_pattern, original_fact)
    counterfactual_numbers = re.findall(number_pattern, counterfactual_fact)
    original_unique = [value for value in original_numbers if value not in counterfactual_numbers]
    counterfactual_unique = [value for value in counterfactual_numbers if value not in original_numbers]
    if original_unique and counterfactual_unique:
        return original_unique, counterfactual_unique
    stop = {
        "a", "an", "and", "are", "at", "be", "becomes", "degree", "degrees", "graph", "is", "line",
        "of", "one", "the", "then", "to", "with",
    }
    tokens_o = re.findall(r"[a-z]+", original_fact.lower())
    tokens_c = re.findall(r"[a-z]+", counterfactual_fact.lower())
    return (
        [token for token in tokens_o if token not in stop and token not in tokens_c],
        [token for token in tokens_c if token not in stop and token not in tokens_o],
    )


def _first_match(text: str, terms: Iterable[str]) -> int | None:
    positions = []
    for term in terms:
        match = re.search(rf"(?<![A-Za-z0-9]){re.escape(term.lower())}(?![A-Za-z0-9])", text.lower())
        if match:
            positions.append(match.start())
    return min(positions) if positions else None


def annotate_rollouts(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_base: dict[str, dict[str, dict]] = defaultdict(dict)
    for row in rows:
        by_base[str(row["base_problem_id"])][str(row["condition"])] = row
    enriched: list[dict[str, Any]] = []
    boxed = re.compile(r"\\boxed\s*\{([^}]*)\}")
    for base, conditions in by_base.items():
        original_ids = conditions["original"]["generated_token_ids"]
        counter_ids = conditions["counterfactual"]["generated_token_ids"]
        sham_ids = conditions["sham"]["generated_token_ids"]

        def divergence(left: list[int], right: list[int]) -> int | None:
            for index, (a, b) in enumerate(zip(left, right)):
                if int(a) != int(b):
                    return index
            return min(len(left), len(right)) if len(left) != len(right) else None

        def sentences(text: str) -> list[str]:
            return [part.strip() for part in re.split(r"(?<=[.!?])\s+|\n+", text) if part.strip()]

        def sentence_divergence(left: str, right: str) -> dict[str, Any]:
            left_sentences = sentences(left)
            right_sentences = sentences(right)
            for index, (a, b) in enumerate(zip(left_sentences, right_sentences)):
                if a != b:
                    return {"sentence_index": index, "left": a, "right": b}
            if len(left_sentences) != len(right_sentences):
                index = min(len(left_sentences), len(right_sentences))
                return {
                    "sentence_index": index,
                    "left": left_sentences[index] if index < len(left_sentences) else None,
                    "right": right_sentences[index] if index < len(right_sentences) else None,
                }
            return {"sentence_index": None, "left": None, "right": None}

        shared = {
            "first_token_divergence_original_vs_counterfactual": divergence(original_ids, counter_ids),
            "first_token_divergence_original_vs_sham": divergence(original_ids, sham_ids),
            "first_meaningful_sentence_divergence_original_vs_counterfactual": sentence_divergence(
                str(conditions["original"]["continuation_text"]),
                str(conditions["counterfactual"]["continuation_text"]),
            ),
            "first_meaningful_sentence_divergence_original_vs_sham": sentence_divergence(
                str(conditions["original"]["continuation_text"]), str(conditions["sham"]["continuation_text"])
            ),
        }
        for condition in ("original", "counterfactual", "sham"):
            row = dict(conditions[condition])
            terms_o, terms_c = _distinctive_values(str(row["original_fact"]), str(row["counterfactual_fact"]))
            text = str(row["continuation_text"])
            pos_o = _first_match(text, terms_o)
            pos_c = _first_match(text, terms_c)
            if pos_o is not None and pos_c is None:
                fact_statement = "original_fact"
                first_position = pos_o
            elif pos_c is not None and pos_o is None:
                fact_statement = "counterfactual_fact"
                first_position = pos_c
            elif pos_o is not None and pos_c is not None:
                fact_statement = "both_or_ambiguous"
                first_position = min(pos_o, pos_c)
            else:
                fact_statement = "neither_detected"
                first_position = None
            answers = boxed.findall(text)
            row.update(
                {
                    **shared,
                    "original_fact_signature": terms_o,
                    "counterfactual_fact_signature": terms_c,
                    "first_entity_or_fact_statement": fact_statement,
                    "first_fact_character_offset": first_position,
                    "final_answer_if_reached": answers[-1] if answers else None,
                    "rollout_is_single_seed_validation_not_frequency_estimate": True,
                    "automatic_annotation_requires_manual_audit": fact_statement in {"both_or_ambiguous", "neither_detected"},
                }
            )
            enriched.append(row)
    order = {"original": 0, "counterfactual": 1, "sham": 2}
    enriched.sort(key=lambda row: (int(row["base_problem_id"]), order[str(row["condition"])]))
    return enriched


def primary_statistics(facts: list[dict[str, Any]]) -> dict[str, Any]:
    ce = [float(row["CE"]) for row in facts]
    controlled = [float(row["CE_controlled"]) for row in facts]
    sham = [float(row["sham_shift"]) for row in facts]
    target_minus_absolute_sham = [target - abs(control) for target, control in zip(ce, sham)]
    js_cf = [float(row["js_original_counterfactual"]) for row in facts]
    js_sham = [float(row["js_original_sham"]) for row in facts]
    target_exceeds_absolute_sham = [float(row["CE"]) > abs(float(row["sham_shift"])) for row in facts]
    target_js_exceeds_sham = [a > b for a, b in zip(js_cf, js_sham)]
    return {
        "independent_unit": "base_problem_id",
        "n_unique_base_problems": len(facts),
        "effect_definition": "CE = D(original image) - D(counterfactual image); positive is expected",
        "primary_CE": summarize_effect_values(ce, seed=BOOTSTRAP_SEED, resamples=BOOTSTRAP_RESAMPLES),
        "sham_controlled_CE": summarize_effect_values(
            controlled, seed=BOOTSTRAP_SEED + 10, resamples=BOOTSTRAP_RESAMPLES
        ),
        "sham_shift": summarize_effect_values(sham, seed=BOOTSTRAP_SEED + 20, resamples=BOOTSTRAP_RESAMPLES),
        "paired_target_CE_minus_absolute_sham": summarize_effect_values(
            target_minus_absolute_sham, seed=BOOTSTRAP_SEED + 30, resamples=BOOTSTRAP_RESAMPLES
        ),
        "target_CE_exceeds_absolute_sham": {
            "count": int(sum(target_exceeds_absolute_sham)),
            "proportion": float(np.mean(target_exceeds_absolute_sham)),
        },
        "secondary_JS": {
            "original_vs_counterfactual_mean": float(np.mean(js_cf)),
            "original_vs_sham_mean": float(np.mean(js_sham)),
            "target_exceeds_sham_count": int(sum(target_js_exceeds_sham)),
            "target_exceeds_sham_proportion": float(np.mean(target_js_exceeds_sham)),
            "not_primary_metric": True,
        },
        "per_problem": [
            {
                "base_problem_id": str(row["base_problem_id"]),
                "example_id": str(row["example_id"]),
                "CE": float(row["CE"]),
                "sham_shift": float(row["sham_shift"]),
                "CE_controlled": float(row["CE_controlled"]),
                "expected_direction": bool(float(row["CE"]) > 0),
                "target_exceeds_absolute_sham": bool(float(row["CE"]) > abs(float(row["sham_shift"]))),
            }
            for row in facts
        ],
        "attention_not_used_as_primary_measure": True,
    }


def evidence_statistics(facts: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in facts:
        grouped[str(row["evidence_type"])].append(row)
    return {
        evidence_type: {
            "CE": summarize_effect_values(
                [float(row["CE"]) for row in rows], seed=BOOTSTRAP_SEED + index, resamples=BOOTSTRAP_RESAMPLES
            ),
            "CE_controlled": summarize_effect_values(
                [float(row["CE_controlled"]) for row in rows],
                seed=BOOTSTRAP_SEED + 100 + index,
                resamples=BOOTSTRAP_RESAMPLES,
            ),
        }
        for index, (evidence_type, rows) in enumerate(sorted(grouped.items()))
    }


def temporal_statistics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    pre = [row for row in rows if row["phase"] == "pre_e0"]
    common_offsets = [-64, -32, -16, -8, 0]
    curve = []
    for offset in common_offsets:
        values = [float(row["CE_controlled"]) for row in pre if int(row["relative_to_e0_tokens"]) == offset]
        if values:
            curve.append(
                {
                    "relative_to_e0_tokens": offset,
                    "CE_controlled": summarize_effect_values(
                        values, seed=BOOTSTRAP_SEED + 200 + offset, resamples=BOOTSTRAP_RESAMPLES
                    ),
                    "JS_original_counterfactual_mean": float(
                        np.mean(
                            [
                                float(row["js_original_counterfactual"])
                                for row in pre
                                if int(row["relative_to_e0_tokens"]) == offset
                            ]
                        )
                    ),
                }
            )
    by_base: dict[str, list[dict]] = defaultdict(list)
    for row in pre:
        by_base[str(row["base_problem_id"])].append(row)
    onset_rows = []
    for base, base_rows in sorted(by_base.items(), key=lambda item: int(item[0])):
        early_rows = [row for row in base_rows if int(row["relative_to_e0_tokens"]) <= -8]
        qualifying = sorted(
            [
                row
                for row in early_rows
                if float(row["CE"]) > 0 and float(row["CE_controlled"]) > 0
            ],
            key=lambda row: int(row["relative_to_e0_tokens"]),
        )
        onset_rows.append(
            {
                "base_problem_id": base,
                "early_checkpoint_evaluable": bool(early_rows),
                "strict_pre_e0_sensitivity_at_or_before_minus_8": bool(qualifying) if early_rows else None,
                "earliest_observed_relative_checkpoint": (
                    int(qualifying[0]["relative_to_e0_tokens"]) if qualifying else None
                ),
                "criterion": "CE > 0 and sham-controlled CE > 0 at a checkpoint no later than E0-8",
            }
        )
    evaluable = [row for row in onset_rows if row["early_checkpoint_evaluable"]]
    sensitive_count = sum(bool(row["strict_pre_e0_sensitivity_at_or_before_minus_8"]) for row in evaluable)
    return {
        "checkpoint_definition": "prefix length; 0 means the exact y_<E0 boundary ending at generated token E0-1",
        "all_pre_e0_checkpoints_are_strictly_before_e0": True,
        "common_checkpoint_curve": curve,
        "onset_by_problem": onset_rows,
        "sensitive_at_or_before_minus_8_count": sensitive_count,
        "early_checkpoint_evaluable_count": len(evaluable),
        "early_checkpoint_not_evaluable_count": len(onset_rows) - len(evaluable),
        "sensitive_at_or_before_minus_8_proportion": float(sensitive_count / len(evaluable)) if evaluable else None,
    }


def attention_moderator(facts: list[dict[str, Any]], manifest: list[dict[str, Any]]) -> dict[str, Any]:
    timing_rows = read_jsonl(ROOT / "outputs/stage2c/analysis/timing_categories.jsonl")
    by_key = {
        (str(row["example_id"]), int(row["events"]["e0"][0])): row
        for row in timing_rows
    }
    manifest_by_base = {str(row["base_problem_id"]): row for row in manifest}
    matched = []
    for fact in facts:
        base = str(fact["base_problem_id"])
        item = manifest_by_base[base]
        key = (str(item["example_id"]), int(item["event"]["e0_start_token"]))
        attention = by_key.get(key)
        if attention is None:
            continue
        matched.append(
            {
                "base_problem_id": base,
                "example_id": key[0],
                "timing_category": attention["timing_category"],
                "pre_e0_roi_density": float(
                    attention["prediction_aligned_region_means"]["roi_per_token_density"]["PRE"]
                ),
                "CE": float(fact["CE"]),
                "CE_controlled": float(fact["CE_controlled"]),
            }
        )
    if len(matched) >= 3:
        rho, p_value = spearmanr(
            [row["pre_e0_roi_density"] for row in matched], [row["CE_controlled"] for row in matched]
        )
        correlation = {"spearman_rho": float(rho), "two_sided_p_value": float(p_value)}
    else:
        correlation = {"spearman_rho": None, "two_sided_p_value": None}
    categories = defaultdict(list)
    for row in matched:
        categories[row["timing_category"]].append(row["CE_controlled"])
    return {
        "analysis_role": "secondary moderator analysis run only after primary cohort and scores were frozen",
        "matched_problem_count": len(matched),
        "unmatched_problem_count": len(facts) - len(matched),
        "pre_e0_density_vs_CE_controlled": correlation,
        "category_descriptives": {
            category: {"n": len(values), "mean_CE_controlled": float(np.mean(values)), "median_CE_controlled": float(np.median(values))}
            for category, values in sorted(categories.items())
        },
        "matched_rows": matched,
        "attention_is_descriptive_and_not_a_primary_measure": True,
        "small_overlap_limits_inference": len(matched) < 20,
    }


def _canvas(title: str) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (1200, 720), "white")
    draw = ImageDraw.Draw(image)
    draw.text((40, 22), title, fill="black")
    draw.line((80, 650, 1160, 650), fill="black", width=2)
    draw.line((80, 80, 80, 650), fill="black", width=2)
    return image, draw


def _xy(value: float, minimum: float, maximum: float, low: int = 630, high: int = 100) -> int:
    if maximum <= minimum:
        return (low + high) // 2
    return int(low - (value - minimum) / (maximum - minimum) * (low - high))


def make_figures(
    facts: list[dict[str, Any]], temporal: dict[str, Any], rollouts: list[dict[str, Any]], moderator: dict[str, Any]
) -> None:
    ensure_directory(FIGURES)
    values = [float(row["CE_controlled"]) for row in facts]
    image, draw = _canvas("Sham-controlled counterfactual effect by independent base problem")
    bound = max(abs(min(values)), abs(max(values)), 1e-9)
    zero = _xy(0, -bound, bound)
    draw.line((80, zero, 1160, zero), fill=(120, 120, 120), width=2)
    width = 1080 / len(values)
    for index, value in enumerate(values):
        x0 = int(80 + index * width + 1)
        x1 = int(80 + (index + 1) * width - 1)
        y = _xy(value, -bound, bound)
        draw.rectangle((x0, min(y, zero), x1, max(y, zero)), fill=(36, 130, 190) if value > 0 else (210, 80, 70))
    image.save(FIGURES / "per_problem_controlled_ce.png")

    image, draw = _canvas("Distribution of sham-controlled counterfactual effects")
    bins = min(12, max(5, int(math.sqrt(len(values)))))
    counts, edges = np.histogram(values, bins=bins)
    maximum = max(int(counts.max()), 1)
    for index, count in enumerate(counts):
        x0 = int(90 + index * (1050 / bins))
        x1 = int(90 + (index + 1) * (1050 / bins) - 3)
        y = _xy(float(count), 0, maximum)
        draw.rectangle((x0, y, x1, 650), fill=(55, 125, 185))
        draw.text((x0, 665), f"{edges[index]:.1f}", fill="black")
    image.save(FIGURES / "controlled_ce_distribution.png")

    condition_means = {
        "original": float(np.mean([row["D_original"] for row in facts])),
        "counterfactual": float(np.mean([row["D_counterfactual"] for row in facts])),
        "sham": float(np.mean([row["D_sham"] for row in facts])),
    }
    image, draw = _canvas("Mean evidence preference D(I) by image condition")
    bound = max(*(abs(value) for value in condition_means.values()), 1e-9)
    zero = _xy(0, -bound, bound)
    draw.line((80, zero, 1160, zero), fill=(130, 130, 130), width=2)
    colors_by_condition = {"original": (45, 130, 190), "counterfactual": (225, 105, 55), "sham": (100, 160, 100)}
    for index, (condition, value) in enumerate(condition_means.items()):
        x0 = 190 + index * 330
        x1 = x0 + 180
        y = _xy(value, -bound, bound)
        draw.rectangle((x0, min(y, zero), x1, max(y, zero)), fill=colors_by_condition[condition])
        draw.text((x0, 665), condition, fill="black")
        draw.text((x0, max(85, min(y, zero) - 18)), f"{value:.3f}", fill="black")
    image.save(FIGURES / "condition_fact_preferences.png")

    image, draw = _canvas("Target counterfactual effect versus sham shift")
    x_values = [float(row["sham_shift"]) for row in facts]
    y_values = [float(row["CE"]) for row in facts]
    bound = max(*(abs(value) for value in x_values + y_values), 1e-9)
    draw.line((80, _xy(0, -bound, bound), 1160, _xy(0, -bound, bound)), fill=(160, 160, 160), width=1)
    for x, y in zip(x_values, y_values):
        px = int(80 + (x + bound) / (2 * bound) * 1080)
        py = _xy(y, -bound, bound)
        draw.ellipse((px - 4, py - 4, px + 4, py + 4), fill=(30, 90, 180))
    image.save(FIGURES / "target_ce_vs_sham_shift.png")

    curve = temporal["common_checkpoint_curve"]
    image, draw = _canvas("Strict pre-E0 sham-controlled sensitivity curve")
    if curve:
        low = min(row["CE_controlled"]["mean_bootstrap_ci"]["ci_low"] for row in curve)
        high = max(row["CE_controlled"]["mean_bootstrap_ci"]["ci_high"] for row in curve)
        span = max(high - low, 1e-9)
        low -= span * 0.1
        high += span * 0.1
        points = []
        for index, row in enumerate(curve):
            x = int(100 + index * (1030 / max(len(curve) - 1, 1)))
            summary = row["CE_controlled"]
            y = _xy(summary["mean"], low, high)
            draw.line((x, _xy(summary["mean_bootstrap_ci"]["ci_low"], low, high), x, _xy(summary["mean_bootstrap_ci"]["ci_high"], low, high)), fill=(80, 80, 80), width=2)
            draw.text((x - 16, 665), str(row["relative_to_e0_tokens"]), fill="black")
            points.append((x, y))
        if len(points) > 1:
            draw.line(points, fill=(20, 110, 180), width=4)
        for x, y in points:
            draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill=(20, 110, 180))
    image.save(FIGURES / "temporal_sensitivity_curve.png")

    grouped = defaultdict(list)
    for row in facts:
        grouped[str(row["evidence_type"])].append(float(row["CE_controlled"]))
    image, draw = _canvas("Sham-controlled effect by evidence type")
    type_means = [(key, float(np.mean(value))) for key, value in sorted(grouped.items())]
    bound = max(*(abs(value) for _, value in type_means), 1e-9)
    zero = _xy(0, -bound, bound)
    draw.line((80, zero, 1160, zero), fill=(130, 130, 130), width=2)
    for index, (label, value) in enumerate(type_means):
        width = 1040 / max(len(type_means), 1)
        x0 = int(100 + index * width)
        x1 = int(x0 + width * 0.65)
        y = _xy(value, -bound, bound)
        draw.rectangle((x0, min(y, zero), x1, max(y, zero)), fill=(60, 130, 185))
        draw.text((x0, 665), label[:24], fill="black")
    image.save(FIGURES / "effect_by_evidence_type.png")

    expected = sum(float(row["CE"]) > 0 for row in facts) / len(facts)
    controlled_expected = sum(float(row["CE_controlled"]) > 0 for row in facts) / len(facts)
    image, draw = _canvas("Proportion of base problems with expected-direction effects")
    for index, (label, value) in enumerate((("CE > 0", expected), ("controlled CE > 0", controlled_expected))):
        x0 = 260 + index * 430
        x1 = x0 + 220
        y = _xy(value, 0, 1)
        draw.rectangle((x0, y, x1, 650), fill=(55, 135, 185))
        draw.text((x0, 665), label, fill="black")
        draw.text((x0 + 65, y - 20), f"{value:.1%}", fill="black")
    image.save(FIGURES / "expected_direction_proportion.png")

    counts = Counter((row["condition"], row["first_entity_or_fact_statement"]) for row in rollouts)
    image, draw = _canvas("Short-rollout first fact classification (single matched seed)")
    categories = ["original_fact", "counterfactual_fact", "both_or_ambiguous", "neither_detected"]
    conditions = ["original", "counterfactual", "sham"]
    maximum = max(counts.values(), default=1)
    colors = [(50, 130, 190), (230, 120, 45), (150, 100, 170), (130, 130, 130)]
    group_width = 1080 / len(conditions)
    for ci, condition in enumerate(conditions):
        for ai, category in enumerate(categories):
            value = counts[(condition, category)]
            bar_width = group_width / (len(categories) + 1)
            x0 = int(90 + ci * group_width + ai * bar_width)
            x1 = int(x0 + bar_width - 3)
            y = _xy(value, 0, maximum)
            draw.rectangle((x0, y, x1, 650), fill=colors[ai])
        draw.text((int(100 + ci * group_width), 665), condition, fill="black")
    image.save(FIGURES / "rollout_fact_classification.png")

    matched = moderator["matched_rows"]
    image, draw = _canvas("Secondary: pre-E0 ROI attention density versus controlled CE")
    if matched:
        xs = [row["pre_e0_roi_density"] for row in matched]
        ys = [row["CE_controlled"] for row in matched]
        xmin, xmax = min(xs), max(xs)
        ymin, ymax = min(ys), max(ys)
        for x, y in zip(xs, ys):
            px = int(90 + (x - xmin) / max(xmax - xmin, 1e-12) * 1050)
            py = _xy(y, ymin, ymax)
            draw.ellipse((px - 4, py - 4, px + 4, py + 4), fill=(90, 90, 90))
    image.save(FIGURES / "secondary_attention_moderator.png")

    by_base_rollouts = defaultdict(dict)
    for row in rollouts:
        by_base_rollouts[str(row["base_problem_id"])][str(row["condition"])] = row
    ranked = sorted(facts, key=lambda row: float(row["CE_controlled"]), reverse=True)
    representatives = ranked[:2] + ranked[-2:]
    image = Image.new("RGB", (1400, 900), "white")
    draw = ImageDraw.Draw(image)
    draw.text((35, 25), "Representative strongest and weakest counterfactual effects", fill="black")
    y = 70
    for row in representatives:
        base = str(row["base_problem_id"])
        rollout = by_base_rollouts[base]
        draw.text(
            (35, y),
            f"base {base} | CE={float(row['CE']):.3f} | sham={float(row['sham_shift']):.3f} | controlled={float(row['CE_controlled']):.3f}",
            fill="black",
        )
        y += 24
        for condition in ("original", "counterfactual", "sham"):
            text = " ".join(str(rollout[condition]["continuation_text"]).split())[:165]
            draw.text((55, y), f"{condition}: {text}", fill="black")
            y += 24
        y += 30
    image.save(FIGURES / "representative_success_failure.png")


def main() -> None:
    manifest = read_jsonl(PRIMARY)
    expected = [str(row["base_problem_id"]) for row in manifest]
    if len(expected) != len(set(expected)):
        raise RuntimeError("Primary manifest has duplicate base_problem_id values")
    facts, temporal_rows, raw_rollouts = aggregate_shards(expected)
    hashes_by_base = defaultdict(set)
    for row in [*facts, *temporal_rows, *raw_rollouts]:
        hashes_by_base[str(row["base_problem_id"])].add(str(row["prefix_sha256"]))
    primary_hashes = {str(row["base_problem_id"]): str(row["prefix_sha256"]) for row in facts}
    for base, item in ((str(row["base_problem_id"]), row) for row in manifest):
        if primary_hashes[base] != str(item["prefix_sha256"]):
            raise RuntimeError(f"Frozen/primary prefix hash mismatch for base {base}")
    rollouts = annotate_rollouts(raw_rollouts)
    primary = primary_statistics(facts)
    temporal = temporal_statistics(temporal_rows)
    evidence = evidence_statistics(facts)
    write_jsonl(SCORE_OUT / "fact_preference.jsonl", facts)
    write_jsonl(SCORE_OUT / "temporal_sensitivity.jsonl", temporal_rows)
    write_jsonl(SCORE_OUT / "rollout_results.jsonl", rollouts)
    write_json(ANALYSIS / "primary_statistics.json", primary)
    write_json(ANALYSIS / "evidence_type_statistics.json", evidence)
    write_json(ANALYSIS / "temporal_sensitivity_statistics.json", temporal)
    # The moderator is deliberately computed only after the primary files above are frozen.
    moderator = attention_moderator(facts, manifest)
    write_json(ANALYSIS / "attention_moderator_analysis.json", moderator)
    make_figures(facts, temporal, rollouts, moderator)
    result = {
        "unique_base_problems": len(facts),
        "fact_rows": len(facts),
        "temporal_rows": len(temporal_rows),
        "rollout_rows": len(rollouts),
        "all_primary_prefix_hashes_match_frozen_manifest": True,
        "all_three_rollout_conditions_use_primary_prefix_hash": all(
            str(row["prefix_sha256"]) == primary_hashes[str(row["base_problem_id"])] for row in rollouts
        ),
        "figures": sorted(path.name for path in FIGURES.glob("*.png")),
    }
    write_json(ANALYSIS / "analysis_validation.json", result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
