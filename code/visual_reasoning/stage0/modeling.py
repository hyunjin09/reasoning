"""Qwen3-VL loading, deterministic generation, and token-level logging."""

from __future__ import annotations

import codecs
import platform
import resource
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch
import transformers
from PIL import Image
from transformers import AutoProcessor, LogitsProcessor, Qwen3VLForConditionalGeneration
from transformers.convert_slow_tokenizer import bytes_to_unicode

from .analysis import (
    aggregate_span_signals,
    build_reasoning_spans,
    correctness_status,
    extract_answer,
    extract_reasoning,
    predictive_metrics,
)
from .attention import OnlineAttentionRecorder, visual_grid_metadata
from .data import resolve_image_path


ATTENTION_IMPLEMENTATIONS = {"vision_config": "sdpa", "text_config": "eager"}


def load_runtime(model_checkpoint: Path, device: str) -> tuple[Any, Any]:
    processor = AutoProcessor.from_pretrained(model_checkpoint, local_files_only=True)
    dtype = torch.bfloat16 if device.startswith("cuda") else torch.float32
    model = Qwen3VLForConditionalGeneration.from_pretrained(
        model_checkpoint,
        dtype=dtype,
        attn_implementation=ATTENTION_IMPLEMENTATIONS,
        local_files_only=True,
        low_cpu_mem_usage=True,
    )
    model.to(device)
    model.eval()
    return processor, model


def runtime_environment(model_checkpoint: Path, model: Any, max_new_tokens: int) -> dict[str, Any]:
    cuda_available = torch.cuda.is_available()
    gpu_name = torch.cuda.get_device_name(0) if cuda_available else "none"
    gpu_memory = torch.cuda.get_device_properties(0).total_memory if cuda_available else 0
    return {
        "model_checkpoint_requested": str(model_checkpoint),
        "model_checkpoint_resolved": str(model_checkpoint.resolve()),
        "python_environment": str(Path(sys.executable).resolve()),
        "python_version": platform.python_version(),
        "torch_version": torch.__version__,
        "transformers_version": transformers.__version__,
        "cuda_available": cuda_available,
        "torch_cuda_version": torch.version.cuda,
        "gpu_name": gpu_name,
        "gpu_total_memory_bytes": int(gpu_memory),
        "max_new_tokens": int(max_new_tokens),
        "architecture": model.__class__.__name__,
        "parameter_count": sum(parameter.numel() for parameter in model.parameters()),
        "language_layers": int(model.config.text_config.num_hidden_layers),
        "attention_heads": int(model.config.text_config.num_attention_heads),
        "kv_heads": int(model.config.text_config.num_key_value_heads),
        "head_dimension": int(model.config.text_config.head_dim),
        "image_token_id": int(model.config.image_token_id),
        "vision_patch_size": int(model.config.vision_config.patch_size),
        "vision_merge_size": int(model.config.vision_config.spatial_merge_size),
        "language_attention_implementation": str(model.config.text_config._attn_implementation),
        "vision_attention_implementation": str(model.config.vision_config._attn_implementation),
    }


def prepare_example(
    processor: Any,
    row: dict[str, Any],
    dataset_root: Path,
    device: str,
) -> tuple[dict[str, torch.Tensor], dict[str, Any], Path]:
    image_path = resolve_image_path(dataset_root, str(row["image"]))
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
    if not visual_positions:
        raise RuntimeError(f"No visual placeholders found for sample {row['sample_index']}")
    if batch["image_grid_thw"].shape[0] != 1:
        raise RuntimeError("Stage 0 currently expects exactly one image per MathVerse example")

    grid = [int(value) for value in batch["image_grid_thw"][0].tolist()]
    grid_info = visual_grid_metadata(
        grid,
        merge_size=int(processor.image_processor.merge_size),
        patch_size=int(processor.image_processor.patch_size),
    )
    if len(visual_positions) != int(grid_info["visual_token_count"]):
        raise RuntimeError(
            f"Visual placeholder count {len(visual_positions)} does not match grid-derived count "
            f"{grid_info['visual_token_count']}"
        )

    prepared = {key: value.to(device) if isinstance(value, torch.Tensor) else value for key, value in batch.items()}
    input_record = {
        "example_id": str(row["sample_index"]),
        "sample_index": str(row["sample_index"]),
        "problem_index": str(row["problem_index"]),
        "mathverse_variant": str(row["problem_version"]),
        "question": str(row.get("question", "")),
        "generation_query": question,
        "ground_truth_answer": str(row.get("answer", "")),
        "image_reference": str(row["image"]),
        "resolved_image_path": str(image_path),
        "original_image_size": [int(image.width), int(image.height)],
        "metadata": row.get("metadata") or {},
        "question_type": row.get("question_type"),
        "prompt_token_count": int(input_ids.numel()),
        "visual_token_indices": visual_positions,
        "prompt_nonvisual_token_indices": [
            index for index in range(int(input_ids.numel())) if index not in set(visual_positions)
        ],
        "visual_mapping": grid_info,
        "image_grid_thw": grid,
        "preprocessing": {
            "processor_class": processor.__class__.__name__,
            "image_processor_class": processor.image_processor.__class__.__name__,
            "patch_size": int(processor.image_processor.patch_size),
            "temporal_patch_size": int(processor.image_processor.temporal_patch_size),
            "merge_size": int(processor.image_processor.merge_size),
            "resized_image_size": grid_info["resized_image_size"],
        },
    }
    return prepared, input_record, image_path


def _clone_inputs(inputs: dict[str, Any]) -> dict[str, Any]:
    return {key: value.clone() if isinstance(value, torch.Tensor) else value for key, value in inputs.items()}


def _reset_generation_state(model: Any, seed: int = 0) -> None:
    if hasattr(model.model, "rope_deltas"):
        model.model.rope_deltas = None
    torch.manual_seed(int(seed))
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(int(seed))
        torch.cuda.reset_peak_memory_stats()


class OnlineGenerationScoreRecorder(LogitsProcessor):
    """Record processed next-token uncertainty without retaining all logits."""

    def __init__(self) -> None:
        self.rows: list[dict[str, float]] = []
        self._pending_log_probs: torch.Tensor | None = None
        self._pending_summary: dict[str, float] | None = None

    @torch.no_grad()
    def __call__(self, _input_ids: torch.LongTensor, scores: torch.FloatTensor) -> torch.FloatTensor:
        if scores.ndim != 2 or scores.shape[0] != 1:
            raise ValueError(f"Expected single-example scores [1,vocab], got {tuple(scores.shape)}")
        if self._pending_log_probs is not None:
            raise RuntimeError("Previous generation score was not paired with a streamed token")
        values = scores.detach().float()
        log_probs = torch.log_softmax(values, dim=-1)
        probabilities = torch.softmax(values, dim=-1)
        finite_terms = torch.where(
            probabilities > 0,
            probabilities * log_probs,
            torch.zeros_like(probabilities),
        )
        top_values, _ = torch.topk(probabilities, k=min(2, probabilities.shape[-1]), dim=-1)
        top1 = float(top_values[0, 0].item())
        top2 = float(top_values[0, 1].item()) if top_values.shape[-1] > 1 else 0.0
        self._pending_log_probs = log_probs[0]
        self._pending_summary = {
            "next_token_entropy": float((-finite_terms.sum()).item()),
            "top1_probability": top1,
            "top2_probability": top2,
            "top1_top2_margin": top1 - top2,
        }
        return scores

    @torch.no_grad()
    def put(self, value: torch.Tensor) -> None:
        # Transformers streams the full prompt before the first score exists.
        if self._pending_log_probs is None:
            return
        flattened = value.reshape(-1)
        if flattened.numel() != 1 or self._pending_summary is None:
            raise ValueError("Stage 1 score streaming requires batch size one")
        token_id = int(flattened[0].item())
        self.rows.append(
            {
                "token_log_probability": float(self._pending_log_probs[token_id].item()),
                **self._pending_summary,
            }
        )
        self._pending_log_probs = None
        self._pending_summary = None

    def end(self) -> None:
        if self._pending_log_probs is not None:
            raise RuntimeError("Generation ended with an unconsumed predictive-score row")


def _incremental_decode_pieces_reference(tokenizer: Any, token_ids: list[int]) -> tuple[list[str], str, bool]:
    """Reference implementation retained for regression checks and non-ByteLevel tokenizers."""
    full = tokenizer.decode(token_ids, skip_special_tokens=False, clean_up_tokenization_spaces=False)
    boundaries = [0]
    for end in range(1, len(token_ids) + 1):
        prefix = tokenizer.decode(token_ids[:end], skip_special_tokens=False, clean_up_tokenization_spaces=False)
        common = 0
        for left, right in zip(prefix, full):
            if left != right:
                break
            common += 1
        boundaries.append(max(boundaries[-1], common))
    if boundaries:
        boundaries[-1] = len(full)
    pieces = [full[start:end] for start, end in zip(boundaries, boundaries[1:])]
    aligned = len(pieces) == len(token_ids) and "".join(pieces) == full
    return pieces, full, aligned


def _incremental_decode_pieces(tokenizer: Any, token_ids: list[int]) -> tuple[list[str], str, bool]:
    """Decode Qwen ByteLevel token pieces in linear time without changing boundaries."""
    backend = getattr(tokenizer, "backend_tokenizer", None)
    decoder = getattr(backend, "decoder", None)
    if decoder is None or decoder.__class__.__name__ != "ByteLevel":
        return _incremental_decode_pieces_reference(tokenizer, token_ids)

    try:
        inverse_byte_map = {character: byte for byte, character in bytes_to_unicode().items()}
        tokens = tokenizer.convert_ids_to_tokens(token_ids, skip_special_tokens=False)
        utf8_decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
        pieces = [
            utf8_decoder.decode(bytes(inverse_byte_map[character] for character in token), final=False)
            for token in tokens
        ]
        tail = utf8_decoder.decode(b"", final=True)
        if tail:
            if pieces:
                pieces[-1] += tail
            else:
                return _incremental_decode_pieces_reference(tokenizer, token_ids)
        full = tokenizer.decode(token_ids, skip_special_tokens=False, clean_up_tokenization_spaces=False)
        aligned = len(pieces) == len(token_ids) and "".join(pieces) == full
        if aligned:
            return pieces, full, True
    except (KeyError, TypeError, UnicodeError):
        pass
    return _incremental_decode_pieces_reference(tokenizer, token_ids)


def generate_once(
    model: Any,
    processor: Any,
    prepared_inputs: dict[str, Any],
    max_new_tokens: int,
    recorder: OnlineAttentionRecorder | None,
    generation_kwargs: dict[str, Any] | None = None,
    seed: int = 0,
    collect_predictive_metrics: bool = True,
    memory_safe_scores: bool = False,
) -> dict[str, Any]:
    _reset_generation_state(model, seed=seed)
    prompt_length = int(prepared_inputs["input_ids"].shape[1])
    generation_kwargs = dict(generation_kwargs or {"do_sample": False})
    score_recorder = OnlineGenerationScoreRecorder() if collect_predictive_metrics and memory_safe_scores else None
    generate_kwargs: dict[str, Any] = {
        **generation_kwargs,
        "max_new_tokens": int(max_new_tokens),
        "use_cache": True,
        "return_dict_in_generate": True,
        "output_scores": bool(collect_predictive_metrics and not memory_safe_scores),
    }
    if score_recorder is not None:
        generate_kwargs.update({"logits_processor": [score_recorder], "streamer": score_recorder})
    start = time.perf_counter()
    with torch.inference_mode():
        generated = model.generate(
            **_clone_inputs(prepared_inputs),
            **generate_kwargs,
        )
    elapsed = time.perf_counter() - start
    generated_ids = [int(value) for value in generated.sequences[0, prompt_length:].tolist()]
    scores = list(generated.scores) if generated.scores is not None else []
    if collect_predictive_metrics:
        recorded_count = len(score_recorder.rows) if score_recorder is not None else len(scores)
        if recorded_count != len(generated_ids):
            raise RuntimeError(f"Generation scores {recorded_count} do not align with generated IDs {len(generated_ids)}")

    pieces, raw_decoded, incremental_alignment = _incremental_decode_pieces(processor.tokenizer, generated_ids)
    response = processor.tokenizer.decode(
        generated_ids,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=False,
    )
    token_rows: list[dict[str, Any]] = []
    attention_arrays = recorder.as_arrays() if recorder is not None else None
    if attention_arrays is not None and attention_arrays["modality_by_layer"].shape[0] != len(generated_ids):
        raise RuntimeError("Attention steps do not align with generated tokens")

    for index, (token_id, piece) in enumerate(zip(generated_ids, pieces)):
        row: dict[str, Any] = {
            "token_index": index,
            "token_id": token_id,
            "decoded_token": piece,
            "generation_position": prompt_length + index,
        }
        if collect_predictive_metrics:
            row.update(
                score_recorder.rows[index]
                if score_recorder is not None
                else predictive_metrics(scores[index][0], token_id)
            )
        if attention_arrays is not None:
            modality = attention_arrays["modality_by_layer"][index].mean(axis=0)
            row.update(
                {
                    "visual_attention_mass": float(modality[0]),
                    "prompt_attention_mass": float(modality[1]),
                    "reasoning_attention_mass": float(modality[2]),
                }
            )
        token_rows.append(row)

    peak_gpu_allocated = int(torch.cuda.max_memory_allocated()) if torch.cuda.is_available() else 0
    peak_gpu_reserved = int(torch.cuda.max_memory_reserved()) if torch.cuda.is_available() else 0
    peak_cpu_rss_kb = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    del generated
    del scores
    return {
        "generated_token_ids": generated_ids,
        "generated_token_count": len(generated_ids),
        "full_generated_response": response,
        "raw_decoded_response": raw_decoded,
        "incremental_decode_alignment": incremental_alignment,
        "token_rows": token_rows,
        "attention_arrays": attention_arrays,
        "generation_parameters": {**generation_kwargs, "max_new_tokens": int(max_new_tokens), "seed": int(seed)},
        "predictive_score_definition": (
            "processed next-token distribution after configured Transformers logits processors"
            if collect_predictive_metrics
            else "not collected for protocol-only comparison"
        ),
        "runtime": {
            "elapsed_seconds": elapsed,
            "peak_gpu_allocated_bytes": peak_gpu_allocated,
            "peak_gpu_reserved_bytes": peak_gpu_reserved,
            "peak_cpu_rss_kb": peak_cpu_rss_kb,
        },
    }


def analyze_instrumented_generation(
    generation: dict[str, Any],
    ground_truth: str,
    max_new_tokens: int,
    eos_token_ids: list[int],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    token_rows = generation["token_rows"]
    response = generation["full_generated_response"]
    predicted = extract_answer(response)
    generated_ids = generation["generated_token_ids"]
    truncated = len(generated_ids) >= max_new_tokens and (not generated_ids or generated_ids[-1] not in eos_token_ids)
    status = "truncated" if truncated else correctness_status(predicted, ground_truth)
    spans = build_reasoning_spans(token_rows)
    aggregate_span_signals(
        spans,
        token_rows,
        signal_names=(
            "visual_attention_mass",
            "prompt_attention_mass",
            "reasoning_attention_mass",
            "next_token_entropy",
            "top1_probability",
            "top1_top2_margin",
        ),
    )
    arrays = generation["attention_arrays"]
    if arrays is not None:
        for span in spans:
            start, end = int(span["start_token"]), int(span["end_token"])
            span["visual_focus"] = arrays["visual_focus"][start:end].mean(axis=0).astype(float).tolist()

    visual_values = np.asarray([float(row["visual_attention_mass"]) for row in token_rows], dtype=np.float32)
    entropy_values = np.asarray([float(row["next_token_entropy"]) for row in token_rows], dtype=np.float32)
    quarter = max(1, len(visual_values) // 4)
    correlation = None
    if len(visual_values) > 2 and float(visual_values.std()) > 0 and float(entropy_values.std()) > 0:
        correlation = float(np.corrcoef(visual_values, entropy_values)[0, 1])
    threshold = float(visual_values.mean() + visual_values.std()) if len(visual_values) else float("inf")
    peak_count = 0
    for index in range(1, max(1, len(visual_values) - 1)):
        if index >= len(visual_values) - 1:
            break
        if visual_values[index] > threshold and visual_values[index] >= visual_values[index - 1] and visual_values[index] >= visual_values[index + 1]:
            peak_count += 1

    summary = {
        "full_generated_response": response,
        "extracted_reasoning": extract_reasoning(response),
        "extracted_final_answer": predicted,
        "ground_truth_answer": ground_truth,
        "status": status,
        "correct": status == "correct",
        "truncated": truncated,
        "generated_token_count": len(generated_ids),
        "generated_token_ids": generated_ids,
        "runtime": generation["runtime"],
        "alignment": {
            "incremental_decode_alignment": bool(generation["incremental_decode_alignment"]),
            "token_score_alignment": len(token_rows) == len(generated_ids),
            "attention_token_alignment": arrays is not None and arrays["modality_by_layer"].shape[0] == len(generated_ids),
            "span_ranges_valid": all(0 <= int(span["start_token"]) < int(span["end_token"]) <= len(token_rows) for span in spans),
        },
        "descriptive_statistics": {
            "mean_visual_attention": float(visual_values.mean()) if len(visual_values) else 0.0,
            "early_quartile_visual_attention": float(visual_values[:quarter].mean()) if len(visual_values) else 0.0,
            "late_quartile_visual_attention": float(visual_values[-quarter:].mean()) if len(visual_values) else 0.0,
            "visual_entropy_correlation": correlation,
            "visual_peak_count": peak_count,
        },
    }
    return summary, spans


def attention_modules(model: Any) -> list[torch.nn.Module]:
    return [layer.self_attn for layer in model.model.language_model.layers]
