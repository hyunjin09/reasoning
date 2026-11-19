"""Qwen3-VL prefill-cache and cutoff scoring helpers for Stage 3B.0."""

from __future__ import annotations

import copy
import time
from typing import Any, Sequence

import torch

from visual_reasoning.stage0.modeling import _reset_generation_state, attention_modules
from visual_reasoning.stage3a.runtime import summarize_candidate_log_probs
from visual_reasoning.stage3b0.cache import clone_cache
from visual_reasoning.stage3b0.intervention import GenerationStartVisualCutoff


def _seed_without_clearing_rope(seed: int) -> None:
    torch.manual_seed(int(seed))
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(int(seed))
        torch.cuda.reset_peak_memory_stats()


def suffix_position_ids(
    *, prompt_length: int, suffix_length: int, rope_deltas: torch.Tensor, device: torch.device
) -> torch.Tensor:
    """Construct Qwen3-VL's cached 4-axis positions for an unpadded suffix."""

    if prompt_length <= 0 or suffix_length <= 0:
        raise ValueError("Prompt and suffix lengths must be positive")
    delta = rope_deltas.to(device=device, dtype=torch.long)
    if delta.shape != (1, 1):
        raise ValueError(f"Stage 3B.0 expects one-example rope_deltas [1,1], got {tuple(delta.shape)}")
    text = torch.arange(
        int(prompt_length), int(prompt_length) + int(suffix_length), dtype=torch.long, device=device
    ).view(1, -1)
    vision = text.unsqueeze(0).expand(3, -1, -1) + delta.view(1, 1, 1)
    return torch.cat((text.unsqueeze(0), vision), dim=0)


@torch.inference_mode()
def prefill_condition(
    *, model: Any, prepared: dict[str, Any], seed: int
) -> tuple[Any, torch.Tensor, dict[str, Any]]:
    """Run normal multimodal prefill and retain the post-RoPE language K/V cache."""

    _reset_generation_state(model, seed=seed)
    started = time.perf_counter()
    output = model(**prepared, use_cache=True, return_dict=True, logits_to_keep=1)
    if output.past_key_values is None or output.rope_deltas is None:
        raise RuntimeError("Qwen prefill did not return cache and rope_deltas")
    if torch.cuda.is_available():
        torch.cuda.synchronize()
    runtime = time.perf_counter() - started
    cache = output.past_key_values
    rope = output.rope_deltas.detach().clone()
    audit = {
        "prompt_length": int(prepared["input_ids"].shape[1]),
        "cache_sequence_length": int(cache.get_seq_length()),
        "rope_deltas": rope.detach().cpu().tolist(),
        "runtime_seconds": runtime,
        "peak_gpu_allocated_bytes": int(torch.cuda.max_memory_allocated()) if torch.cuda.is_available() else 0,
    }
    del output
    return cache, rope, audit


@torch.inference_mode()
def score_candidate_from_cache(
    *,
    model: Any,
    prefill_cache: Any,
    rope_deltas: torch.Tensor,
    prompt_length: int,
    visual_token_indices: Sequence[int],
    prefix_token_ids: Sequence[int],
    candidate_token_ids: Sequence[int],
    seed: int,
    cutoff_enabled: bool = True,
) -> dict[str, Any]:
    """Score one candidate after a normal or patched prefill cache."""

    prefix = [int(value) for value in prefix_token_ids]
    candidate = [int(value) for value in candidate_token_ids]
    if not prefix:
        raise ValueError("Stage 3B.0 strict pre-E0 probe requires at least one generated prefix token")
    if not candidate:
        raise ValueError("Candidate continuation must be nonempty")
    suffix = [*prefix, *candidate]
    device = prefill_cache.layers[0].keys.device
    input_ids = torch.tensor([suffix], dtype=torch.long, device=device)
    attention_mask = torch.ones((1, int(prompt_length) + len(suffix)), dtype=torch.long, device=device)
    positions = suffix_position_ids(
        prompt_length=int(prompt_length),
        suffix_length=len(suffix),
        rope_deltas=rope_deltas,
        device=device,
    )
    candidate_rows = torch.arange(
        len(prefix) - 1,
        len(prefix) - 1 + len(candidate),
        dtype=torch.long,
        device=device,
    )
    targets = torch.tensor(candidate, dtype=torch.long, device=device)
    working_cache = clone_cache(prefill_cache)
    model.model.rope_deltas = rope_deltas.detach().clone().to(device)
    _seed_without_clearing_rope(seed)
    cutoff = GenerationStartVisualCutoff(
        prompt_length=int(prompt_length),
        visual_key_indices=visual_token_indices,
        num_attention_heads=int(model.config.text_config.num_attention_heads),
        enabled=cutoff_enabled,
    ).attach(attention_modules(model))
    started = time.perf_counter()
    try:
        output = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            position_ids=positions,
            past_key_values=working_cache,
            use_cache=True,
            return_dict=True,
            logits_to_keep=candidate_rows,
        )
    finally:
        cutoff.close()
    log_probs = torch.log_softmax(output.logits[0].float(), dim=-1)
    selected = log_probs.gather(-1, targets[:, None]).squeeze(-1)
    if torch.cuda.is_available():
        torch.cuda.synchronize()
    summary = summarize_candidate_log_probs(selected.detach().cpu().tolist())
    summary.update(
        {
            "candidate_token_ids": candidate,
            "local_logit_rows": [int(value) for value in candidate_rows.detach().cpu().tolist()],
            "absolute_logit_rows": [
                int(prompt_length) + int(value) for value in candidate_rows.detach().cpu().tolist()
            ],
            "runtime_seconds": time.perf_counter() - started,
            "peak_gpu_allocated_bytes": int(torch.cuda.max_memory_allocated()) if torch.cuda.is_available() else 0,
            "finite": bool(torch.isfinite(selected).all().item()),
            "cutoff_enabled": bool(cutoff_enabled),
            "cutoff_audit": copy.deepcopy(cutoff.audit),
            "distribution_definition": "raw model next-token distribution before sampling processors",
        }
    )
    del output, log_probs, selected, working_cache
    return summary


def score_preference_from_cache(
    *,
    model: Any,
    prefill_cache: Any,
    rope_deltas: torch.Tensor,
    prompt_length: int,
    visual_token_indices: Sequence[int],
    prefix_token_ids: Sequence[int],
    candidate_original_ids: Sequence[int],
    candidate_counterfactual_ids: Sequence[int],
    seed: int,
    cutoff_enabled: bool = True,
) -> dict[str, Any]:
    original = score_candidate_from_cache(
        model=model,
        prefill_cache=prefill_cache,
        rope_deltas=rope_deltas,
        prompt_length=prompt_length,
        visual_token_indices=visual_token_indices,
        prefix_token_ids=prefix_token_ids,
        candidate_token_ids=candidate_original_ids,
        seed=seed,
        cutoff_enabled=cutoff_enabled,
    )
    counterfactual = score_candidate_from_cache(
        model=model,
        prefill_cache=prefill_cache,
        rope_deltas=rope_deltas,
        prompt_length=prompt_length,
        visual_token_indices=visual_token_indices,
        prefix_token_ids=prefix_token_ids,
        candidate_token_ids=candidate_counterfactual_ids,
        seed=seed,
        cutoff_enabled=cutoff_enabled,
    )
    return {
        "original_candidate": original,
        "counterfactual_candidate": counterfactual,
        "L_o": float(original["mean_log_probability"]),
        "L_c": float(counterfactual["mean_log_probability"]),
        "D": float(original["mean_log_probability"] - counterfactual["mean_log_probability"]),
    }
