#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import torch

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "code"))

from piqd.data.mathverse_loader import inspect_mathverse, load_smoke_samples
from piqd.fastv.fastv_adapter import FASTV_STATUS, select_active_shift_event, select_top_visual_indices
from piqd.hooks.active_attention_logger import ActiveBankAttentionLogger
from piqd.model.qwen_loader import (
    build_prefill,
    language_model_forward,
    load_processor,
    load_qwen_model,
    move_inputs,
    processor_inputs,
    prune_prefill,
)
from piqd.utils.env import resolve_hf_snapshot
from piqd.utils.io import ensure_dir, write_json, write_jsonl


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mathverse-root", default="/data/dataset/MathVerse")
    parser.add_argument(
        "--model-cache-root",
        default="/home/hyunjin/.cache/huggingface/hub/models--Qwen--Qwen3-VL-8B-Thinking",
    )
    parser.add_argument("--output-dir", default="outputs/piqd/phase1")
    parser.add_argument("--num-samples", type=int, default=10)
    parser.add_argument("--max-new-tokens", type=int, default=64)
    parser.add_argument("--retention-ratio", type=float, default=0.333)
    parser.add_argument("--pruning-layer", type=int, default=2)
    parser.add_argument("--dtype", default="bfloat16", choices=["bfloat16", "bf16", "float16", "fp16"])
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--model-load-only", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = ensure_dir(args.output_dir)
    snapshot = resolve_hf_snapshot(args.model_cache_root)
    samples = load_smoke_samples(args.mathverse_root, limit=args.num_samples)
    config = {
        "phase": "phase1",
        "mathverse_root": args.mathverse_root,
        "model_cache_root": args.model_cache_root,
        "resolved_snapshot": str(snapshot),
        "num_samples_requested": args.num_samples,
        "num_samples_selected": len(samples),
        "max_new_tokens": args.max_new_tokens,
        "retention_ratio": args.retention_ratio,
        "pruning_layer": args.pruning_layer,
        "dtype": args.dtype,
        "device": args.device,
        "fastv_status": FASTV_STATUS,
        "pruning_mode": "delete",
        "decoding": {"do_sample": False, "num_beams": 1},
    }
    write_json(output_dir / "phase1_config.json", config)
    write_jsonl(output_dir / "phase1_samples.jsonl", [sample.to_json() for sample in samples])

    processor = load_processor(snapshot)
    model, dtype = load_qwen_model(snapshot, dtype_name=args.dtype, device=args.device)
    model_info = {
        "model_class": type(model).__name__,
        "processor_class": type(processor).__name__,
        "dtype": str(dtype),
        "device": str(next(model.parameters()).device),
        "attn_implementation": getattr(model.config, "_attn_implementation", "unknown"),
        "snapshot": str(snapshot),
    }
    if torch.cuda.is_available():
        model_info["gpu_name"] = torch.cuda.get_device_name(0)
        model_info["gpu_memory_allocated_bytes"] = torch.cuda.memory_allocated(0)
        model_info["gpu_memory_reserved_bytes"] = torch.cuda.memory_reserved(0)
    write_model_loading(output_dir / "phase1_model_loading.md", model_info, args.model_load_only)
    if args.model_load_only:
        write_jsonl(output_dir / "phase1_generation_logs.jsonl", [])
        write_jsonl(output_dir / "phase1_event_logs.jsonl", [])
        write_fastv_status(output_dir / "phase1_fastv_status.md", config, model_info, model_load_only=True)
        return

    generation_rows: list[dict[str, Any]] = []
    event_rows: list[dict[str, Any]] = []
    for sample in samples:
        try:
            generation, event = run_sample(model, processor, sample, args)
        except torch.cuda.OutOfMemoryError:
            raise
        except Exception as exc:
            generation = {
                "sample_id": sample.sample_id,
                "status": "failed",
                "error": repr(exc),
            }
            event = {
                "sample_id": sample.sample_id,
                "status": "failed",
                "error": repr(exc),
            }
        generation_rows.append(generation)
        event_rows.append(event)
        write_jsonl(output_dir / "phase1_generation_logs.jsonl", generation_rows)
        write_jsonl(output_dir / "phase1_event_logs.jsonl", event_rows)

    write_fastv_status(output_dir / "phase1_fastv_status.md", config, model_info, model_load_only=False)
    write_summary(output_dir / "phase1_summary.md", generation_rows, event_rows, config, model_info)


def run_sample(model: Any, processor: Any, sample: Any, args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any]]:
    device = next(model.parameters()).device
    raw_inputs = processor_inputs(processor, sample.image_path, sample.prompt)
    inputs = move_inputs(raw_inputs, device)
    full_prefill = build_prefill(model, inputs)
    if full_prefill.num_visual_tokens <= 0:
        raise ValueError("sample produced no visual tokens")

    score_logger = ActiveBankAttentionLogger(
        layer_idx=args.pruning_layer,
        visual_positions=full_prefill.visual_positions,
        active_visual_indices=list(range(full_prefill.num_visual_tokens)),
    )
    score_logger.attach(model)
    with torch.no_grad():
        _ = language_model_forward(model, full_prefill)
    score_logger.detach()
    if score_logger.latest_visual_scores is None:
        raise RuntimeError("failed to capture visual scores for FastV selection")

    retained_indices = select_top_visual_indices(score_logger.latest_visual_scores.tolist(), args.retention_ratio)
    pruned_prefill = prune_prefill(full_prefill, retained_indices)
    active_logger = ActiveBankAttentionLogger(
        layer_idx=args.pruning_layer,
        visual_positions=pruned_prefill.visual_positions,
        active_visual_indices=retained_indices,
    )

    generated_ids, ended_normally = greedy_generate(model, pruned_prefill, active_logger, args.max_new_tokens)
    generated_text = processor.tokenizer.decode(generated_ids, skip_special_tokens=True)
    similarities = [row["risd_similarity_active"] for row in active_logger.generated_records()]
    event_selection = select_active_shift_event(similarities)
    event_prefix = ""
    if event_selection.event_step is not None and generated_ids:
        event_prefix = processor.tokenizer.decode(generated_ids[: event_selection.event_step + 1], skip_special_tokens=True)

    generation = {
        "sample_id": sample.sample_id,
        "status": "ok",
        "generated_prefix_token_ids": generated_ids,
        "generated_text": generated_text,
        "decoding_config": {"do_sample": False, "num_beams": 1, "max_new_tokens": args.max_new_tokens},
        "fastv_status": FASTV_STATUS,
        "pruning_mode": "delete",
        "retention_ratio": args.retention_ratio,
        "rounding_rule": "round(num_visual_tokens * retention_ratio), clamped to [1, num_visual_tokens]",
        "num_visual_tokens_full": full_prefill.num_visual_tokens,
        "num_visual_tokens_retained": len(retained_indices),
        "active_visual_token_indices": retained_indices,
        "active_bank_similarity_curve": active_logger.generated_records(),
        "event_name": event_selection.event_name,
        "event_token_index": event_selection.event_step,
        "event_text_prefix": event_prefix,
        "ended_normally": ended_normally,
        "truncated": not ended_normally and len(generated_ids) >= args.max_new_tokens,
    }
    event = {
        "sample_id": sample.sample_id,
        "status": "ok",
        "event_name": event_selection.event_name,
        "event_token_index": event_selection.event_step,
        "event_similarity": event_selection.similarity,
        "fallback_used": event_selection.fallback_used,
        "similarity_curve": active_logger.generated_records(),
        "definition": "active-bank qK similarity over retained FastV visual tokens only; not full-bank RVIS",
    }
    return generation, event


def greedy_generate(model: Any, prefill: Any, logger: ActiveBankAttentionLogger, max_new_tokens: int) -> tuple[list[int], bool]:
    logger.attach(model)
    generated: list[int] = []
    ended_normally = False
    eos = model.generation_config.eos_token_id
    eos_ids = set(eos if isinstance(eos, list) else [eos]) if eos is not None else set()
    try:
        with torch.no_grad():
            logger.set_current_token(None)
            outputs = language_model_forward(model, prefill)
            logits = model.lm_head(outputs.last_hidden_state[:, -1:, :])
            past_key_values = outputs.past_key_values
            next_token = int(torch.argmax(logits[:, -1, :], dim=-1).item())
            for _ in range(max_new_tokens):
                generated.append(next_token)
                if next_token in eos_ids:
                    ended_normally = True
                    break
                token_tensor = torch.tensor([[next_token]], dtype=torch.long, device=prefill.inputs_embeds.device)
                token_embeds = model.model.get_input_embeddings()(token_tensor)
                past_len = past_key_values.get_seq_length() if past_key_values is not None else prefill.seq_len
                attention_mask = torch.ones((1, past_len + 1), dtype=torch.long, device=prefill.inputs_embeds.device)
                logger.set_current_token(next_token)
                outputs = model.model.language_model(
                    input_ids=None,
                    inputs_embeds=token_embeds,
                    attention_mask=attention_mask,
                    past_key_values=past_key_values,
                    use_cache=True,
                    return_dict=True,
                )
                logits = model.lm_head(outputs.last_hidden_state[:, -1:, :])
                past_key_values = outputs.past_key_values
                next_token = int(torch.argmax(logits[:, -1, :], dim=-1).item())
    finally:
        logger.detach()
    return generated, ended_normally


def write_model_loading(path: Path, info: dict[str, Any], model_load_only: bool) -> None:
    lines = [
        "# Phase 1 Model Loading",
        "",
        f"- model_class: `{info['model_class']}`",
        f"- processor_class: `{info['processor_class']}`",
        f"- dtype: `{info['dtype']}`",
        f"- device: `{info['device']}`",
        f"- attn_implementation: `{info['attn_implementation']}`",
        f"- snapshot: `{info['snapshot']}`",
        f"- local_files_only: `true`",
        f"- model_load_only: `{str(model_load_only).lower()}`",
    ]
    if "gpu_name" in info:
        lines.extend([
            f"- gpu_name: `{info['gpu_name']}`",
            f"- gpu_memory_allocated_bytes: `{info['gpu_memory_allocated_bytes']}`",
            f"- gpu_memory_reserved_bytes: `{info['gpu_memory_reserved_bytes']}`",
        ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_fastv_status(path: Path, config: dict[str, Any], model_info: dict[str, Any], model_load_only: bool) -> None:
    lines = [
        "# Phase 1 FastV Status",
        "",
        f"- fastv_status: `{config['fastv_status']}`",
        "- reason: Qwen3-VL is not directly supported by the FastV reference modified LLaMA forward; Phase 1 uses static attention top-k visual token deletion for smoke hook validation.",
        f"- retention_ratio: `{config['retention_ratio']}`",
        f"- pruning_layer: `{config['pruning_layer']}`",
        "- rounding_rule: `round(num_visual_tokens * retention_ratio)`, clamped to at least 1 token.",
        "- pruning_mode: `delete`",
        "- dynamic_token_swapping: `false`",
        "- dstp: `false`",
        f"- model_load_only: `{str(model_load_only).lower()}`",
        f"- model_class: `{model_info['model_class']}`",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_summary(path: Path, generation_rows: list[dict[str, Any]], event_rows: list[dict[str, Any]], config: dict[str, Any], model_info: dict[str, Any]) -> None:
    ok = [row for row in generation_rows if row.get("status") == "ok"]
    first_shift = [row for row in event_rows if row.get("event_name") == "first_active_attention_shift"]
    fallback = [row for row in event_rows if row.get("fallback_used")]
    lines = [
        "# Phase 1 Summary",
        "",
        f"- model_loading_works: `{bool(model_info)}`",
        f"- mathverse_loader_works: `{config['num_samples_selected'] > 0}`",
        f"- fastv_status: `{config['fastv_status']}`",
        f"- active_bank_similarity_logging_works: `{any(row.get('similarity_curve') for row in event_rows)}`",
        f"- samples_selected: `{config['num_samples_selected']}`",
        f"- samples_processed_ok: `{len(ok)}`",
        f"- first_active_attention_shift_count: `{len(first_shift)}`",
        f"- fallback_event_count: `{len(fallback)}`",
        "- phase2_safe_to_start: `false`",
        "",
        "Phase 2 should wait until the user explicitly approves and until this smoke output is reviewed.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

