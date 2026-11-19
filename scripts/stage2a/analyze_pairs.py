#!/usr/bin/env python3
"""Run Stage 2A within-problem descriptive analysis on existing Stage 1 bundles."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.stats import spearmanr

from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl
from visual_reasoning.stage2a.analysis import (
    holm_adjust,
    normalized_token_bins,
    paired_effect,
    progress_window_mean,
    token_weighted_semantic_means,
)


CLEAR_SHIFT = {
    "119": "VI text redundantly states sector/base radii retained visually; VD removes text availability",
    "136": "tree-shadow length 9 moves from VI text into VD image",
    "139": "candle, tube, and image dimensions move from VI text into VD image",
    "140": "net height and horizontal distances move from VI text into VD image",
    "141": "building/benchmark shadow dimensions move from VI text into VD image",
    "147": "benchmark and flagpole-shadow dimensions move from VI text into VD image",
    "148": "bamboo-pole height becomes image-only in VD",
    "153": "window and shadow dimensions move from VI text into VD image",
    "154": "ladder/wall dimensions move from VI text into VD image",
    "155": "observer height and ground distances move from VI text into VD image",
    "622": "logarithm formula moves from VI text into VD image",
    "752": "sqrt(3)x prism dimension moves from VI text into VD image",
    "753": "cylinder radius 3 moves from VI text into VD image",
}
MIXED_SHIFT = {
    "760": "radius label moves into VD image while several relational constraints become explicit in VD text",
}
NO_EFFECTIVE_VISUAL_SHIFT = {
    "546", "548", "550", "551", "560", "565", "567", "574", "575", "579", "594",
    "609", "611", "613", "614", "615", "616", "617", "618", "621", "751", "768",
}
VARIANTS = ("Vision Intensive", "Vision Dominant")
MODALITIES = ("visual", "prompt", "reasoning")
SEMANTIC_LABELS = (
    "VISUAL_READ", "COMPUTE", "RELATION_INFERENCE", "VERIFY", "PLAN", "ANSWER_SELECTION", "OTHER"
)
BIN_COUNT = 20


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pairing-manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def weighted_optional(spans: list[dict[str, Any]], key: str) -> float:
    values, weights = [], []
    for span in spans:
        value = span["visual_focus_metrics"].get(key)
        if value is None or not math.isfinite(float(value)):
            continue
        values.append(float(value))
        weights.append(int(span["end_token"]) - int(span["start_token"]))
    return float(np.average(values, weights=weights)) if values else 0.0


def expand_span_metric(spans: list[dict[str, Any]], key: str, token_count: int) -> np.ndarray:
    result = np.full((token_count,), np.nan, dtype=np.float64)
    for span in spans:
        value = span["visual_focus_metrics"].get(key)
        if value is not None and math.isfinite(float(value)):
            result[int(span["start_token"]) : int(span["end_token"])] = float(value)
    finite = np.isfinite(result)
    if not finite.any():
        return np.zeros_like(result)
    first = int(np.flatnonzero(finite)[0])
    result[:first] = result[first]
    for index in range(first + 1, token_count):
        if not math.isfinite(float(result[index])):
            result[index] = result[index - 1]
    return result


def safe_spearman(left: np.ndarray, right: np.ndarray) -> float:
    if left.size < 3 or float(left.std()) == 0 or float(right.std()) == 0:
        return 0.0
    return float(spearmanr(left, right).statistic)


def load_trajectory(row: dict[str, Any]) -> dict[str, Any]:
    root = Path(row["artifact_dir"])
    input_row = read_json(root / "input.json")
    result = read_json(root / "result.json")
    spans = read_json(root / "spans.json")
    peaks = read_json(root / "candidate_visual_peaks.json")
    with np.load(root / "attention_summary.npz", allow_pickle=False) as arrays:
        modality = np.asarray(arrays["modality_by_layer"], dtype=np.float64).mean(axis=1)
        density = np.asarray(arrays["modality_density_by_layer"], dtype=np.float64).mean(axis=1)
    with np.load(root / "uncertainty.npz", allow_pickle=False) as arrays:
        uncertainty = np.stack(
            (
                np.asarray(arrays["entropy"], dtype=np.float64),
                np.asarray(arrays["top1_probability"], dtype=np.float64),
                np.asarray(arrays["top1_top2_margin"], dtype=np.float64),
            ),
            axis=-1,
        )
    token_count = modality.shape[0]
    if density.shape != modality.shape or uncertainty.shape != (token_count, 3):
        raise ValueError(f"{row['example_id']}: token arrays disagree")
    signals = np.concatenate((modality, density, uncertainty), axis=1)
    names = (
        "visual_mass", "prompt_mass", "reasoning_mass",
        "visual_density", "prompt_density", "reasoning_density",
        "entropy", "top1_probability", "top1_top2_margin",
    )
    bins = normalized_token_bins(signals, BIN_COUNT)
    metrics = {name: float(signals[:, index].mean()) for index, name in enumerate(names)}
    for window, bounds in {"early": (0.0, 0.25), "middle": (0.25, 0.75), "late": (0.75, 1.0)}.items():
        window_values = progress_window_mean(signals, *bounds)
        for index, name in enumerate(names):
            metrics[f"{window}_{name}"] = float(window_values[index])
    peak_rows = peaks.get("peaks", [])
    late_peaks = [peak for peak in peak_rows if float(peak["normalized_generation_position"]) >= 0.75]
    metrics.update(
        {
            "reasoning_length": float(token_count),
            "peak_count": float(len(peak_rows)),
            "peak_rate_per_1000_tokens": 1000.0 * len(peak_rows) / token_count,
            "late_peak_count": float(len(late_peaks)),
            "late_peak_rate_per_1000_late_tokens": 1000.0 * len(late_peaks) / max(1.0, token_count * 0.25),
            "mean_peak_prominence": float(np.mean([p["prominence"] for p in peak_rows])) if peak_rows else 0.0,
            "mean_peak_timing": float(np.mean([p["normalized_generation_position"] for p in peak_rows])) if peak_rows else 0.0,
            "focus_similarity_to_prefill": weighted_optional(spans, "similarity_to_prefill"),
            "focus_similarity_to_previous_span": weighted_optional(spans, "similarity_to_previous_span"),
            "focus_spatial_entropy": weighted_optional(spans, "spatial_entropy"),
            "focus_topk_overlap": weighted_optional(spans, "topk_overlap_previous_span"),
            "focus_turnover": weighted_optional(spans, "turnover_from_previous_span"),
        }
    )
    turnover_tokens = expand_span_metric(spans, "turnover_from_previous_span", token_count)
    bins = np.concatenate((bins, normalized_token_bins(turnover_tokens[:, None], BIN_COUNT)), axis=1)
    bin_names = names + ("focus_turnover",)
    metrics["binned_visual_reasoning_mass_spearman"] = safe_spearman(bins[:, 0], bins[:, 2])
    semantic = token_weighted_semantic_means(spans, signals)
    return {
        "example_id": str(row["example_id"]),
        "variant": str(row["variant"]),
        "artifact_dir": str(root),
        "question": str(input_row["question"]),
        "answer": str(input_row["ground_truth_answer"]),
        "image_path": str(input_row["resolved_image_path"]),
        "image_id": str(row["image_id"]),
        "visual_token_count": len(input_row["visual_token_indices"]),
        "prompt_token_count": int(input_row["prompt_token_count"]),
        "status": str(result["status"]),
        "metrics": metrics,
        "bins": {name: bins[:, index].tolist() for index, name in enumerate(bin_names)},
        "semantic": {label: {name: float(values[index]) for index, name in enumerate(names)} for label, values in semantic.items()},
    }


def pair_class(base_problem_id: str) -> tuple[str, str]:
    if base_problem_id in CLEAR_SHIFT:
        return "clear_information_shift", CLEAR_SHIFT[base_problem_id]
    if base_problem_id in MIXED_SHIFT:
        return "mixed_redistribution", MIXED_SHIFT[base_problem_id]
    if base_problem_id in NO_EFFECTIVE_VISUAL_SHIFT:
        return "no_effective_visual_shift", "stored images are identical or no evidence item changes visual availability"
    raise KeyError(f"unclassified both-correct pair {base_problem_id}")


def curve_summary(pairs: list[dict[str, Any]], signal: str, seed: int) -> dict[str, Any]:
    vi = np.asarray([pair["Vision Intensive"]["bins"][signal] for pair in pairs], dtype=np.float64)
    vd = np.asarray([pair["Vision Dominant"]["bins"][signal] for pair in pairs], dtype=np.float64)
    diff = vd - vi
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, len(pairs), size=(10_000, len(pairs)))
    boot = diff[draws].mean(axis=1)
    return {
        "bin_edges": np.linspace(0.0, 1.0, BIN_COUNT + 1).tolist(),
        "vi_mean": vi.mean(axis=0).tolist(),
        "vd_mean": vd.mean(axis=0).tolist(),
        "paired_difference_mean": diff.mean(axis=0).tolist(),
        "paired_difference_bootstrap_95ci_low": np.percentile(boot, 2.5, axis=0).tolist(),
        "paired_difference_bootstrap_95ci_high": np.percentile(boot, 97.5, axis=0).tolist(),
    }


def font() -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("DejaVuSans.ttf", 14)
    except OSError:
        return ImageFont.load_default()


def save_curve_plot(curves: dict[str, dict[str, Any]], path: Path, title: str) -> None:
    width, height = 1200, 760
    canvas = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(canvas)
    draw.text((30, 18), title, fill="black", font=font())
    colors = {"vi": (50, 105, 170), "vd": (200, 70, 55)}
    signals = ("visual_mass", "reasoning_mass", "prompt_mass", "entropy")
    for panel, signal in enumerate(signals):
        row, col = divmod(panel, 2)
        left, top = 70 + col * 580, 70 + row * 330
        right, bottom = left + 510, top + 260
        draw.rectangle((left, top, right, bottom), outline=(80, 80, 80))
        values = curves[signal]["vi_mean"] + curves[signal]["vd_mean"]
        low, high = min(values), max(values)
        margin = max(1e-9, (high - low) * 0.1)
        low, high = low - margin, high + margin
        for name, key in (("VI", "vi_mean"), ("VD", "vd_mean")):
            points = []
            for index, value in enumerate(curves[signal][key]):
                x = left + int((index + 0.5) / BIN_COUNT * (right - left))
                y = bottom - int((value - low) / (high - low) * (bottom - top))
                points.append((x, y))
            draw.line(points, fill=colors[key[:2]], width=3)
        draw.text((left, top - 20), signal, fill="black", font=font())
        draw.text((right - 150, top + 10), "VI blue / VD red", fill=(60, 60, 60), font=font())
        draw.text((left, bottom + 7), "normalized reasoning progress 0% -> 100%", fill=(60, 60, 60), font=font())
    ensure_directory(path.parent)
    canvas.save(path)


def summarize_stratum(pairs: list[dict[str, Any]], seed_offset: int) -> dict[str, Any]:
    metric_names = sorted(pairs[0]["Vision Intensive"]["metrics"])
    metrics: dict[str, Any] = {}
    for name in metric_names:
        vi_values = [pair["Vision Intensive"]["metrics"][name] for pair in pairs]
        vd_values = [pair["Vision Dominant"]["metrics"][name] for pair in pairs]
        metrics[name] = paired_effect(vi_values, vd_values)
        differences = np.asarray(vd_values) - np.asarray(vi_values)
        influential = int(np.argmax(np.abs(differences)))
        metrics[name]["pair_ids_in_difference_order"] = [pair["base_problem_id"] for pair in pairs]
        metrics[name]["largest_absolute_difference"] = {
            "base_problem_id": pairs[influential]["base_problem_id"],
            "difference": float(differences[influential]),
            "mean_difference_excluding_pair": float(np.delete(differences, influential).mean()) if len(pairs) > 1 else None,
        }
    curve_signals = tuple(pairs[0]["Vision Intensive"]["bins"])
    curves = {name: curve_summary(pairs, name, 20260826 + seed_offset + index) for index, name in enumerate(curve_signals)}
    semantic: dict[str, Any] = {}
    for label in SEMANTIC_LABELS:
        matching = [pair for pair in pairs if label in pair["Vision Intensive"]["semantic"] and label in pair["Vision Dominant"]["semantic"]]
        if not matching:
            continue
        semantic[label] = {}
        for name in ("visual_mass", "visual_density", "prompt_density", "reasoning_density", "entropy"):
            semantic[label][name] = paired_effect(
                [pair["Vision Intensive"]["semantic"][label][name] for pair in matching],
                [pair["Vision Dominant"]["semantic"][label][name] for pair in matching],
            )
    delta_visual = np.asarray([pair["Vision Dominant"]["metrics"]["visual_mass"] - pair["Vision Intensive"]["metrics"]["visual_mass"] for pair in pairs])
    delta_reasoning = np.asarray([pair["Vision Dominant"]["metrics"]["reasoning_mass"] - pair["Vision Intensive"]["metrics"]["reasoning_mass"] for pair in pairs])
    delta_prompt = np.asarray([pair["Vision Dominant"]["metrics"]["prompt_mass"] - pair["Vision Intensive"]["metrics"]["prompt_mass"] for pair in pairs])
    sign_valid = (delta_visual != 0) & (delta_reasoning != 0)
    allocation = {
        "delta_visual_vs_delta_reasoning_spearman": safe_spearman(delta_visual, delta_reasoning),
        "delta_visual_vs_delta_prompt_spearman": safe_spearman(delta_visual, delta_prompt),
        "nonzero_sign_pair_count": int(sign_valid.sum()),
        "opposite_sign_visual_reasoning_fraction": float(np.mean(np.sign(delta_visual[sign_valid]) == -np.sign(delta_reasoning[sign_valid]))) if sign_valid.any() else None,
        "same_sign_visual_reasoning_fraction": float(np.mean(np.sign(delta_visual[sign_valid]) == np.sign(delta_reasoning[sign_valid]))) if sign_valid.any() else None,
        "boundary": "descriptive paired co-allocation only; source masses share a unit-sum constraint",
    }
    return {"pair_count": len(pairs), "metrics": metrics, "normalized_progress": curves, "semantic_alignment": semantic, "allocation": allocation}


def main() -> None:
    args = parse_args()
    rows = read_jsonl(args.pairing_manifest)
    by_problem: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_problem[str(row["base_problem_id"])].append(row)
    both_correct = {
        base: pair for base, pair in by_problem.items() if len(pair) == 2 and all(str(row["status"]) == "correct" for row in pair)
    }
    expected = set(CLEAR_SHIFT) | set(MIXED_SHIFT) | set(NO_EFFECTIVE_VISUAL_SHIFT)
    if set(both_correct) != expected or len(both_correct) != 36:
        raise ValueError("manual pair classification does not exactly cover the 36 both-correct pairs")
    pair_rows: list[dict[str, Any]] = []
    for base in sorted(both_correct, key=int):
        variants = {str(row["variant"]): load_trajectory(row) for row in both_correct[base]}
        if set(variants) != set(VARIANTS):
            raise ValueError(f"{base}: variants do not form a VI/VD pair")
        pair_type, rationale = pair_class(base)
        vi, vd = variants["Vision Intensive"], variants["Vision Dominant"]
        vi_hash = hashlib.sha256(Path(vi["image_path"]).read_bytes()).hexdigest()
        vd_hash = hashlib.sha256(Path(vd["image_path"]).read_bytes()).hexdigest()
        pair_rows.append(
            {
                "base_problem_id": base,
                "audit_class": pair_type,
                "audit_rationale": rationale,
                "same_question_text": vi["question"] == vd["question"],
                "same_image_bytes": vi_hash == vd_hash,
                "same_answer": vi["answer"] == vd["answer"],
                "Vision Intensive": vi,
                "Vision Dominant": vd,
                "scientific_boundary": "descriptive within-problem comparison; no causal visual-usage claim",
            }
        )
    strata = {
        "clear_information_shift": [pair for pair in pair_rows if pair["audit_class"] == "clear_information_shift"],
        "no_effective_visual_shift": [pair for pair in pair_rows if pair["audit_class"] == "no_effective_visual_shift"],
        "mixed_redistribution": [pair for pair in pair_rows if pair["audit_class"] == "mixed_redistribution"],
        "all_both_correct_context_only": pair_rows,
    }
    statistics = {
        "status": "complete",
        "difference_definition": "Vision Dominant minus Vision Intensive",
        "primary_stratum": "clear_information_shift",
        "classification_counts": {name: len(pairs) for name, pairs in strata.items()},
        "normalized_progress": {"bin_count": BIN_COUNT, "procedure": "direct mean over generated tokens falling into 20 equal index intervals per completed trajectory"},
        "strata": {name: summarize_stratum(pairs, index * 100) for index, (name, pairs) in enumerate(strata.items())},
        "inference_caveat": "paired p-values are exploratory; automatic semantic labels are noisy and candidate peaks are segmentation-scale-sensitive",
        "scientific_boundary": "attention and focus are descriptive evidence, not causal visual usage",
    }
    primary_core = (
        "visual_mass", "visual_density", "early_visual_mass", "middle_visual_mass", "late_visual_mass",
        "reasoning_density", "prompt_density", "peak_rate_per_1000_tokens",
        "late_peak_rate_per_1000_late_tokens", "focus_turnover", "entropy", "reasoning_length",
    )
    primary_metrics = statistics["strata"]["clear_information_shift"]["metrics"]
    adjusted = holm_adjust({name: float(primary_metrics[name]["wilcoxon_p_value"]) for name in primary_core})
    for name, value in adjusted.items():
        primary_metrics[name]["holm_adjusted_p_value_primary_family"] = value
    output = ensure_directory(args.output_dir)
    manifest_rows = []
    for pair in pair_rows:
        manifest_rows.append(
            {
                "base_problem_id": pair["base_problem_id"],
                "audit_class": pair["audit_class"],
                "audit_rationale": pair["audit_rationale"],
                "same_question_text": pair["same_question_text"],
                "same_image_bytes": pair["same_image_bytes"],
                "same_answer": pair["same_answer"],
                "vi_example_id": pair["Vision Intensive"]["example_id"],
                "vd_example_id": pair["Vision Dominant"]["example_id"],
                "vi_artifact_dir": pair["Vision Intensive"]["artifact_dir"],
                "vd_artifact_dir": pair["Vision Dominant"]["artifact_dir"],
                "vi_reasoning_length": int(pair["Vision Intensive"]["metrics"]["reasoning_length"]),
                "vd_reasoning_length": int(pair["Vision Dominant"]["metrics"]["reasoning_length"]),
                "vi_visual_token_count": pair["Vision Intensive"]["visual_token_count"],
                "vd_visual_token_count": pair["Vision Dominant"]["visual_token_count"],
                "scientific_boundary": pair["scientific_boundary"],
            }
        )
    write_jsonl(output / "both_correct_pair_manifest.jsonl", manifest_rows)
    write_json(output / "paired_statistics.json", statistics)
    for name, result in statistics["strata"].items():
        save_curve_plot(result["normalized_progress"], output / "figures" / f"normalized_progress_{name}.png", f"Stage 2A {name}: paired descriptive trajectories")
    print(json.dumps({"both_correct_pairs": len(pair_rows), "classification_counts": statistics["classification_counts"], "output": str(output)}, indent=2))


if __name__ == "__main__":
    main()
