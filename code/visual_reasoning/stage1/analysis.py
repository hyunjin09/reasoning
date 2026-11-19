"""Reproducible span and descriptive-signal analysis for Stage 1."""

from __future__ import annotations

import math
import re
from typing import Any, Iterable

import numpy as np
from scipy.signal import find_peaks

from visual_reasoning.stage0.analysis import correctness_status, extract_answer


SEMANTIC_LABELS = (
    "VISUAL_READ",
    "COMPUTE",
    "RELATION_INFERENCE",
    "VERIFY",
    "PLAN",
    "ANSWER_SELECTION",
    "OTHER",
)
VISUAL_PATTERNS = (
    r"\b(?:diagram|image|graph|plot|chart|shown|labeled|x-axis|y-axis|visuali[sz]e)\b",
    r"\bfigure\b(?!\s+out\b)",
    r"\blook(?:ing|ed|s)?\s+(?:at|closely|again)\b",
    r"\b(?:can|could)\s+see\b",
)
VERIFY_TERMS = ("check", "verify", "confirm", "reconsider", "make sure")
PLAN_TERMS = ("let's", "need to", "first", "approach", "plan", "step back", "we should")
RELATION_TERMS = (
    "angle",
    "triangle",
    "circle",
    "parallel",
    "perpendicular",
    "tangent",
    "line",
    "segment",
    "intersect",
    "equal",
    "relation",
)


def semantic_label(text: str) -> str:
    lower = text.lower()
    stripped = lower.strip()
    if re.search(r"(?:final\s+answer|answer\s+is|option\s+[a-e]|choice\s+[a-e])", lower) or re.fullmatch(
        r"(?:\*\*)?[a-e](?:\*\*)?(?:<\|im_end\|>)?", stripped
    ):
        return "ANSWER_SELECTION"
    if any(re.search(pattern, lower) for pattern in VISUAL_PATTERNS):
        return "VISUAL_READ"
    if any(term in lower for term in VERIFY_TERMS):
        return "VERIFY"
    if any(term in lower for term in PLAN_TERMS):
        return "PLAN"
    if re.search(r"\d\s*[+\-*/=]|[+\-*/=]\s*\d|\b(?:calculate|compute|subtract|add|multiply|divide)\b", lower):
        return "COMPUTE"
    if any(term in lower for term in RELATION_TERMS):
        return "RELATION_INFERENCE"
    return "OTHER"


def visual_reference_context(text: str) -> dict[str, Any]:
    lower = text.lower()
    matched = [match.group(0) for pattern in VISUAL_PATTERNS for match in re.finditer(pattern, lower)]
    return {"visual_reference_expressions": matched, "has_visual_reference": bool(matched)}


def build_spans(token_rows: list[dict[str, Any]], max_tokens: int = 64) -> list[dict[str, Any]]:
    spans: list[dict[str, Any]] = []
    start = 0
    pieces: list[str] = []
    for index, row in enumerate(token_rows):
        piece = str(row.get("decoded_token", ""))
        pieces.append(piece)
        raw_text = "".join(pieces)
        boundary = bool(re.search(r"[.!?](?:\s|$)|\n", piece)) or len(pieces) >= max_tokens
        if boundary and re.search(r"\b(?:vs|e\.g|i\.e|etc)\.\s*$", raw_text, flags=re.IGNORECASE):
            boundary = False
        if not boundary and index != len(token_rows) - 1:
            continue
        text = raw_text.strip()
        if not text and index != len(token_rows) - 1:
            continue
        stored_text = text if text else raw_text
        spans.append(
            {
                "span_id": len(spans),
                "start_token": start,
                "end_token": index + 1,
                "span_text": stored_text,
                "semantic_label": semantic_label(stored_text),
                "lexical_context": visual_reference_context(stored_text),
            }
        )
        start = index + 1
        pieces = []
    return spans


def add_source_densities(
    token_rows: list[dict[str, Any]],
    attention_arrays: dict[str, np.ndarray],
    prompt_length: int,
    visual_count: int,
) -> dict[str, np.ndarray]:
    modality = np.asarray(attention_arrays["modality_by_layer"], dtype=np.float32)
    key_lengths = np.asarray(attention_arrays["key_lengths"], dtype=np.int32)
    if modality.shape[0] != len(token_rows) or key_lengths.shape[0] != len(token_rows):
        raise ValueError("Attention arrays do not align with token rows")
    prompt_count = int(prompt_length) - int(visual_count)
    reasoning_counts = np.maximum(0, key_lengths - int(prompt_length))
    source_counts = np.stack(
        (
            np.full_like(reasoning_counts, int(visual_count)),
            np.full_like(reasoning_counts, prompt_count),
            reasoning_counts,
        ),
        axis=-1,
    ).astype(np.int32)
    denominators = source_counts[:, None, :].astype(np.float32)
    density = np.divide(modality, denominators, out=np.zeros_like(modality), where=denominators > 0)
    mean_mass = modality.mean(axis=1)
    mean_density = density.mean(axis=1)
    for index, row in enumerate(token_rows):
        row.update(
            {
                "visual_source_token_count": int(source_counts[index, 0]),
                "prompt_source_token_count": int(source_counts[index, 1]),
                "reasoning_source_token_count": int(source_counts[index, 2]),
                "visual_attention_density": float(mean_density[index, 0]),
                "prompt_attention_density": float(mean_density[index, 1]),
                "reasoning_attention_density": float(mean_density[index, 2]),
            }
        )
        for name, position in (("visual", 0), ("prompt", 1), ("reasoning", 2)):
            if f"{name}_attention_mass" not in row:
                row[f"{name}_attention_mass"] = float(mean_mass[index, position])
    return {**attention_arrays, "modality_density_by_layer": density, "source_token_counts": source_counts}


def _summary(values: np.ndarray) -> dict[str, float]:
    return {"mean": float(values.mean()), "maximum": float(values.max()), "end": float(values[-1])}


def _normalize_distribution(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=np.float32)
    total = float(values.sum())
    return values / total if total > 0 else np.zeros_like(values)


def _cosine(left: np.ndarray, right: np.ndarray) -> float | None:
    denominator = float(np.linalg.norm(left) * np.linalg.norm(right))
    return float(np.dot(left, right) / denominator) if denominator > 0 else None


def _topk_overlap(left: np.ndarray, right: np.ndarray, k: int) -> float | None:
    if not left.size or not right.size or float(left.sum()) <= 0 or float(right.sum()) <= 0:
        return None
    left_set = set(np.argpartition(left, -k)[-k:].tolist())
    right_set = set(np.argpartition(right, -k)[-k:].tolist())
    union = left_set | right_set
    return len(left_set & right_set) / len(union) if union else None


def aggregate_spans(
    spans: list[dict[str, Any]],
    token_rows: list[dict[str, Any]],
    attention_arrays: dict[str, np.ndarray],
) -> dict[str, np.ndarray]:
    modality = np.asarray(attention_arrays["modality_by_layer"], dtype=np.float32)
    density = np.asarray(attention_arrays["modality_density_by_layer"], dtype=np.float32)
    visual_focus = np.asarray(attention_arrays["visual_focus"], dtype=np.float32)
    prefill_focus = _normalize_distribution(visual_focus[0]) if visual_focus.shape[0] else np.zeros((visual_focus.shape[1],), dtype=np.float32)
    mass_rows: list[np.ndarray] = []
    density_rows: list[np.ndarray] = []
    focus_rows: list[np.ndarray] = []
    uncertainty_rows: list[np.ndarray] = []
    previous_focus: np.ndarray | None = None
    top_k = max(1, min(10, visual_focus.shape[1]))
    for span in spans:
        start, end = int(span["start_token"]), int(span["end_token"])
        span_mass = modality[start:end].mean(axis=0)
        span_density = density[start:end].mean(axis=0)
        focus = _normalize_distribution(visual_focus[start:end].mean(axis=0))
        entropy = np.asarray([float(row["next_token_entropy"]) for row in token_rows[start:end]], dtype=np.float32)
        top1 = np.asarray([float(row["top1_probability"]) for row in token_rows[start:end]], dtype=np.float32)
        margin = np.asarray([float(row["top1_top2_margin"]) for row in token_rows[start:end]], dtype=np.float32)
        visual_mass = np.asarray([float(row["visual_attention_mass"]) for row in token_rows[start:end]], dtype=np.float32)
        prompt_mass = np.asarray([float(row["prompt_attention_mass"]) for row in token_rows[start:end]], dtype=np.float32)
        reasoning_mass = np.asarray([float(row["reasoning_attention_mass"]) for row in token_rows[start:end]], dtype=np.float32)
        visual_density = np.asarray([float(row["visual_attention_density"]) for row in token_rows[start:end]], dtype=np.float32)
        prompt_density = np.asarray([float(row["prompt_attention_density"]) for row in token_rows[start:end]], dtype=np.float32)
        reasoning_density = np.asarray([float(row["reasoning_attention_density"]) for row in token_rows[start:end]], dtype=np.float32)
        entropy_terms = focus[focus > 0]
        spatial_entropy = float(-(entropy_terms * np.log(entropy_terms)).sum() / math.log(len(focus))) if len(focus) > 1 and entropy_terms.size else 0.0
        previous_similarity = _cosine(focus, previous_focus) if previous_focus is not None else None
        span["attention"] = {
            "visual_mass": _summary(visual_mass),
            "prompt_mass": _summary(prompt_mass),
            "reasoning_mass": _summary(reasoning_mass),
            "visual_density": _summary(visual_density),
            "prompt_density": _summary(prompt_density),
            "reasoning_density": _summary(reasoning_density),
        }
        span["uncertainty"] = {
            "entropy": _summary(entropy),
            "top1_probability": _summary(top1),
            "top1_top2_margin": _summary(margin),
        }
        span["visual_focus_metrics"] = {
            "similarity_to_prefill": _cosine(focus, prefill_focus),
            "similarity_to_previous_span": previous_similarity,
            "spatial_entropy": spatial_entropy,
            "topk": top_k,
            "topk_overlap_previous_span": _topk_overlap(focus, previous_focus, top_k) if previous_focus is not None else None,
            "turnover_from_previous_span": 1.0 - previous_similarity if previous_similarity is not None else None,
        }
        mass_rows.append(span_mass)
        density_rows.append(span_density)
        focus_rows.append(focus)
        uncertainty_rows.append(
            np.asarray(
                [
                    [entropy.mean(), entropy.max(), entropy[-1]],
                    [top1.mean(), top1.max(), top1[-1]],
                    [margin.mean(), margin.max(), margin[-1]],
                ],
                dtype=np.float32,
            )
        )
        previous_focus = focus
    return {
        "span_ranges": np.asarray([[span["start_token"], span["end_token"]] for span in spans], dtype=np.int32),
        "modality_mass_by_span_layer": np.stack(mass_rows) if mass_rows else np.empty((0, modality.shape[1], 3), dtype=np.float32),
        "modality_density_by_span_layer": np.stack(density_rows) if density_rows else np.empty((0, density.shape[1], 3), dtype=np.float32),
        "visual_focus_distribution": np.stack(focus_rows) if focus_rows else np.empty((0, visual_focus.shape[1]), dtype=np.float32),
        "uncertainty_by_span": np.stack(uncertainty_rows) if uncertainty_rows else np.empty((0, 3, 3), dtype=np.float32),
        "modality_names": np.asarray(("visual", "prompt", "reasoning")),
        "uncertainty_names": np.asarray(("entropy", "top1_probability", "top1_top2_margin")),
        "summary_names": np.asarray(("mean", "maximum", "end")),
    }


def candidate_visual_peaks(spans: list[dict[str, Any]]) -> dict[str, Any]:
    raw = np.asarray([float(span["attention"]["visual_mass"]["mean"]) for span in spans], dtype=np.float32)
    if raw.size >= 3:
        smoothed = np.convolve(np.pad(raw, (1, 1), mode="edge"), np.asarray([0.25, 0.5, 0.25]), mode="valid")
        prominence_threshold = max(float(smoothed.std()) * 0.5, np.finfo(np.float32).eps)
        positions, properties = find_peaks(smoothed, prominence=prominence_threshold, distance=2)
        prominences = properties.get("prominences", np.zeros_like(positions, dtype=np.float32))
    else:
        smoothed = raw.copy()
        prominence_threshold = float("inf")
        positions = np.empty((0,), dtype=np.int64)
        prominences = np.empty((0,), dtype=np.float32)
    peak_rows = []
    total_tokens = int(spans[-1]["end_token"]) if spans else 0
    for index, (position, prominence) in enumerate(zip(positions.tolist(), prominences.tolist())):
        peak_span = spans[position]
        token_midpoint = (int(peak_span["start_token"]) + int(peak_span["end_token"])) / 2.0
        previous_token_midpoint = None
        if index > 0:
            previous_span = spans[int(positions[index - 1])]
            previous_token_midpoint = (
                int(previous_span["start_token"]) + int(previous_span["end_token"])
            ) / 2.0
        peak_rows.append(
            {
                "span_id": int(position),
                "raw_visual_attention": float(raw[position]),
                "smoothed_visual_attention": float(smoothed[position]),
                "prominence": float(prominence),
                "token_midpoint": token_midpoint,
                "normalized_generation_position": float(token_midpoint / max(1, total_tokens)),
                "inter_peak_distance": None if index == 0 else int(position - positions[index - 1]),
                "inter_peak_token_distance": None if previous_token_midpoint is None else token_midpoint - previous_token_midpoint,
                "inter_peak_normalized_distance": None
                if previous_token_midpoint is None
                else (token_midpoint - previous_token_midpoint) / max(1, total_tokens),
            }
        )
    return {
        "method": "three-span [0.25,0.5,0.25] smoothing; scipy.signal.find_peaks; per-example prominence=0.5*SD; minimum distance=2 spans",
        "prominence_threshold": prominence_threshold,
        "span_count": len(spans),
        "peak_count": len(peak_rows),
        "peaks": peak_rows,
    }


def analyze_generation(
    generation: dict[str, Any],
    ground_truth: str,
    max_new_tokens: int,
    eos_token_ids: Iterable[int],
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, np.ndarray], dict[str, Any]]:
    token_rows = generation["token_rows"]
    arrays = generation["attention_arrays"]
    response = str(generation["full_generated_response"])
    token_ids = [int(value) for value in generation["generated_token_ids"]]
    eos_set = {int(value) for value in eos_token_ids}
    hit_cap = len(token_ids) >= int(max_new_tokens)
    predicted = extract_answer(response)
    status = "truncated" if hit_cap else correctness_status(predicted, ground_truth)
    complete = not hit_cap and predicted is not None and status != "invalid"
    spans = build_spans(token_rows)
    span_arrays = aggregate_spans(spans, token_rows, arrays)
    peaks = candidate_visual_peaks(spans)
    summary = {
        "full_generated_response": response,
        "extracted_final_answer": predicted,
        "ground_truth_answer": ground_truth,
        "status": status,
        "complete": complete,
        "correct": status == "correct",
        "truncated": hit_cap,
        "generated_token_count": len(token_ids),
        "generated_token_ids": token_ids,
        "runtime": generation["runtime"],
        "alignment": {
            "incremental_decode_alignment": bool(generation["incremental_decode_alignment"]),
            "token_score_alignment": len(token_rows) == len(token_ids),
            "attention_token_alignment": arrays is not None and arrays["modality_by_layer"].shape[0] == len(token_ids),
            "span_ranges_valid": all(0 <= int(span["start_token"]) < int(span["end_token"]) <= len(token_rows) for span in spans),
        },
        "candidate_visual_peaks": peaks,
    }
    return summary, spans, span_arrays, peaks
