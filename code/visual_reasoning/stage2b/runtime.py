"""Stage 2B teacher-forced and free-rollout runtime helpers."""

from __future__ import annotations

import copy
import re
import time
from typing import Any, Iterable

import torch

from visual_reasoning.stage0.analysis import correctness_status, extract_answer
from visual_reasoning.stage0.modeling import _reset_generation_state, generate_once
from visual_reasoning.stage2b.intervention import ROIAttentionKnockout


def extend_prepared_inputs(prepared: dict[str, Any], suffix_token_ids: Iterable[int]) -> dict[str, Any]:
    extended = {key: value.clone() if isinstance(value, torch.Tensor) else value for key, value in prepared.items()}
    suffix = [int(value) for value in suffix_token_ids]
    if not suffix:
        return extended
    input_ids = extended["input_ids"]
    suffix_tensor = torch.tensor([suffix], dtype=input_ids.dtype, device=input_ids.device)
    extended["input_ids"] = torch.cat((input_ids, suffix_tensor), dim=1)
    for key, fill_value in (("attention_mask", 1), ("mm_token_type_ids", 0)):
        if key not in extended:
            continue
        source = extended[key]
        fill = torch.full((source.shape[0], len(suffix)), fill_value, dtype=source.dtype, device=source.device)
        extended[key] = torch.cat((source, fill), dim=1)
    return extended


def teacher_forced_local_metrics(
    *,
    model: Any,
    prepared: dict[str, Any],
    clean_token_ids: list[int],
    prompt_length: int,
    start_token: int,
    horizon_tokens: int,
    intervention: ROIAttentionKnockout,
    roi_key_indices: list[int] | None,
    intervention_window: tuple[int, int] | None,
    seed: int,
    baseline_log_probs: torch.Tensor | None = None,
) -> tuple[dict[str, Any], torch.Tensor]:
    horizon_end = min(len(clean_token_ids), int(start_token) + int(horizon_tokens))
    if horizon_end <= start_token:
        raise ValueError("Local evaluation horizon is empty")
    target_ids = [int(value) for value in clean_token_ids[start_token:horizon_end]]
    batch = extend_prepared_inputs(prepared, clean_token_ids[:horizon_end])
    logit_rows = torch.arange(
        int(prompt_length) - 1 + int(start_token),
        int(prompt_length) - 1 + int(horizon_end),
        device=batch["input_ids"].device,
        dtype=torch.long,
    )
    target_tensor = torch.tensor(target_ids, device=batch["input_ids"].device, dtype=torch.long)
    intervention.set_condition(roi_key_indices, intervention_window)
    _reset_generation_state(model, seed=seed)
    start_time = time.perf_counter()
    with torch.inference_mode():
        output = model(
            **batch,
            use_cache=False,
            return_dict=True,
            logits_to_keep=logit_rows,
        )
        selected_logits = output.logits[0].float()
        log_probs = torch.log_softmax(selected_logits, dim=-1)
        chosen_log_probs = log_probs.gather(-1, target_tensor[:, None]).squeeze(-1)
        probabilities = log_probs.exp()
        entropy = -(probabilities * log_probs).sum(-1)
        kl_from_baseline = None
        if baseline_log_probs is not None:
            baseline = baseline_log_probs.to(log_probs.device)
            kl_from_baseline = (baseline.exp() * (baseline - log_probs)).sum(-1)
    if torch.cuda.is_available():
        torch.cuda.synchronize()
    elapsed = time.perf_counter() - start_time
    finite = bool(torch.isfinite(chosen_log_probs).all().item() and torch.isfinite(entropy).all().item())
    result = {
        "start_token": int(start_token),
        "horizon_end_token": int(horizon_end),
        "horizon_token_count": len(target_ids),
        "clean_token_ids": target_ids,
        "clean_token_log_probabilities": [float(value) for value in chosen_log_probs.detach().cpu().tolist()],
        "clean_token_nll": [float(value) for value in (-chosen_log_probs).detach().cpu().tolist()],
        "mean_clean_token_nll": float((-chosen_log_probs).mean().item()),
        "sum_clean_token_log_probability": float(chosen_log_probs.sum().item()),
        "mean_predictive_entropy": float(entropy.mean().item()),
        "mean_kl_from_baseline": (
            float(kl_from_baseline.mean().item()) if kl_from_baseline is not None else 0.0
        ),
        "finite": finite,
        "runtime_seconds": elapsed,
        "peak_gpu_allocated_bytes": int(torch.cuda.max_memory_allocated()) if torch.cuda.is_available() else 0,
        "intervention_window": list(intervention_window) if intervention_window is not None else None,
        "roi_key_indices": list(roi_key_indices or []),
        "hook_audit": copy.deepcopy(intervention.audit),
        "distribution_definition": "raw model next-token distribution before sampling processors",
    }
    del output, selected_logits, probabilities, entropy, chosen_log_probs
    return result, log_probs.detach()


def free_rollout(
    *,
    model: Any,
    processor: Any,
    prepared: dict[str, Any],
    clean_token_ids: list[int],
    ground_truth: str,
    start_token: int,
    safety_ceiling: int,
    generation_kwargs: dict[str, Any],
    seed: int,
    eos_token_ids: list[int],
    intervention: ROIAttentionKnockout,
    roi_key_indices: list[int] | None,
    intervention_window: tuple[int, int] | None,
) -> dict[str, Any]:
    if not 0 <= start_token < safety_ceiling:
        raise ValueError("Free-rollout prefix must end before the total safety ceiling")
    prefix_ids = [int(value) for value in clean_token_ids[:start_token]]
    batch = extend_prepared_inputs(prepared, prefix_ids)
    intervention.set_condition(roi_key_indices, intervention_window)
    generation = generate_once(
        model,
        processor,
        batch,
        max_new_tokens=int(safety_ceiling) - int(start_token),
        recorder=None,
        generation_kwargs=generation_kwargs,
        seed=seed,
        collect_predictive_metrics=False,
    )
    continuation_ids = [int(value) for value in generation["generated_token_ids"]]
    full_ids = prefix_ids + continuation_ids
    full_response = processor.tokenizer.decode(
        full_ids,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=False,
    )
    predicted = extract_answer(full_response)
    total_hit_cap = len(full_ids) >= int(safety_ceiling)
    status = "truncated" if total_hit_cap else correctness_status(predicted, ground_truth)
    ended_with_eos = bool(continuation_ids and int(continuation_ids[-1]) in set(eos_token_ids))
    return {
        "clean_prefix_token_count": len(prefix_ids),
        "continuation_generated_token_count": len(continuation_ids),
        "total_reasoning_token_count": len(full_ids),
        "continuation_token_ids": continuation_ids,
        "full_reasoning_token_ids": full_ids,
        "continuation_text": generation["full_generated_response"],
        "full_response": full_response,
        "extracted_final_answer": predicted,
        "ground_truth_answer": str(ground_truth),
        "status": status,
        "correct": status == "correct",
        "truncated": total_hit_cap,
        "normal_termination": not total_hit_cap,
        "ended_with_eos": ended_with_eos,
        "runtime": generation["runtime"],
        "generation_parameters": generation["generation_parameters"],
        "intervention_window": list(intervention_window) if intervention_window is not None else None,
        "roi_key_indices": list(roi_key_indices or []),
        "hook_audit": copy.deepcopy(intervention.audit),
    }


def evidence_number_mentions(text: str, semantic_fact: str) -> dict[str, Any]:
    numbers = re.findall(r"(?<![A-Za-z])\d+(?:\.\d+)?", semantic_fact)
    return {
        "semantic_fact": semantic_fact,
        "numeric_strings": numbers,
        "numeric_strings_mentioned": [value for value in numbers if re.search(rf"(?<!\d){re.escape(value)}(?!\d)", text)],
    }
