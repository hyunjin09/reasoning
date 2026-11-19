"""Token, answer, span, and summary analysis for Stage 0."""

from __future__ import annotations

import math
import re
from statistics import median
from typing import Any, Iterable, Sequence

import torch


VISUAL_TERMS = ("look", "diagram", "figure", "shown", "labeled", "image", "visual", "see")
GEOMETRY_TERMS = ("angle", "triangle", "circle", "parallel", "perpendicular", "tangent", "line", "segment")
VERIFY_TERMS = ("check", "verify", "confirm", "therefore", "thus")


def predictive_metrics(logits: torch.Tensor, selected_token_id: int) -> dict[str, float]:
    values = logits.detach().float().reshape(-1)
    log_probs = torch.log_softmax(values, dim=-1)
    probs = torch.softmax(values, dim=-1)
    top_values, _ = torch.topk(probs, k=min(2, probs.numel()))
    top1 = float(top_values[0].item())
    top2 = float(top_values[1].item()) if top_values.numel() > 1 else 0.0
    entropy = float((-(probs * log_probs).sum()).item())
    return {
        "token_log_probability": float(log_probs[int(selected_token_id)].item()),
        "next_token_entropy": entropy,
        "top1_probability": top1,
        "top2_probability": top2,
        "top1_top2_margin": top1 - top2,
    }


def extract_answer(response: str, choices: Sequence[str] = ("A", "B", "C", "D", "E")) -> str | None:
    allowed = "".join(re.escape(choice.upper()) for choice in choices)
    explicit_patterns = (
        rf"(?:final\s+answer|answer|option|choice)\s*(?:is|:|=)?\s*\(?([{allowed}])\)?\b",
        rf"\boxed\{{\s*([{allowed}])\s*\}}",
    )
    for pattern in explicit_patterns:
        matches = re.findall(pattern, response, flags=re.IGNORECASE)
        if matches:
            return matches[-1].upper()
    standalone = re.findall(rf"(?<![A-Za-z])([{allowed}])(?![A-Za-z])", response, flags=re.IGNORECASE)
    return standalone[-1].upper() if standalone else None


def extract_reasoning(response: str) -> str:
    think_match = re.search(r"<think>(.*?)(?:</think>|$)", response, flags=re.DOTALL | re.IGNORECASE)
    if think_match:
        return think_match.group(1).strip()
    final_marker = re.search(r"(?:final\s+answer|answer)\s*(?:is|:|=)", response, flags=re.IGNORECASE)
    if final_marker:
        return response[: final_marker.start()].strip()
    return response.strip()


def provisional_semantic_label(text: str) -> str:
    lower = text.lower()
    if any(term in lower for term in VISUAL_TERMS):
        return "visual_reference"
    if any(term in lower for term in VERIFY_TERMS):
        return "verification"
    if re.search(r"(?:final\s+answer|answer\s+is|option\s+[A-E])", lower):
        return "answer_selection"
    if any(term in lower for term in GEOMETRY_TERMS):
        return "geometric_relation"
    if re.search(r"\d|[+\-*/=]", text):
        return "calculation"
    return "reasoning"


def lexical_context(text: str) -> dict[str, Any]:
    lower = text.lower()
    matched = [term for term in VISUAL_TERMS if re.search(rf"\b{re.escape(term)}\b", lower)]
    return {"visual_reference_expressions": matched, "has_visual_reference": bool(matched)}


def build_reasoning_spans(token_rows: list[dict[str, Any]], max_tokens: int = 64) -> list[dict[str, Any]]:
    spans: list[dict[str, Any]] = []
    start = 0
    pieces: list[str] = []
    for index, row in enumerate(token_rows):
        piece = str(row.get("decoded_token", ""))
        pieces.append(piece)
        boundary = bool(re.search(r"[.!?](?:\s|$)|\n", piece)) or len(pieces) >= max_tokens
        is_last = index == len(token_rows) - 1
        if not boundary and not is_last:
            continue
        text = "".join(pieces).strip()
        if text:
            spans.append(
                {
                    "span_id": len(spans),
                    "start_token": start,
                    "end_token": index + 1,
                    "span_text": text,
                    "provisional_semantic_label": provisional_semantic_label(text),
                    "lexical_context": lexical_context(text),
                }
            )
        start = index + 1
        pieces = []
    return spans


def aggregate_span_signals(
    spans: list[dict[str, Any]],
    token_rows: list[dict[str, Any]],
    signal_names: Iterable[str],
) -> None:
    for span in spans:
        rows = token_rows[int(span["start_token"]) : int(span["end_token"])]
        signals: dict[str, float | None] = {}
        for name in signal_names:
            values = [float(row[name]) for row in rows if row.get(name) is not None and math.isfinite(float(row[name]))]
            signals[name] = sum(values) / len(values) if values else None
        span["signals"] = signals


def correctness_status(predicted: str | None, ground_truth: str) -> str:
    if predicted is None:
        return "invalid"
    return "correct" if predicted.strip().upper() == ground_truth.strip().upper() else "wrong"


def correctness_summary(example_summaries: list[dict[str, Any]]) -> dict[str, Any]:
    lengths = [int(row["generated_token_count"]) for row in example_summaries]
    status_counts = {status: 0 for status in ("correct", "wrong", "invalid", "truncated")}
    for row in example_summaries:
        status = str(row["status"])
        status_counts[status] = status_counts.get(status, 0) + 1
    return {
        "total_examples": len(example_summaries),
        **status_counts,
        "average_reasoning_length_tokens": sum(lengths) / len(lengths) if lengths else 0.0,
        "median_reasoning_length_tokens": float(median(lengths)) if lengths else 0.0,
    }

