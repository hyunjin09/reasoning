"""Stage 1A.2 generation protocols and lightweight repetition diagnostics."""

from __future__ import annotations

import re
from collections import Counter
from typing import Any, Iterable

import numpy as np

from visual_reasoning.stage0.analysis import correctness_status, extract_answer


MAX_NEW_TOKENS_40960 = 40_960
OFFICIAL_THINKING_SEED = 1_234
OFFICIAL_QWEN_SOURCE = "https://github.com/QwenLM/Qwen3-VL#evaluation-reproduction"
OFFICIAL_QWEN_PARAMETERS: dict[str, Any] = {
    "do_sample": True,
    "temperature": 0.6,
    "top_p": 0.95,
    "top_k": 20,
    "repetition_penalty": 1.0,
    "presence_penalty": 0.0,
    "max_new_tokens": MAX_NEW_TOKENS_40960,
    "seed": OFFICIAL_THINKING_SEED,
}
GREEDY_PARAMETERS: dict[str, Any] = {
    "do_sample": False,
    "repetition_penalty": 1.0,
    "presence_penalty": 0.0,
    "max_new_tokens": MAX_NEW_TOKENS_40960,
    "seed": OFFICIAL_THINKING_SEED,
}


def protocol_parameters(name: str, max_new_tokens: int = MAX_NEW_TOKENS_40960, seed: int = OFFICIAL_THINKING_SEED) -> dict[str, Any]:
    if name == "greedy":
        values = dict(GREEDY_PARAMETERS)
    elif name == "official":
        values = dict(OFFICIAL_QWEN_PARAMETERS)
    else:
        raise ValueError(f"Unknown Stage 1 protocol: {name}")
    values["max_new_tokens"] = int(max_new_tokens)
    values["seed"] = int(seed)
    return values


def transformers_generation_kwargs(parameters: dict[str, Any]) -> dict[str, Any]:
    """Map the recorded protocol to behavior-changing Transformers kwargs.

    Transformers does not expose vLLM's presence_penalty. The official value is
    zero, so omitting it is exactly a no-op and is recorded as such.
    """

    kwargs: dict[str, Any] = {
        "do_sample": bool(parameters["do_sample"]),
        "repetition_penalty": float(parameters.get("repetition_penalty", 1.0)),
    }
    if kwargs["do_sample"]:
        kwargs.update(
            {
                "temperature": float(parameters["temperature"]),
                "top_p": float(parameters["top_p"]),
                "top_k": int(parameters["top_k"]),
            }
        )
    return kwargs


def classify_protocol_generation(
    generated_token_ids: list[int],
    response: str,
    ground_truth: str,
    max_new_tokens: int,
    eos_token_ids: Iterable[int],
) -> dict[str, Any]:
    eos = {int(value) for value in eos_token_ids}
    # The prospective gate requires termination *before* the safety ceiling.
    # Reaching the ceiling is a cap hit even if EOS happens to be sampled on
    # that final allowed step.
    hit_cap = len(generated_token_ids) >= int(max_new_tokens)
    ended_with_eos = bool(generated_token_ids and int(generated_token_ids[-1]) in eos)
    predicted = extract_answer(response)
    status = "truncated" if hit_cap else correctness_status(predicted, ground_truth)
    return {
        "status": status,
        "complete": not hit_cap and predicted is not None and status != "invalid",
        "correct": status == "correct",
        "truncated": hit_cap,
        "normal_termination": not hit_cap,
        "termination_reason": "safety_cap" if hit_cap else ("eos" if ended_with_eos else "other_normal_stop"),
        "ended_with_eos": ended_with_eos,
        "extracted_final_answer": predicted,
    }


def _word_tokens(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9]+|[^\w\s]", text.lower())


def _normalized_sentences(text: str) -> list[str]:
    pieces = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [re.sub(r"\s+", " ", piece.strip().lower()) for piece in pieces if piece.strip()]


def repeated_ngram_fraction(tokens: list[str], n: int) -> float:
    if len(tokens) < n:
        return 0.0
    ngrams = [tuple(tokens[index : index + n]) for index in range(len(tokens) - n + 1)]
    return 1.0 - len(set(ngrams)) / len(ngrams)


def repetition_diagnostics(text: str) -> dict[str, Any]:
    words = _word_tokens(text)
    sentences = _normalized_sentences(text)
    sentence_counts = Counter(sentences)
    repeated_sentence_occurrences = sum(count - 1 for count in sentence_counts.values() if count > 1)
    longest_identical_sentence_run = 0
    current_run = 0
    previous = None
    for sentence in sentences:
        current_run = current_run + 1 if sentence == previous else 1
        longest_identical_sentence_run = max(longest_identical_sentence_run, current_run)
        previous = sentence
    cue_patterns = {
        "wait": r"\bwait\b",
        "reconsider": r"\breconsider\w*\b",
        "lets_check": r"\blet['’]?s\s+(?:check|verify|reconsider)\b",
        "check_again": r"\b(?:check|verify|reconsider)(?:ing)?\s+again\b",
        "double_check": r"\bdouble[- ]check\b",
    }
    cue_counts = {name: len(re.findall(pattern, text, flags=re.IGNORECASE)) for name, pattern in cue_patterns.items()}
    trigram_fraction = repeated_ngram_fraction(words, 3)
    eightgram_fraction = repeated_ngram_fraction(words, 8)
    repeated_sentence_fraction = repeated_sentence_occurrences / len(sentences) if sentences else 0.0
    flags = {
        "high_repeated_trigrams": len(words) >= 200 and trigram_fraction >= 0.35,
        "high_repeated_eightgrams": len(words) >= 200 and eightgram_fraction >= 0.20,
        "high_repeated_sentences": len(sentences) >= 20 and repeated_sentence_fraction >= 0.20,
        "long_identical_sentence_run": longest_identical_sentence_run >= 3,
        "many_self_correction_cues": sum(cue_counts.values()) >= 20,
    }
    most_repeated_sentences = [
        {"sentence": sentence, "count": count}
        for sentence, count in sentence_counts.most_common(5)
        if count > 1
    ]
    return {
        "method": "exact normalized word n-gram and sentence repetition plus simple self-correction cue counts",
        "word_token_count": len(words),
        "sentence_count": len(sentences),
        "repeated_ngram_fraction": {
            "n3": trigram_fraction,
            "n4": repeated_ngram_fraction(words, 4),
            "n8": eightgram_fraction,
        },
        "repeated_sentence_occurrences": repeated_sentence_occurrences,
        "repeated_sentence_fraction": repeated_sentence_fraction,
        "longest_identical_sentence_run": longest_identical_sentence_run,
        "self_correction_cue_counts": cue_counts,
        "most_repeated_sentences": most_repeated_sentences,
        "flags": flags,
        "any_pathology_flag": any(flags.values()),
    }


def protocol_run_metrics(results: list[dict[str, Any]], max_new_tokens: int) -> dict[str, Any]:
    lengths = np.asarray([int(row["generated_token_count"]) for row in results], dtype=np.int64)
    latencies = np.asarray([float(row["runtime"]["elapsed_seconds"]) for row in results], dtype=np.float64)
    normal = [row for row in results if bool(row["normal_termination"])]
    completed = [row for row in results if bool(row["complete"])]
    return {
        "max_new_tokens": int(max_new_tokens),
        "total": len(results),
        "normal_termination": len(normal),
        "normal_termination_rate": len(normal) / len(results) if results else 0.0,
        "cap_hit": sum(bool(row["truncated"]) for row in results),
        "cap_hit_rate": sum(bool(row["truncated"]) for row in results) / len(results) if results else 0.0,
        "completed_with_answer": len(completed),
        "correct": sum(row["status"] == "correct" for row in results),
        "wrong": sum(row["status"] == "wrong" for row in results),
        "invalid": sum(row["status"] == "invalid" for row in results),
        "median_generation_length": float(np.median(lengths)) if lengths.size else 0.0,
        "p90_generation_length": float(np.percentile(lengths, 90)) if lengths.size else 0.0,
        "maximum_generation_length": int(lengths.max()) if lengths.size else 0,
        "median_latency_seconds": float(np.median(latencies)) if latencies.size else 0.0,
        "p90_latency_seconds": float(np.percentile(latencies, 90)) if latencies.size else 0.0,
        "peak_gpu_allocated_bytes": max((int(row["runtime"]["peak_gpu_allocated_bytes"]) for row in results), default=0),
        "maximum_artifact_bytes": max((int(row["output_bytes"]) for row in results), default=0),
        "pathology_flagged": sum(bool(row["repetition"]["any_pathology_flag"]) for row in results),
        "per_example": [
            {
                "example_id": row["example_id"],
                "status": row["status"],
                "normal_termination": row["normal_termination"],
                "termination_reason": row["termination_reason"],
                "generated_token_count": row["generated_token_count"],
                "latency_seconds": row["runtime"]["elapsed_seconds"],
                "peak_gpu_allocated_bytes": row["runtime"]["peak_gpu_allocated_bytes"],
                "artifact_bytes": row["output_bytes"],
                "any_pathology_flag": row["repetition"]["any_pathology_flag"],
            }
            for row in results
        ],
    }
