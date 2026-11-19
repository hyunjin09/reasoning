#!/usr/bin/env python3
"""Run passive Stage 3C.2 attention/QK/Value extraction."""

from __future__ import annotations

import argparse
import gc
import json
import math
import os
import time
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import torch

from visual_reasoning.stage0.data import load_mathverse_rows
from visual_reasoning.stage0.modeling import load_runtime, runtime_environment
from visual_reasoning.stage3a.runtime import next_token_logits, prepare_custom_image
from visual_reasoning.stage3b0.layout import build_token_groups
from visual_reasoning.stage3c1.runtime import MultiLayerAttentionCapture
from visual_reasoning.stage3c2.metrics import build_exclusive_budget_groups


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c2"
CONDITIONS = ("O", "O_sham", "C", "C_sham")
GROUP_NAMES = (
    "target_roi", "mention_roi", "irrelevant_roi", "other_visual",
    "prompt_question", "previous_reasoning", "candidate_sink", "other",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--roi-mapping", type=Path, required=True)
    parser.add_argument("--mention-annotations", type=Path, required=True)
    parser.add_argument("--semantic-labels", type=Path, required=True)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--model-checkpoint", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--shard-count", type=int, default=1)
    parser.add_argument("--max-bases", type=int, default=0)
    parser.add_argument("--baseline-audit", action="store_true")
    parser.add_argument("--repeat-first", action="store_true")
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def condition_paths(base: str) -> dict[str, Path]:
    metadata = read_json(ROOT / "outputs/stage3b3_redesign/counterfactual_shams" / base / "edit_metadata.json")
    if metadata["manual_validation"]["status"] != "pass":
        raise RuntimeError(f"Four-condition edit validation failed for {base}")
    return {condition: ROOT / metadata["paths"][condition] for condition in CONDITIONS}


def requested_layout(prompt_length: int, ed: int) -> tuple[dict[int, list[int]], dict[int, list[int]]]:
    offsets = (-16, -8, -4, -2, -1, 0)
    a = [prompt_length + ed + offset - 1 for offset in offsets if ed + offset >= 1]
    b_center = ed - 1
    b = [prompt_length + b_center + offset - 1 for offset in offsets if b_center + offset >= 1]
    return {28: b, 29: a}, {28: [0, 1, 2, 3, 4, 5, 6, 16], 29: [0, 1, 2, 3, 6, 11, 12, 15]}


def target_definition(layer: int) -> tuple[str, int, list[int], list[int]]:
    if layer == 29:
        return "target_a", 0, [11, 6, 15, 12], [0, 1, 2, 3]
    if layer == 28:
        return "target_b", -1, [16, 0, 3, 6], [1, 2, 4, 5]
    raise ValueError(layer)


def finite_summary(values: torch.Tensor, attention: torch.Tensor | None = None) -> dict[str, float | None]:
    data = values.detach().float()
    valid = torch.isfinite(data)
    if not bool(valid.any()):
        return {"mean": None, "median": None, "maximum": None, "attention_weighted_mean": None}
    selected = data[valid]
    weighted = None
    if attention is not None:
        weights = attention.detach().float()[valid]
        if float(weights.sum()) > 0:
            weighted = float((selected * weights).sum() / weights.sum())
    return {"mean": float(selected.mean()), "median": float(selected.median()), "maximum": float(selected.max()), "attention_weighted_mean": weighted}


def entropy(values: torch.Tensor) -> float:
    probabilities = values.detach().float()
    positive = probabilities > 0
    return float(-(probabilities[positive] * probabilities[positive].log()).sum())


def sink_groups(token_ids: Sequence[int], current: int, visual: Sequence[int], tokenizer: Any) -> dict[str, list[int]]:
    visual_set = set(map(int, visual))
    all_special = set(map(int, tokenizer.all_special_ids))
    special = [index for index, token in enumerate(token_ids[:current + 1]) if token in all_special and index not in visual_set]
    newline = [index for index, token in enumerate(token_ids[:current + 1]) if "\n" in tokenizer.decode([int(token)], skip_special_tokens=False) or "\r" in tokenizer.decode([int(token)], skip_special_tokens=False)]
    adjacent = []
    if visual_set:
        adjacent = [index for index in (min(visual_set) - 1, max(visual_set) + 1) if 0 <= index <= current and index not in visual_set]
    return {"first_prompt_token": [0], "special_control": special, "newline_formatting": newline, "image_boundary_neighbor": adjacent, "active_query_token": [current]}


@torch.inference_mode()
def capture_condition(*, model: Any, prepared: dict[str, Any], context: Sequence[int], positions_by_layer: dict[int, list[int]], heads_by_layer: dict[int, list[int]], seed: int) -> tuple[torch.Tensor, dict[int, dict[str, Any]]]:
    capture = MultiLayerAttentionCapture(model=model, positions_by_layer=positions_by_layer, heads_by_layer=heads_by_layer)
    with capture:
        logits = next_token_logits(model=model, prepared=prepared, prefix_token_ids=context, seed=seed)
    return logits, capture.complete_states()


def tensor_state_signature(states: dict[int, dict[str, Any]]) -> list[torch.Tensor]:
    tensors: list[torch.Tensor] = []
    for layer in sorted(states):
        state = states[layer]
        tensors.extend([state["key"], state["value"]])
        for position in state["positions"]:
            tensors.extend(state["rows"][position][name] for name in ("query", "raw_dot", "scaled_logits", "final_logits", "attention", "head_output"))
    return tensors


def group_measurement(*, indices: list[int], alpha: torch.Tensor, key_norm: torch.Tensor, value_norm: torch.Tensor, cosine: torch.Tensor, raw_dot: torch.Tensor, scaled: torch.Tensor, final_logits: torch.Tensor, values: torch.Tensor, wo: torch.Tensor, logical_head: int) -> tuple[dict[str, Any], torch.Tensor, torch.Tensor]:
    head_dim = int(values.shape[-1])
    index_tensor = torch.tensor(indices, dtype=torch.long)
    mass = float(alpha[index_tensor].sum()) if indices else 0.0
    vector = (alpha[index_tensor, None] * values[index_tensor]).sum(dim=0) if indices else torch.zeros(head_dim)
    start = logical_head * head_dim
    projected = torch.nn.functional.linear(vector, wo[:, start:start + head_dim])
    geometry = {}
    for name, tensor in (("k_norm", key_norm), ("qk_cosine", cosine), ("raw_dot", raw_dot), ("scaled_logit", scaled), ("final_masked_logit", final_logits), ("value_norm", value_norm)):
        geometry[name] = finite_summary(tensor[index_tensor], alpha[index_tensor]) if indices else finite_summary(torch.empty(0))
    return ({
        "token_count": len(indices), "attention_mass": mass,
        "attention_density": mass / len(indices) if indices else 0.0,
        "geometry": geometry, "alpha_v_norm": float(vector.norm()),
        "alpha_v_norm_per_attention_mass": float(vector.norm() / mass) if mass > 0 else None,
        "wo_residual_norm": float(projected.norm()),
    }, vector, projected)


def analyze_layer(*, base: str, example_id: str, condition: str, layer_state: dict[str, Any], prompt_length: int, ed: int, question_positions: Sequence[int], visual_positions: Sequence[int], target_positions: Sequence[int], mention_positions: Sequence[int], irrelevant_positions: Sequence[int], token_ids: Sequence[int], tokenizer: Any, state_labels: dict[tuple[str, int], dict[str, Any]], raw_path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    layer = int(layer_state["layer_index"])
    target_id, center_delta, causal_heads, control_heads = target_definition(layer)
    captured_heads = [int(value) for value in layer_state["heads"]]
    head_lookup = {head: index for index, head in enumerate(captured_heads)}
    key_full, value_full, wo = layer_state["key"], layer_state["value"], layer_state["wo_weight"]
    raw_records, head_rows, set_rows = [], [], []
    max_mass_error = max_alpha_error = max_wo_error = 0.0
    all_finite = True
    for position in layer_state["positions"]:
        generated_index = int(position) - prompt_length + 1
        center = ed + center_delta
        offset = generated_index - center
        label = state_labels[(target_id, generated_index)]
        row_state = layer_state["rows"][position]
        visible = int(position) + 1
        groups = build_exclusive_budget_groups(
            current_position=position, prompt_length=prompt_length,
            visual_positions=visual_positions, target_positions=target_positions,
            mention_positions=mention_positions, irrelevant_positions=irrelevant_positions,
            question_positions=question_positions, sink_positions=[0],
        )
        query = row_state["query"]
        key, values = key_full[:, :visible, :], value_full[:, :visible, :]
        raw_dot, scaled, final_logits, attention = row_state["raw_dot"], row_state["scaled_logits"], row_state["final_logits"], row_state["attention"]
        q_norm, key_norm, value_norm = query.norm(dim=-1), key.norm(dim=-1), values.norm(dim=-1)
        cosine = raw_dot / (q_norm[:, None] * key_norm).clamp_min(1e-30)
        raw_records.append({"offset": offset, "position": position, "heads": np.asarray(captured_heads), "q_norm": q_norm.numpy(), "k_norm": key_norm.numpy(), "value_norm": value_norm.numpy(), "cosine": cosine.numpy(), "raw_dot": raw_dot.numpy(), "scaled_logits": scaled.numpy(), "final_logits": final_logits.numpy(), "attention": attention.numpy()})
        vectors_by_head: dict[int, dict[str, torch.Tensor]] = {}
        projected_by_head: dict[int, dict[str, torch.Tensor]] = {}
        for local_head, logical_head in enumerate(captured_heads):
            alpha = attention[local_head]
            metrics, vectors, projected = {}, {}, {}
            for name in GROUP_NAMES:
                metrics[name], vectors[name], projected[name] = group_measurement(
                    indices=groups[name], alpha=alpha, key_norm=key_norm[local_head], value_norm=value_norm[local_head],
                    cosine=cosine[local_head], raw_dot=raw_dot[local_head], scaled=scaled[local_head], final_logits=final_logits[local_head],
                    values=values[local_head], wo=wo, logical_head=logical_head,
                )
            vectors_by_head[logical_head], projected_by_head[logical_head] = vectors, projected
            mass_sum = sum(float(metrics[name]["attention_mass"]) for name in GROUP_NAMES)
            mass_error = abs(mass_sum - 1.0)
            reconstructed = (alpha[:, None] * values[local_head]).sum(dim=0)
            alpha_error = float((sum(vectors.values()) - reconstructed).abs().max())
            head_dim = int(values.shape[-1]); start = logical_head * head_dim
            direct_wo = torch.nn.functional.linear(reconstructed, wo[:, start:start + head_dim])
            wo_error = float((sum(projected.values()) - direct_wo).abs().max())
            max_mass_error, max_alpha_error, max_wo_error = max(max_mass_error, mass_error), max(max_alpha_error, alpha_error), max(max_wo_error, wo_error)
            visual_indices = sorted(set(map(int, visual_positions)))
            visual_alpha = alpha[torch.tensor(visual_indices, dtype=torch.long)]
            visual_mass = float(visual_alpha.sum())
            visual_distribution = visual_alpha / visual_mass if visual_mass > 0 else torch.zeros_like(visual_alpha)
            nonsink = alpha[torch.tensor(sorted(set(range(visible)) - {0}), dtype=torch.long)]
            nonsink = nonsink / nonsink.sum() if float(nonsink.sum()) > 0 else nonsink
            secondary_sinks = sink_groups(token_ids, position, visual_positions, tokenizer)
            secondary = {}
            for sink_name, indices in secondary_sinks.items():
                subset = [index for index in indices if index < visible]
                secondary[sink_name] = {"positions": subset, "mass": float(alpha[torch.tensor(subset, dtype=torch.long)].sum()) if subset else 0.0}
            finite = bool(torch.isfinite(alpha).all() and torch.isfinite(query[local_head]).all() and torch.isfinite(key_norm[local_head]).all() and torch.isfinite(value_norm[local_head]).all())
            all_finite &= finite
            head_rows.append({
                "base_problem_id": base, "example_id": example_id, "condition": condition,
                "target_id": target_id, "head_role": "causal" if logical_head in causal_heads else "noncausal_control",
                "layer_index": layer, "logical_query_head": logical_head,
                "kv_head": int(layer_state["query_to_kv_group"][logical_head]),
                "offset_from_target": offset, "offset_from_E_d": generated_index - ed,
                "generated_index": generated_index, "absolute_query_position": int(position),
                "semantic_state": label["semantic_state"], "q_norm": float(q_norm[local_head]), "groups": metrics,
                "attention_entropy_all_context": entropy(alpha),
                "attention_entropy_visual_only": entropy(visual_distribution) if visual_mass > 0 else 0.0,
                "attention_entropy_non_sink": entropy(nonsink) if nonsink.numel() else 0.0,
                "secondary_sink_candidates": secondary,
                "source_mass_sum": mass_sum, "source_mass_absolute_error": mass_error,
                "alpha_v_reconstruction_max_abs_error": alpha_error, "wo_reconstruction_max_abs_error": wo_error,
                "all_values_finite": finite, "attention_manipulated": False,
            })
        row_by_head = {row["logical_query_head"]: row for row in head_rows[-len(captured_heads):]}
        for role, heads in (("causal", causal_heads), ("noncausal_control", control_heads)):
            set_groups = {}
            for name in GROUP_NAMES:
                wo_sum = sum(projected_by_head[head][name] for head in heads)
                set_groups[name] = {
                    "mean_attention_mass": float(np.mean([row_by_head[head]["groups"][name]["attention_mass"] for head in heads])),
                    "mean_attention_density": float(np.mean([row_by_head[head]["groups"][name]["attention_density"] for head in heads])),
                    "mean_qk_cosine": float(np.mean([row_by_head[head]["groups"][name]["geometry"]["qk_cosine"]["mean"] for head in heads])),
                    "mean_scaled_logit": float(np.mean([row_by_head[head]["groups"][name]["geometry"]["scaled_logit"]["mean"] for head in heads])),
                    "mean_alpha_v_norm": float(np.mean([row_by_head[head]["groups"][name]["alpha_v_norm"] for head in heads])),
                    "mean_wo_residual_norm": float(np.mean([row_by_head[head]["groups"][name]["wo_residual_norm"] for head in heads])),
                    "post_wo_head_set_sum_norm": float(wo_sum.norm()),
                }
            set_rows.append({
                "base_problem_id": base, "example_id": example_id, "condition": condition,
                "target_id": target_id, "head_set_role": role, "layer_index": layer, "heads": heads,
                "offset_from_target": offset, "offset_from_E_d": generated_index - ed,
                "generated_index": generated_index, "semantic_state": label["semantic_state"],
                "groups": set_groups,
                "mean_attention_entropy_all_context": float(np.mean([row_by_head[head]["attention_entropy_all_context"] for head in heads])),
                "mean_attention_entropy_visual_only": float(np.mean([row_by_head[head]["attention_entropy_visual_only"] for head in heads])),
                "mean_attention_entropy_non_sink": float(np.mean([row_by_head[head]["attention_entropy_non_sink"] for head in heads])),
                "attention_manipulated": False,
            })
    max_heads = len(captured_heads); max_source = max(record["attention"].shape[1] for record in raw_records)
    payload: dict[str, np.ndarray] = {"offsets_from_target": np.asarray([r["offset"] for r in raw_records]), "absolute_query_positions": np.asarray([r["position"] for r in raw_records]), "valid_source_lengths": np.asarray([r["attention"].shape[1] for r in raw_records]), "logical_heads": np.tile(np.asarray(captured_heads), (len(raw_records), 1)), "q_norm": np.full((len(raw_records), max_heads), np.nan, np.float32)}
    for metric in ("k_norm", "value_norm", "cosine", "raw_dot", "scaled_logits", "final_logits", "attention"):
        payload[metric] = np.full((len(raw_records), max_heads, max_source), np.nan, np.float32)
    for time_index, record in enumerate(raw_records):
        source = record["attention"].shape[1]; payload["q_norm"][time_index] = record["q_norm"]
        for metric in ("k_norm", "value_norm", "cosine", "raw_dot", "scaled_logits", "final_logits", "attention"):
            payload[metric][time_index, :, :source] = record[metric]
    raw_path.parent.mkdir(parents=True, exist_ok=True); np.savez_compressed(raw_path, **payload)
    audit = {"layer_index": layer, "tensor_shapes": layer_state["tensor_shapes"], "query_to_kv_group": layer_state["query_to_kv_group"], "wo_bias_present": bool(layer_state["wo_bias_present"]), "eager_reconstruction": layer_state["reconstruction"], "maximum_source_mass_absolute_error": max_mass_error, "maximum_alpha_v_reconstruction_absolute_error": max_alpha_error, "maximum_wo_reconstruction_absolute_error": max_wo_error, "all_values_finite": all_finite, "raw_tensor_path": str(raw_path.relative_to(ROOT)), "raw_tensor_granularity": "per condition, target layer, temporal checkpoint, logical query head, and individual causally visible source-token position"}
    return head_rows, set_rows, audit


def main() -> None:
    args = parse_args(); config = read_json(args.config)
    world_size = int(os.environ.get("WORLD_SIZE", "1"))
    local_rank = int(os.environ.get("LOCAL_RANK", str(args.shard_index)))
    if world_size > 1:
        args.shard_index = local_rank
        args.shard_count = world_size
    torch.cuda.set_device(local_rank if world_size > 1 else 0)
    output_dir = args.output_dir.resolve()
    if world_size > 1 and "smoke" not in output_dir.parts:
        output_dir = output_dir / f"shard_{local_rank}"
    output_dir.relative_to(OUT.resolve())
    manifest = read_jsonl(args.manifest)[args.shard_index::args.shard_count]
    if args.max_bases: manifest = manifest[:args.max_bases]
    events = {str(row["base_problem_id"]): row for row in read_jsonl(args.events)}
    rois = {str(row["base_problem_id"]): row for row in read_jsonl(args.roi_mapping)}
    mentions = {str(row["base_problem_id"]): row for row in read_jsonl(args.mention_annotations)}
    labels_all = read_jsonl(args.semantic_labels)
    labels = {str(base): {} for base in (row["base_problem_id"] for row in manifest)}
    for row in labels_all:
        if str(row["base_problem_id"]) in labels:
            labels[str(row["base_problem_id"])][(row["target_id"], int(row["generated_index"]))] = row
    data = {str(row["sample_index"]): row for row in load_mathverse_rows(args.dataset_root)}
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "run_config.json", {"config": str(args.config.resolve()), "manifest": str(args.manifest.resolve()), "shard_index": args.shard_index, "shard_count": args.shard_count, "base_problem_ids": [str(row["base_problem_id"]) for row in manifest], "baseline_audit": args.baseline_audit, "repeat_first": args.repeat_first})
    processor, model = load_runtime(args.model_checkpoint, device="cuda")
    environment = runtime_environment(args.model_checkpoint, model, 40_960)
    if "A5000" not in str(environment["gpu_name"]): raise RuntimeError(f"Stage 3C.2 requires A5000, observed {environment['gpu_name']}")
    observed = {"language_layers": int(model.config.text_config.num_hidden_layers), "logical_query_heads": int(model.config.text_config.num_attention_heads), "kv_heads": int(model.config.text_config.num_key_value_heads), "query_heads_per_kv_group": int(model.config.text_config.num_attention_heads // model.config.text_config.num_key_value_heads), "head_dimension": int(model.config.text_config.head_dim)}
    if observed != config["architecture_expected"]: raise RuntimeError(f"Architecture mismatch: {observed}")
    write_json(output_dir / "environment.json", {**environment, "architecture_observed": observed})
    completed = 0
    for item_index, item in enumerate(manifest):
        base = str(item["base_problem_id"]); result_path = output_dir / "examples" / base / "result.json"
        if result_path.is_file():
            if not args.resume: raise FileExistsError(result_path)
            completed += 1; print(f"[{completed}/{len(manifest)}] resume skip base {base}", flush=True); continue
        event, roi, mention = events[base], rois[base], mentions[base]
        context = list(map(int, event["history_before_ed_token_ids"])); ed = int(event["ed_generated_index"])
        if len(context) != ed: raise RuntimeError(f"E_d history mismatch for {base}")
        source_row = data[str(item["example_id"])]
        prepared, metadata = {}, {}
        for condition, path in condition_paths(base).items(): prepared[condition], metadata[condition] = prepare_custom_image(processor, source_row, path, device="cuda")
        prompt_ids = [metadata[c]["prompt_token_ids"] for c in CONDITIONS]; visual = [metadata[c]["visual_token_indices"] for c in CONDITIONS]; grids = [metadata[c]["image_grid_thw"] for c in CONDITIONS]
        layout_exact = all(value == prompt_ids[0] for value in prompt_ids[1:]) and all(value == visual[0] for value in visual[1:]) and all(value == grids[0] for value in grids[1:]) and visual[0] == roi["absolute_source_groups"]["V_all"]
        if not layout_exact: raise RuntimeError(f"Four-condition layout mismatch for {base}")
        question = str(source_row.get("query_cot") or source_row.get("question") or "")
        token_groups = build_token_groups(prompt_token_ids=prompt_ids[0], visual_token_indices=visual[0], question_token_ids=processor.tokenizer.encode(question, add_special_tokens=False))
        prompt_length = len(prompt_ids[0]); positions_by_layer, heads_by_layer = requested_layout(prompt_length, ed); full_ids = [*prompt_ids[0], *context]
        head_rows, set_rows, condition_audits = [], [], {}; instrumentation = determinism = None; started = time.perf_counter()
        for condition in CONDITIONS:
            baseline_logits = next_token_logits(model=model, prepared=prepared[condition], prefix_token_ids=context, seed=int(config["seed"])) if args.baseline_audit and item_index == 0 and condition == "O" else None
            logits, states = capture_condition(model=model, prepared=prepared[condition], context=context, positions_by_layer=positions_by_layer, heads_by_layer=heads_by_layer, seed=int(config["seed"]))
            if baseline_logits is not None:
                error = float((baseline_logits - logits).abs().max()); instrumentation = {"condition": condition, "maximum_logit_absolute_error": error, "tolerance": config["instrumentation_logit_tolerance"], "passed": error <= config["instrumentation_logit_tolerance"]}
            if args.repeat_first and item_index == 0 and condition == "O":
                repeat_logits, repeat_states = capture_condition(model=model, prepared=prepared[condition], context=context, positions_by_layer=positions_by_layer, heads_by_layer=heads_by_layer, seed=int(config["seed"]))
                errors = [float((left - right).abs().max()) for left, right in zip(tensor_state_signature(states), tensor_state_signature(repeat_states), strict=True)]
                logit_error = float((logits - repeat_logits).abs().max()); maximum = max([logit_error, *errors])
                determinism = {"maximum_absolute_error": maximum, "logit_maximum_absolute_error": logit_error, "exact": maximum == 0.0, "passed": maximum <= config["deterministic_repeat_tolerance"]}
            condition_audits[condition] = {}
            for layer, state in states.items():
                raw_root = output_dir / "raw_tensors" if "smoke" in output_dir.parts else OUT / "extraction/raw_tensors"
                rows, aggregates, audit = analyze_layer(base=base, example_id=str(item["example_id"]), condition=condition, layer_state=state, prompt_length=prompt_length, ed=ed, question_positions=token_groups["Q"], visual_positions=visual[0], target_positions=roi["absolute_source_groups"]["V_target"], mention_positions=mention["mention_absolute_source_positions"], irrelevant_positions=roi["absolute_source_groups"]["V_irrelevant"], token_ids=full_ids, tokenizer=processor.tokenizer, state_labels=labels[base], raw_path=raw_root / base / f"{condition}_layer{layer}.npz")
                head_rows.extend(rows); set_rows.extend(aggregates); condition_audits[condition][str(layer)] = audit
            del states, logits; gc.collect(); torch.cuda.empty_cache()
        write_json(result_path, {"base_problem_id": base, "example_id": str(item["example_id"]), "evidence_type": item["evidence_type"], "ed_generated_index": ed, "conditions": list(CONDITIONS), "condition_layout_exact": layout_exact, "question_positions": token_groups["Q"], "visual_positions": visual[0], "target_positions": roi["absolute_source_groups"]["V_target"], "mention_positions": mention["mention_absolute_source_positions"], "irrelevant_positions": roi["absolute_source_groups"]["V_irrelevant"], "head_rows": head_rows, "head_set_rows": set_rows, "audits": condition_audits, "instrumentation_faithfulness": instrumentation, "deterministic_repeat": determinism, "runtime_seconds": time.perf_counter() - started, "selection_used_attention": False, "attention_manipulated": False})
        completed += 1; print(f"[{completed}/{len(manifest)}] completed base {base} seconds={time.perf_counter()-started:.1f}", flush=True)
        del prepared, metadata, head_rows, set_rows; gc.collect(); torch.cuda.empty_cache()
    print(json.dumps({"completed": completed, "requested": len(manifest)}, indent=2), flush=True)


if __name__ == "__main__":
    main()
