"""Qwen3-VL runtime helpers for Stage 3A image-conditioned scoring."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Iterable, Sequence

import torch
from PIL import Image

from visual_reasoning.stage0.attention import visual_grid_metadata
from visual_reasoning.stage0.modeling import _reset_generation_state, generate_once
from visual_reasoning.stage2b.runtime import extend_prepared_inputs


def candidate_logit_rows(prompt_length: int, prefix_length: int, candidate_length: int) -> list[int]:
    if prompt_length <= 0 or prefix_length < 0 or candidate_length <= 0:
        raise ValueError("Invalid prompt, prefix, or candidate length")
    start = int(prompt_length) + int(prefix_length) - 1
    return list(range(start, start + int(candidate_length)))


def summarize_candidate_log_probs(values: Sequence[float]) -> dict[str, Any]:
    if not values:
        raise ValueError("Candidate continuation must contain at least one token")
    floats = [float(value) for value in values]
    return {
        "token_count": len(floats),
        "token_log_probabilities": floats,
        "sum_log_probability": float(sum(floats)),
        "mean_log_probability": float(sum(floats) / len(floats)),
    }


def prepare_custom_image(
    processor: Any,
    row: dict[str, Any],
    image_path: Path,
    device: str,
) -> tuple[dict[str, torch.Tensor], dict[str, Any]]:
    image = Image.open(image_path).convert("RGB")
    question = str(row.get("query_cot") or row.get("question") or "")
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": image},
                {"type": "text", "text": question},
            ],
        }
    ]
    batch = processor.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        return_dict=True,
        return_tensors="pt",
    )
    input_ids = batch["input_ids"][0]
    visual_positions = (input_ids == int(processor.image_token_id)).nonzero().flatten().tolist()
    if not visual_positions or batch["image_grid_thw"].shape[0] != 1:
        raise RuntimeError("Stage 3A expects one image and nonempty visual placeholders")
    grid = [int(value) for value in batch["image_grid_thw"][0].tolist()]
    grid_info = visual_grid_metadata(
        grid,
        merge_size=int(processor.image_processor.merge_size),
        patch_size=int(processor.image_processor.patch_size),
    )
    if len(visual_positions) != int(grid_info["visual_token_count"]):
        raise RuntimeError("Visual placeholder/grid mismatch")
    prepared = {key: value.to(device) if isinstance(value, torch.Tensor) else value for key, value in batch.items()}
    metadata = {
        "prompt_token_count": int(input_ids.numel()),
        "prompt_token_ids": [int(value) for value in input_ids.tolist()],
        "visual_token_indices": visual_positions,
        "image_grid_thw": grid,
        "visual_mapping": grid_info,
        "image_size": [int(image.width), int(image.height)],
        "image_path": str(image_path),
    }
    return prepared, metadata


@torch.inference_mode()
def score_candidate(
    *,
    model: Any,
    prepared: dict[str, Any],
    prefix_token_ids: Iterable[int],
    candidate_token_ids: Sequence[int],
    seed: int,
) -> dict[str, Any]:
    prefix = [int(value) for value in prefix_token_ids]
    candidate = [int(value) for value in candidate_token_ids]
    prompt_length = int(prepared["input_ids"].shape[1])
    rows = candidate_logit_rows(prompt_length, len(prefix), len(candidate))
    batch = extend_prepared_inputs(prepared, [*prefix, *candidate])
    row_tensor = torch.tensor(rows, dtype=torch.long, device=batch["input_ids"].device)
    target = torch.tensor(candidate, dtype=torch.long, device=batch["input_ids"].device)
    _reset_generation_state(model, seed=seed)
    started = time.perf_counter()
    output = model(**batch, use_cache=False, return_dict=True, logits_to_keep=row_tensor)
    log_probs = torch.log_softmax(output.logits[0].float(), dim=-1)
    selected = log_probs.gather(-1, target[:, None]).squeeze(-1)
    if torch.cuda.is_available():
        torch.cuda.synchronize()
    summary = summarize_candidate_log_probs(selected.detach().cpu().tolist())
    summary.update(
        {
            "candidate_token_ids": candidate,
            "logit_rows": rows,
            "runtime_seconds": time.perf_counter() - started,
            "finite": bool(torch.isfinite(selected).all().item()),
            "distribution_definition": "raw model next-token distribution before sampling processors",
        }
    )
    del output, log_probs, selected
    return summary


@torch.inference_mode()
def next_token_logits(
    *,
    model: Any,
    prepared: dict[str, Any],
    prefix_token_ids: Iterable[int],
    seed: int,
) -> torch.Tensor:
    prefix = [int(value) for value in prefix_token_ids]
    prompt_length = int(prepared["input_ids"].shape[1])
    row = prompt_length + len(prefix) - 1
    batch = extend_prepared_inputs(prepared, prefix)
    row_tensor = torch.tensor([row], dtype=torch.long, device=batch["input_ids"].device)
    _reset_generation_state(model, seed=seed)
    output = model(**batch, use_cache=False, return_dict=True, logits_to_keep=row_tensor)
    logits = output.logits[0, 0].detach().float().cpu()
    del output
    return logits


def short_rollout(
    *,
    model: Any,
    processor: Any,
    prepared: dict[str, Any],
    prefix_token_ids: Iterable[int],
    generation_kwargs: dict[str, Any],
    seed: int,
    max_new_tokens: int = 128,
) -> dict[str, Any]:
    prefix = [int(value) for value in prefix_token_ids]
    batch = extend_prepared_inputs(prepared, prefix)
    generation = generate_once(
        model,
        processor,
        batch,
        max_new_tokens=max_new_tokens,
        recorder=None,
        generation_kwargs=generation_kwargs,
        seed=seed,
        collect_predictive_metrics=False,
    )
    return {
        "prefix_token_count": len(prefix),
        "generated_token_ids": generation["generated_token_ids"],
        "generated_token_count": generation["generated_token_count"],
        "continuation_text": generation["full_generated_response"],
        "runtime": generation["runtime"],
        "generation_parameters": generation["generation_parameters"],
    }

