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

from piqd.hooks.query_key_capture import QueryKeyCaptureHook, stack_queries, stack_visual_keys
from piqd.model.qwen_loader import (
    build_prefill,
    language_model_forward,
    load_processor,
    load_qwen_model,
    move_inputs,
    processor_inputs,
)
from piqd.phase2.artifacts import Phase2ArtifactRow, load_phase1_artifacts
from piqd.phase2.replay import (
    append_generated_tokens,
    build_condition_replay_from_prefill,
    decoded_context,
    event_key,
    hash_token_ids,
)
from piqd.utils.env import resolve_hf_snapshot
from piqd.utils.io import ensure_dir, write_json, write_jsonl


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase1-dir", default="outputs/piqd/phase1")
    parser.add_argument("--output-dir", default="outputs/piqd/phase2")
    parser.add_argument(
        "--model-cache-root",
        default="/home/hyunjin/.cache/huggingface/hub/models--Qwen--Qwen3-VL-8B-Thinking",
    )
    parser.add_argument("--num-samples", type=int, default=10)
    parser.add_argument("--dtype", default="bfloat16", choices=["bfloat16", "bf16", "float16", "fp16"])
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--pruning-layer", type=int, default=2)
    parser.add_argument("--selected-layers", default="")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = ensure_dir(args.output_dir)
    rows, blockers = load_phase1_artifacts(args.phase1_dir)
    if blockers:
        write_blockers(output_dir / "phase2_blockers.md", blockers)
        write_summary(output_dir / "phase2_summary.md", status="blocked", blockers=blockers)
        return
    rows = rows[: args.num_samples]
    snapshot = resolve_hf_snapshot(args.model_cache_root)

    processor = load_processor(snapshot)
    model, dtype = load_qwen_model(snapshot, dtype_name=args.dtype, device=args.device)
    selected_layers = resolve_selected_layers(model, args.pruning_layer, args.selected_layers)
    model_info = model_metadata(model, processor, dtype, snapshot, selected_layers)
    write_event_position_convention(output_dir / "phase2_event_position_convention.md")

    config = {
        "phase": "phase2",
        "phase1_dir": args.phase1_dir,
        "model_cache_root": args.model_cache_root,
        "resolved_snapshot": str(snapshot),
        "num_samples_requested": args.num_samples,
        "num_samples_selected": len(rows),
        "dtype": args.dtype,
        "device": args.device,
        "selected_layers": selected_layers,
        "pruning_layer": args.pruning_layer,
        "cache_policy": "full_prefix_forward_per_condition_with_past_key_values_none",
        "tensor_storage": {
            "event_queries": "phase2_event_queries.pt",
            "visual_keys": "phase2_visual_keys.pt",
            "dtype": "float16_cpu",
        },
        "fastv_status": rows[0].fastv_status if rows else "",
    }
    write_json(output_dir / "phase2_config.json", config)

    query_tensors: dict[str, dict[str, Any]] = {}
    visual_key_tensors: dict[str, dict[str, Any]] = {}
    metadata_rows: list[dict[str, Any]] = []
    mapping_rows: list[dict[str, Any]] = []
    same_prefix_rows: list[dict[str, Any]] = []
    cache_rows: list[dict[str, Any]] = []

    try:
        for row in rows:
            result = process_sample(model, processor, row, selected_layers)
            query_tensors.update(result["query_tensors"])
            visual_key_tensors[row.sample_id] = result["visual_keys"]
            metadata_rows.extend(result["metadata_rows"])
            mapping_rows.append(result["mapping_row"])
            same_prefix_rows.extend(result["same_prefix_rows"])
            cache_rows.append(result["cache_row"])
            write_jsonl(output_dir / "phase2_query_tensors_metadata.jsonl", metadata_rows)
            write_jsonl(output_dir / "phase2_visual_token_mapping.jsonl", mapping_rows)
            write_jsonl(output_dir / "phase2_same_prefix_checks.jsonl", same_prefix_rows)
            write_jsonl(output_dir / "phase2_cache_recompute_checks.jsonl", cache_rows)
    except Exception as exc:
        write_summary(
            output_dir / "phase2_summary.md",
            status="failed",
            blockers=[repr(exc)],
            model_info=model_info,
            selected_layers=selected_layers,
        )
        raise

    torch.save(
        {
            "format": "piqd_phase2_event_queries_v1",
            "selected_layers": selected_layers,
            "events": query_tensors,
        },
        output_dir / "phase2_event_queries.pt",
    )
    torch.save(
        {
            "format": "piqd_phase2_visual_keys_v1",
            "selected_layers": selected_layers,
            "samples": visual_key_tensors,
        },
        output_dir / "phase2_visual_keys.pt",
    )

    checks = summarize_checks(metadata_rows, mapping_rows, same_prefix_rows, cache_rows, selected_layers, model_info)
    write_summary(
        output_dir / "phase2_summary.md",
        status="ok",
        model_info=model_info,
        selected_layers=selected_layers,
        checks=checks,
        num_samples=len(rows),
        num_events=len(metadata_rows),
        fastv_status=config["fastv_status"],
    )


def process_sample(model: Any, processor: Any, row: Phase2ArtifactRow, selected_layers: list[int]) -> dict[str, Any]:
    device = next(model.parameters()).device
    raw_inputs = processor_inputs(processor, row.image_path, row.prompt)
    teacher_inputs = append_generated_tokens(raw_inputs, row.generated_token_ids)
    inputs = move_inputs(teacher_inputs, device)
    full_prefill = build_prefill(model, inputs)
    if full_prefill.num_visual_tokens != row.num_visual_tokens_full:
        raise ValueError(
            f"{row.sample_id}: full visual count mismatch, Phase 1={row.num_visual_tokens_full}, "
            f"Phase 2={full_prefill.num_visual_tokens}"
        )

    cfq = build_condition_replay_from_prefill(
        full_prefill=full_prefill,
        generated_token_ids=row.generated_token_ids,
        events=row.events,
        condition="CFQ",
        sample_id=row.sample_id,
    )
    cq = build_condition_replay_from_prefill(
        full_prefill=full_prefill,
        generated_token_ids=row.generated_token_ids,
        events=row.events,
        condition="CQ",
        retained_visual_indices=row.retained_visual_token_indices,
        sample_id=row.sample_id,
    )

    cq_capture = run_capture_condition(model, cq, selected_layers, capture_visual_keys=False)
    cfq_capture = run_capture_condition(model, cfq, selected_layers, capture_visual_keys=True)
    k_full = stack_visual_keys(cfq_capture, selected_layers)

    query_tensors: dict[str, dict[str, Any]] = {}
    metadata_rows: list[dict[str, Any]] = []
    same_prefix_rows: list[dict[str, Any]] = []
    prefix_hash = hash_token_ids(row.generated_token_ids)
    for event in row.events:
        key = event_key(event)
        event_uid = f"{row.sample_id}::{key}"
        q_cq = stack_queries(cq_capture, key, selected_layers)
        q_cfq = stack_queries(cfq_capture, key, selected_layers)
        if tuple(q_cq.shape) != tuple(q_cfq.shape):
            raise ValueError(f"{event_uid}: q_CQ and q_CFQ shape mismatch")
        token_cq = int(cq.prefill.input_ids[0, cq.target_positions[key]].item())
        token_cfq = int(cfq.prefill.input_ids[0, cfq.target_positions[key]].item())
        if token_cq != event.token_id or token_cfq != event.token_id:
            raise ValueError(f"{event_uid}: same-position token mismatch")
        context = decoded_context(processor.tokenizer, row.generated_token_ids, event.generated_token_index)
        query_tensors[event_uid] = {
            "q_CQ": q_cq,
            "q_CFQ": q_cfq,
            "sample_id": row.sample_id,
            "event_type": event.event_type,
            "generated_token_index": event.generated_token_index,
        }
        metadata_rows.append(
            {
                "sample_id": row.sample_id,
                "event_uid": event_uid,
                "event_type": event.event_type,
                "event_source": event.source,
                "generation_step": event.generated_token_index,
                "generated_token_index": event.generated_token_index,
                "absolute_position_CQ": cq.target_positions[key],
                "absolute_position_CFQ": cfq.target_positions[key],
                "token_id_at_position": event.token_id,
                "decoded_local_context": context,
                "selected_layers": selected_layers,
                "head_policy": "all_heads_saved",
                "q_CQ_shape": list(q_cq.shape),
                "q_CFQ_shape": list(q_cfq.shape),
                "tensor_key": event_uid,
                "prefix_hash": prefix_hash,
            }
        )
        same_prefix_rows.append(
            {
                "sample_id": row.sample_id,
                "event_uid": event_uid,
                "event_type": event.event_type,
                "same_generated_token_ids": True,
                "same_generated_token_index": True,
                "same_decoded_local_context": True,
                "same_position_token_id": token_cq == token_cfq == event.token_id,
                "token_id_at_position_CQ": token_cq,
                "token_id_at_position_CFQ": token_cfq,
                "generated_token_index_CQ": event.generated_token_index,
                "generated_token_index_CFQ": event.generated_token_index,
                "absolute_position_CQ": cq.target_positions[key],
                "absolute_position_CFQ": cfq.target_positions[key],
                "decoded_local_context": context,
                "prefix_hash_CQ": prefix_hash,
                "prefix_hash_CFQ": prefix_hash,
            }
        )

    mapping_row = build_visual_mapping_row(row, full_prefill, cq, cfq, k_full)
    cache_row = {
        "sample_id": row.sample_id,
        "cache_policy": "full_prefix_forward_per_condition_with_past_key_values_none",
        "chunked": False,
        "CQ_starts_with_past_key_values_none": True,
        "CFQ_starts_with_past_key_values_none": True,
        "past_key_values_reused_across_visual_conditions": False,
        "CQ_cache_context_id": cq.cache_context_id,
        "CFQ_cache_context_id": cfq.cache_context_id,
        "cache_context_ids_distinct": cq.cache_context_id != cfq.cache_context_id,
        "chunked_past_key_values_chained_within_condition_only": True,
    }
    return {
        "query_tensors": query_tensors,
        "visual_keys": {
            "K_full": k_full,
            "sample_id": row.sample_id,
            "selected_layers": selected_layers,
            "K_full_shape": list(k_full.shape),
            "K_full_hash": tensor_hash(k_full),
        },
        "metadata_rows": metadata_rows,
        "mapping_row": mapping_row,
        "same_prefix_rows": same_prefix_rows,
        "cache_row": cache_row,
    }


def run_capture_condition(
    model: Any,
    replay: Any,
    selected_layers: list[int],
    capture_visual_keys: bool,
) -> dict[int, Any]:
    hook = QueryKeyCaptureHook(
        selected_layers=selected_layers,
        target_positions=replay.target_positions,
        visual_positions=replay.prefill.visual_positions,
        capture_visual_keys=capture_visual_keys,
    )
    hook.attach(model)
    try:
        with torch.no_grad():
            outputs = language_model_forward(model, replay.prefill, past_key_values=None)
            if outputs.past_key_values is None:
                raise RuntimeError(f"{replay.condition}: model did not return past_key_values")
            del outputs
    finally:
        hook.detach()
    return hook.captured


def build_visual_mapping_row(
    row: Phase2ArtifactRow,
    full_prefill: Any,
    cq: Any,
    cfq: Any,
    k_full: torch.Tensor,
) -> dict[str, Any]:
    retained_mapping = []
    for retained_local_idx, full_visual_idx in enumerate(row.retained_visual_token_indices):
        retained_mapping.append(
            {
                "retained_list_index": retained_local_idx,
                "full_visual_index": int(full_visual_idx),
                "full_sequence_position": int(full_prefill.visual_positions[int(full_visual_idx)].item()),
                "CQ_sequence_position": int(cq.prefill.visual_positions[retained_local_idx].item()),
            }
        )
    return {
        "sample_id": row.sample_id,
        "num_visual_tokens_full": row.num_visual_tokens_full,
        "num_visual_tokens_retained": row.num_visual_tokens_retained,
        "retained_visual_indices_from_phase1": row.retained_visual_token_indices,
        "full_visual_sequence_positions": [int(item) for item in full_prefill.visual_positions.tolist()],
        "CQ_visual_sequence_positions": [int(item) for item in cq.prefill.visual_positions.tolist()],
        "CFQ_visual_sequence_positions": [int(item) for item in cfq.prefill.visual_positions.tolist()],
        "retained_visual_mapping": retained_mapping,
        "image_grid_thw": full_prefill.image_grid_thw.detach().cpu().tolist() if full_prefill.image_grid_thw is not None else None,
        "K_full_shape": list(k_full.shape),
        "K_full_hash": tensor_hash(k_full),
        "fastv_status": row.fastv_status,
        "pruning_mode": row.pruning_mode,
        "phase2_recomputed_retained_indices": False,
    }


def resolve_selected_layers(model: Any, pruning_layer: int, selected_layers_arg: str) -> list[int]:
    num_layers = len(model.model.language_model.layers)
    if selected_layers_arg.strip():
        layers = [int(item.strip()) for item in selected_layers_arg.split(",") if item.strip()]
    else:
        layers = [pruning_layer, pruning_layer + 1, num_layers // 2, num_layers - 1]
    layers = sorted(set(layers))
    for layer_idx in layers:
        if layer_idx < 0 or layer_idx >= num_layers:
            raise ValueError(f"selected layer out of range: {layer_idx}; model has {num_layers} layers")
    return layers


def model_metadata(model: Any, processor: Any, dtype: torch.dtype, snapshot: Path, selected_layers: list[int]) -> dict[str, Any]:
    text_config = model.config.text_config
    return {
        "model_class": type(model).__name__,
        "processor_class": type(processor).__name__,
        "snapshot": str(snapshot),
        "dtype": str(dtype),
        "device": str(next(model.parameters()).device),
        "device_map": "single_device_explicit_to_cuda",
        "attn_implementation": getattr(model.config, "_attn_implementation", "unknown"),
        "num_layers": len(model.model.language_model.layers),
        "selected_layers": selected_layers,
        "num_heads": int(text_config.num_attention_heads),
        "num_key_value_heads": int(text_config.num_key_value_heads),
        "head_dim": int(getattr(text_config, "head_dim", text_config.hidden_size // text_config.num_attention_heads)),
    }


def summarize_checks(
    metadata_rows: list[dict[str, Any]],
    mapping_rows: list[dict[str, Any]],
    same_prefix_rows: list[dict[str, Any]],
    cache_rows: list[dict[str, Any]],
    selected_layers: list[int],
    model_info: dict[str, Any],
) -> dict[str, Any]:
    same_prefix_pass = all(row["same_generated_token_ids"] and row["same_decoded_local_context"] for row in same_prefix_rows)
    same_position_pass = all(row["same_position_token_id"] and row["generated_token_index_CQ"] == row["generated_token_index_CFQ"] for row in same_prefix_rows)
    cache_pass = all(
        row["CQ_starts_with_past_key_values_none"]
        and row["CFQ_starts_with_past_key_values_none"]
        and not row["past_key_values_reused_across_visual_conditions"]
        and row["cache_context_ids_distinct"]
        for row in cache_rows
    )
    query_shape_pass = all(
        row["q_CQ_shape"] == row["q_CFQ_shape"]
        and row["q_CQ_shape"] == [len(selected_layers), model_info["num_heads"], model_info["head_dim"]]
        for row in metadata_rows
    )
    key_shape_pass = all(
        row["K_full_shape"][0] == len(selected_layers)
        and row["K_full_shape"][1] == model_info["num_heads"]
        and row["K_full_shape"][2] == row["num_visual_tokens_full"]
        and row["K_full_shape"][3] == model_info["head_dim"]
        and row["num_visual_tokens_full"] > row["num_visual_tokens_retained"]
        and all(0 <= idx < row["num_visual_tokens_full"] for idx in row["retained_visual_indices_from_phase1"])
        for row in mapping_rows
    )
    fastv_pass = all(not row["phase2_recomputed_retained_indices"] for row in mapping_rows)
    return {
        "same_prefix_check": same_prefix_pass,
        "same_position_check": same_position_pass,
        "no_cross_condition_kv_reuse_check": cache_pass,
        "query_shape_check": query_shape_pass,
        "full_bank_key_shape_check": key_shape_pass,
        "fastv_artifact_consistency_check": fastv_pass,
    }


def write_event_position_convention(path: Path) -> None:
    lines = [
        "# Phase 2 Event Position Convention",
        "",
        "Phase 1 generation logs record `step = t` after the pruned model has emitted generated token `g_t` and that token is fed back through the language model to predict the next token.",
        "",
        "Therefore Phase 2 extracts `q_t` at the hidden/query state of generated token `g_t`, not at the earlier prompt-only next-token prediction that produced `g_t`.",
        "",
        "For teacher-forced replay, the model input is `[visual condition + original prompt + stored generated prefix Y^P]`. The generated-token index is identical for CQ and CFQ. Absolute sequence positions may differ because CQ delete-pruning removes unretained visual tokens.",
        "",
        "For each event:",
        "- `generated_token_index` is the index `t` into `generated_prefix_token_ids`.",
        "- `absolute_position_CQ = CQ_prefix_start + t`.",
        "- `absolute_position_CFQ = CFQ_prefix_start + t`.",
        "- `token_id_at_position` must equal `generated_prefix_token_ids[t]` in both conditions.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_blockers(path: Path, blockers: list[str]) -> None:
    lines = ["# Phase 2 Blockers", ""]
    lines.extend(f"- {blocker}" for blocker in blockers)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_summary(
    path: Path,
    *,
    status: str,
    blockers: list[str] | None = None,
    model_info: dict[str, Any] | None = None,
    selected_layers: list[int] | None = None,
    checks: dict[str, Any] | None = None,
    num_samples: int = 0,
    num_events: int = 0,
    fastv_status: str = "",
) -> None:
    blockers = blockers or []
    model_info = model_info or {}
    selected_layers = selected_layers or []
    checks = checks or {}
    all_checks_pass = bool(checks) and all(bool(value) for value in checks.values())
    lines = [
        "# Phase 2 Summary",
        "",
        f"- status: `{status}`",
        f"- samples_processed: `{num_samples}`",
        f"- events_processed: `{num_events}`",
        f"- model_path: `{model_info.get('snapshot', '')}`",
        f"- model_class: `{model_info.get('model_class', '')}`",
        f"- dtype: `{model_info.get('dtype', '')}`",
        f"- device_map: `{model_info.get('device_map', '')}`",
        f"- selected_layers: `{selected_layers}`",
        f"- number_of_heads: `{model_info.get('num_heads', '')}`",
        f"- head_dim: `{model_info.get('head_dim', '')}`",
        f"- fastv_status: `{fastv_status}`",
        f"- same_prefix_check: `{checks.get('same_prefix_check', False)}`",
        f"- same_position_check: `{checks.get('same_position_check', False)}`",
        f"- no_cross_condition_KV_reuse_check: `{checks.get('no_cross_condition_kv_reuse_check', False)}`",
        f"- query_shape_check: `{checks.get('query_shape_check', False)}`",
        f"- K_full_shape_check: `{checks.get('full_bank_key_shape_check', False)}`",
        f"- FastV_artifact_consistency_check: `{checks.get('fastv_artifact_consistency_check', False)}`",
        f"- phase3_safe_to_start: `{str(status == 'ok' and all_checks_pass).lower()}`",
        "- phase3_requires_explicit_user_approval: `true`",
        "- phase3_started: `false`",
        "",
        "## Tensor Shapes",
        "- Query tensors are stored per event as `[selected_layers, num_heads, head_dim]` in `phase2_event_queries.pt`.",
        "- Full visual-bank keys are stored per sample as `[selected_layers, num_heads, num_visual_tokens, head_dim]` in `phase2_visual_keys.pt`.",
        "",
        "## Visual Token Counts",
        "See `phase2_visual_token_mapping.jsonl` for per-sample full and retained visual token counts.",
        "",
        "## Unresolved Risks",
        "- FastV remains `approximate_fastv_style_static_pruning`; faithful FastV validation is still required before final claims.",
        "- Phase 2 stores queries and K_full only; it does not compute retrieval metrics or behavioral continuation.",
    ]
    if blockers:
        lines.extend(["", "## Blockers", *[f"- {blocker}" for blocker in blockers]])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def tensor_hash(tensor: torch.Tensor) -> str:
    import hashlib

    contiguous = tensor.detach().cpu().contiguous()
    return hashlib.sha256(contiguous.numpy().tobytes()).hexdigest()


if __name__ == "__main__":
    main()
