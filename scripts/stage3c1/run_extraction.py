#!/usr/bin/env python3
"""Extract the frozen Stage 3C.1 Attention phenotype without interventions."""

from __future__ import annotations

import argparse
import gc
import json
import math
import time
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np
import torch

from visual_reasoning.stage0.data import load_mathverse_rows
from visual_reasoning.stage0.modeling import _reset_generation_state, load_runtime, runtime_environment
from visual_reasoning.stage3a.runtime import next_token_logits, prepare_custom_image
from visual_reasoning.stage3b0.layout import build_token_groups
from visual_reasoning.stage3c1.runtime import MultiLayerAttentionCapture


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c1"
CONDITIONS = ("O", "O_sham", "C", "C_sham")
OFFSETS = (-16, -8, -4, -2, -1, 0)
PARTITION_NAMES = ("visual", "prompt_question", "previous_reasoning", "special_other")
REGION_NAMES = (
    "target_roi",
    "matched_irrelevant_roi",
    "visual_complement",
    "all_visual",
    "prompt_question",
    "previous_reasoning",
    "special_other",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--roi-mapping", type=Path, required=True)
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
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def source_partition(
    *, current: int, prompt_length: int, visual: Sequence[int], question: Sequence[int]
) -> dict[str, list[int]]:
    visual_set = set(map(int, visual))
    question_set = set(map(int, question))
    special_prompt = [
        position
        for position in range(prompt_length)
        if position not in visual_set and position not in question_set
    ]
    groups = {
        "visual": sorted(visual_set),
        "prompt_question": sorted(question_set),
        "previous_reasoning": list(range(prompt_length, current)),
        "special_other": [*special_prompt, current],
    }
    values = [position for positions in groups.values() for position in positions]
    if len(values) != len(set(values)) or sorted(values) != list(range(current + 1)):
        raise RuntimeError("Source partition is not disjoint and exhaustive")
    return groups


def finite_summary(values: torch.Tensor, attention: torch.Tensor | None = None) -> dict[str, float | None]:
    data = values.detach().float()
    valid = torch.isfinite(data)
    if not bool(valid.any()):
        return {"mean": None, "median": None, "maximum": None, "attention_weighted_mean": None}
    selected = data[valid]
    weighted: float | None = None
    if attention is not None:
        weights = attention.detach().float()[valid]
        weight_sum = float(weights.sum().item())
        if weight_sum > 0:
            weighted = float((selected * weights).sum().item() / weight_sum)
    return {
        "mean": float(selected.mean().item()),
        "median": float(selected.median().item()),
        "maximum": float(selected.max().item()),
        "attention_weighted_mean": weighted,
    }


def lse(values: torch.Tensor, indices: Sequence[int]) -> float | None:
    if not indices:
        return None
    selected = values[torch.tensor(indices, dtype=torch.long)]
    selected = selected[torch.isfinite(selected)]
    return float(torch.logsumexp(selected.float(), dim=0).item()) if selected.numel() else None


def entropy(probabilities: torch.Tensor) -> float:
    values = probabilities.detach().float()
    positive = values > 0
    return float(-(values[positive] * values[positive].log()).sum().item())


def classify_position(position: int, groups: dict[str, Sequence[int]]) -> str:
    if position in set(groups["target_roi"]):
        return "target_roi"
    if position in set(groups["matched_irrelevant_roi"]):
        return "matched_irrelevant_roi"
    if position in set(groups["visual_complement"]):
        return "visual_complement"
    if position in set(groups["prompt_question"]):
        return "prompt_question"
    if position in set(groups["previous_reasoning"]):
        return "previous_reasoning"
    return "special_other"


def sink_groups(
    *,
    token_ids: Sequence[int],
    current: int,
    visual_positions: Sequence[int],
    tokenizer: Any,
) -> dict[str, list[int]]:
    visual = set(map(int, visual_positions))
    all_special = set(map(int, tokenizer.all_special_ids))
    special = [
        position
        for position, token_id in enumerate(token_ids[: current + 1])
        if token_id in all_special and position not in visual
    ]
    newline = []
    for position, token_id in enumerate(token_ids[: current + 1]):
        piece = tokenizer.decode([int(token_id)], skip_special_tokens=False)
        if "\n" in piece or "\r" in piece:
            newline.append(position)
    adjacent: list[int] = []
    if visual:
        for position in (min(visual) - 1, max(visual) + 1):
            if 0 <= position <= current and position not in visual:
                adjacent.append(position)
    return {
        "first_prompt_token": [0],
        "special_control": special,
        "newline_formatting": newline,
        "image_boundary_neighbor": sorted(set(adjacent)),
        "active_query_token": [current],
    }


def condition_paths(base: str) -> dict[str, Path]:
    metadata = read_json(
        ROOT / "outputs/stage3b3_redesign/counterfactual_shams" / base / "edit_metadata.json"
    )
    if metadata["manual_validation"]["status"] != "pass":
        raise RuntimeError(f"Four-condition manual edit validation did not pass for base {base}")
    return {condition: ROOT / metadata["paths"][condition] for condition in CONDITIONS}


def requested_layout(prompt_length: int, ed: int) -> tuple[dict[int, list[int]], dict[int, list[int]]]:
    grid = [offset for offset in OFFSETS if ed + offset >= 1]
    positions = [prompt_length + ed + offset - 1 for offset in grid]
    positions_by_layer = {28: positions, 29: positions, 32: [prompt_length + ed - 2, prompt_length + ed - 1]}
    heads_by_layer = {
        28: [0, 1, 2, 3, 4, 5, 6, 16],
        29: [0, 1, 2, 3, 6, 11, 12, 15],
        32: [6, 10, 11, 12, 15],
    }
    return positions_by_layer, heads_by_layer


def active_heads(layer: int, offset: int) -> list[int]:
    if layer == 28:
        return [0, 1, 2, 3, 4, 5, 6, 16]
    if layer == 29:
        return [0, 1, 2, 3, 6, 11, 12, 15]
    if layer == 32 and offset == 0:
        return [6, 11, 12, 15]
    if layer == 32 and offset == -1:
        return [10]
    return []


def role_for_head(layer: int, offset: int, head: int) -> tuple[str, str]:
    if layer == 29:
        return "target_a", "causal" if head in {11, 6, 15, 12} else "noncausal_control"
    if layer == 28:
        return "target_b", "causal" if head in {16, 0, 3, 6} else "noncausal_control"
    if layer == 32 and offset == 0:
        return "target_a_w5_upstream", "upstream_state_control"
    if layer == 32 and offset == -1:
        return "target_b_w5_head10", "secondary_comparator"
    raise ValueError((layer, offset, head))


def analyze_layer(
    *,
    base: str,
    example_id: str,
    condition: str,
    layer_state: dict[str, Any],
    prompt_length: int,
    ed: int,
    question_positions: Sequence[int],
    roi: dict[str, Any],
    token_ids: Sequence[int],
    tokenizer: Any,
    raw_path: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    layer = int(layer_state["layer_index"])
    captured_heads = [int(value) for value in layer_state["heads"]]
    head_lookup = {head: index for index, head in enumerate(captured_heads)}
    key_full = layer_state["key"]
    value_full = layer_state["value"]
    wo = layer_state["wo_weight"]
    head_dim = int(value_full.shape[-1])
    raw_records: list[dict[str, np.ndarray]] = []
    head_rows: list[dict[str, Any]] = []
    set_rows: list[dict[str, Any]] = []
    maximum_source_mass_error = 0.0
    maximum_alpha_v_error = 0.0
    maximum_wo_error = 0.0
    all_finite = True

    for position in layer_state["positions"]:
        generated_index = int(position) - prompt_length + 1
        offset = generated_index - ed
        heads = active_heads(layer, offset)
        if not heads:
            continue
        row_state = layer_state["rows"][position]
        visible = int(position) + 1
        partition = source_partition(
            current=position,
            prompt_length=prompt_length,
            visual=roi["absolute_source_groups"]["V_all"],
            question=question_positions,
        )
        groups = {
            "target_roi": [int(value) for value in roi["absolute_source_groups"]["V_target"]],
            "matched_irrelevant_roi": [int(value) for value in roi["absolute_source_groups"]["V_irrelevant"]],
            "visual_complement": [int(value) for value in roi["absolute_source_groups"]["V_other"]],
            "all_visual": partition["visual"],
            "prompt_question": partition["prompt_question"],
            "previous_reasoning": partition["previous_reasoning"],
            "special_other": partition["special_other"],
        }
        all_non_target = sorted(set(range(visible)) - set(groups["target_roi"]))
        sinks = sink_groups(
            token_ids=token_ids,
            current=position,
            visual_positions=groups["all_visual"],
            tokenizer=tokenizer,
        )
        raw_head_indices = [head_lookup[head] for head in heads]
        query = row_state["query"][raw_head_indices]
        key = key_full[raw_head_indices, :visible, :]
        value = value_full[raw_head_indices, :visible, :]
        raw_dot = row_state["raw_dot"][raw_head_indices]
        scaled = row_state["scaled_logits"][raw_head_indices]
        final_logits = row_state["final_logits"][raw_head_indices]
        attention = row_state["attention"][raw_head_indices]
        head_output = row_state["head_output"][raw_head_indices]
        q_norm = query.norm(dim=-1)
        k_norm = key.norm(dim=-1)
        v_norm = value.norm(dim=-1)
        cosine = raw_dot / (q_norm[:, None] * k_norm).clamp_min(1e-30)

        raw_records.append({
            "offset": np.asarray(offset, dtype=np.int64),
            "position": np.asarray(position, dtype=np.int64),
            "heads": np.asarray(heads, dtype=np.int64),
            "q_norm": q_norm.numpy(),
            "k_norm": k_norm.numpy(),
            "value_norm": v_norm.numpy(),
            "cosine": cosine.numpy(),
            "raw_dot": raw_dot.numpy(),
            "scaled_logits": scaled.numpy(),
            "final_logits": final_logits.numpy(),
            "attention": attention.numpy(),
        })

        per_head_group_vectors: dict[int, dict[str, torch.Tensor]] = {}
        per_head_wo_vectors: dict[int, dict[str, torch.Tensor]] = {}
        for local_head, logical_head in enumerate(heads):
            alpha = attention[local_head]
            values = value[local_head]
            top_positions = torch.topk(alpha, k=min(5, visible)).indices.tolist()
            group_metrics: dict[str, Any] = {}
            group_vectors: dict[str, torch.Tensor] = {}
            wo_vectors: dict[str, torch.Tensor] = {}
            for name in REGION_NAMES:
                indices = groups[name]
                index_tensor = torch.tensor(indices, dtype=torch.long)
                mass = float(alpha[index_tensor].sum().item()) if indices else 0.0
                vector = (
                    (alpha[index_tensor, None] * values[index_tensor]).sum(dim=0)
                    if indices
                    else torch.zeros(head_dim)
                )
                start = logical_head * head_dim
                projected = torch.nn.functional.linear(vector, wo[:, start : start + head_dim])
                group_vectors[name] = vector
                wo_vectors[name] = projected
                geometry = {}
                for metric_name, metric_values in (
                    ("k_norm", k_norm[local_head]),
                    ("cosine", cosine[local_head]),
                    ("raw_dot", raw_dot[local_head]),
                    ("scaled_logit", scaled[local_head]),
                    ("final_masked_logit", final_logits[local_head]),
                    ("value_norm", v_norm[local_head]),
                ):
                    geometry[metric_name] = finite_summary(
                        metric_values[index_tensor], alpha[index_tensor]
                    ) if indices else finite_summary(torch.empty(0))
                group_metrics[name] = {
                    "token_count": len(indices),
                    "attention_mass": mass,
                    "attention_density": mass / len(indices) if indices else 0.0,
                    "logsumexp_final_logit": lse(final_logits[local_head], indices),
                    "geometry": geometry,
                    "alpha_v_norm": float(vector.norm().item()),
                    "alpha_v_norm_per_attention_mass": float(vector.norm().item() / mass) if mass > 0 else None,
                    "wo_residual_norm": float(projected.norm().item()),
                }
            per_head_group_vectors[logical_head] = group_vectors
            per_head_wo_vectors[logical_head] = wo_vectors
            partition_to_region = {
                "visual": "all_visual",
                "prompt_question": "prompt_question",
                "previous_reasoning": "previous_reasoning",
                "special_other": "special_other",
            }
            source_sum = sum(
                float(group_metrics[partition_to_region[name]]["attention_mass"])
                for name in PARTITION_NAMES
            )
            source_error = abs(source_sum - 1.0)
            maximum_source_mass_error = max(maximum_source_mass_error, source_error)
            alpha_sum = sum(
                group_vectors[partition_to_region[name]] for name in PARTITION_NAMES
            )
            reconstructed_head_output = (alpha[:, None] * values).sum(dim=0)
            alpha_error = float((alpha_sum - reconstructed_head_output).abs().max().item())
            maximum_alpha_v_error = max(maximum_alpha_v_error, alpha_error)
            start = logical_head * head_dim
            direct_wo = torch.nn.functional.linear(
                reconstructed_head_output, wo[:, start : start + head_dim]
            )
            reconstructed_wo = sum(
                wo_vectors[partition_to_region[name]] for name in PARTITION_NAMES
            )
            wo_error = float((direct_wo - reconstructed_wo).abs().max().item())
            maximum_wo_error = max(maximum_wo_error, wo_error)
            visual_alpha = alpha[torch.tensor(groups["all_visual"], dtype=torch.long)]
            visual_mass = float(visual_alpha.sum().item())
            visual_distribution = visual_alpha / visual_mass if visual_mass > 0 else torch.zeros_like(visual_alpha)
            visual_entropy = entropy(visual_distribution) if visual_mass > 0 else 0.0
            target_mass = float(group_metrics["target_roi"]["attention_mass"])
            competition_target = group_metrics["target_roi"]["logsumexp_final_logit"]
            competition_other = lse(final_logits[local_head], all_non_target)
            sink_metrics = {}
            global_top = int(alpha.argmax().item())
            for sink_name, sink_positions in sinks.items():
                indices = [value for value in sink_positions if value < visible]
                index_tensor = torch.tensor(indices, dtype=torch.long)
                mass = float(alpha[index_tensor].sum().item()) if indices else 0.0
                vector = (
                    (alpha[index_tensor, None] * values[index_tensor]).sum(dim=0)
                    if indices
                    else torch.zeros(head_dim)
                )
                projected = torch.nn.functional.linear(vector, wo[:, start : start + head_dim])
                sink_metrics[sink_name] = {
                    "token_count": len(indices),
                    "mass": mass,
                    "density": mass / len(indices) if indices else 0.0,
                    "contains_top_attended_position": global_top in set(indices),
                    "value_contribution_norm": float(vector.norm().item()),
                    "wo_residual_norm": float(projected.norm().item()),
                }
            head_row = {
                "base_problem_id": base,
                "example_id": example_id,
                "condition": condition,
                "target_id": role_for_head(layer, offset, logical_head)[0],
                "head_role": role_for_head(layer, offset, logical_head)[1],
                "layer_index": layer,
                "logical_query_head": logical_head,
                "kv_head": int(layer_state["query_to_kv_group"][logical_head]),
                "offset_from_E_d": offset,
                "generated_index": generated_index,
                "absolute_query_position": position,
                "q_norm": float(q_norm[local_head].item()),
                "groups": group_metrics,
                "target_competition_margin": (
                    float(competition_target - competition_other)
                    if competition_target is not None and competition_other is not None
                    else None
                ),
                "lse_all_non_target": competition_other,
                "attention_entropy_all_context": entropy(alpha),
                "attention_entropy_visual_only": visual_entropy,
                "effective_visual_support": float(math.exp(visual_entropy)),
                "target_roi_share_of_visual_attention": target_mass / visual_mass if visual_mass > 0 else None,
                "top1_visual_token_share": float(visual_distribution.max().item()) if visual_mass > 0 else None,
                "top5_visual_token_share": float(torch.topk(visual_distribution, k=min(5, visual_distribution.numel())).values.sum().item()) if visual_mass > 0 else None,
                "top_competing_positions": [
                    {
                        "position": int(source_position),
                        "token_id": int(token_ids[source_position]),
                        "token": str(tokenizer.convert_ids_to_tokens(int(token_ids[source_position]))),
                        "source_class": classify_position(int(source_position), groups),
                        "attention": float(alpha[source_position].item()),
                        "final_masked_logit": float(final_logits[local_head, source_position].item()),
                    }
                    for source_position in top_positions
                ],
                "sink_candidates": sink_metrics,
                "source_mass_sum": source_sum,
                "source_mass_absolute_error": source_error,
                "alpha_v_reconstruction_max_abs_error": alpha_error,
                "wo_reconstruction_max_abs_error": wo_error,
                "all_values_finite": bool(
                    torch.isfinite(q_norm[local_head])
                    and torch.isfinite(k_norm[local_head]).all()
                    and torch.isfinite(v_norm[local_head]).all()
                    and torch.isfinite(alpha).all()
                    and torch.isfinite(head_output[local_head]).all()
                ),
                "attention_manipulated": False,
            }
            all_finite &= bool(head_row["all_values_finite"])
            head_rows.append(head_row)

        if layer == 29:
            sets = {"causal": [11, 6, 15, 12], "noncausal_control": [0, 1, 2, 3]}
        elif layer == 28:
            sets = {"causal": [16, 0, 3, 6], "noncausal_control": [1, 2, 4, 5]}
        elif layer == 32 and offset == 0:
            sets = {"upstream_state_control": [11, 6, 15, 12]}
        else:
            sets = {"secondary_comparator": [10]}
        relevant_rows = head_rows[-len(heads) :]
        row_by_head = {int(row["logical_query_head"]): row for row in relevant_rows}
        for set_role, set_heads in sets.items():
            if not set(set_heads).issubset(row_by_head):
                continue
            set_groups = {}
            for name in REGION_NAMES:
                wo_vector = sum(per_head_wo_vectors[head][name] for head in set_heads)
                set_groups[name] = {
                    "mean_attention_mass": float(np.mean([row_by_head[head]["groups"][name]["attention_mass"] for head in set_heads])),
                    "mean_attention_density": float(np.mean([row_by_head[head]["groups"][name]["attention_density"] for head in set_heads])),
                    "mean_alpha_v_norm": float(np.mean([row_by_head[head]["groups"][name]["alpha_v_norm"] for head in set_heads])),
                    "post_wo_head_set_sum_norm": float(wo_vector.norm().item()),
                }
            set_rows.append({
                "base_problem_id": base,
                "example_id": example_id,
                "condition": condition,
                "target_id": role_for_head(layer, offset, set_heads[0])[0],
                "head_set_role": set_role,
                "layer_index": layer,
                "heads": set_heads,
                "offset_from_E_d": offset,
                "generated_index": generated_index,
                "absolute_query_position": position,
                "groups": set_groups,
                "mean_q_norm": float(np.mean([row_by_head[head]["q_norm"] for head in set_heads])),
                "mean_target_competition_margin": float(np.mean([row_by_head[head]["target_competition_margin"] for head in set_heads])),
                "mean_attention_entropy_all_context": float(np.mean([row_by_head[head]["attention_entropy_all_context"] for head in set_heads])),
                "mean_attention_entropy_visual_only": float(np.mean([row_by_head[head]["attention_entropy_visual_only"] for head in set_heads])),
                "attention_manipulated": False,
            })

    max_heads = max((record["heads"].shape[0] for record in raw_records), default=0)
    max_source = max((record["attention"].shape[1] for record in raw_records), default=0)
    payload: dict[str, np.ndarray] = {
        "offsets_from_E_d": np.asarray([int(record["offset"]) for record in raw_records], dtype=np.int64),
        "absolute_query_positions": np.asarray([int(record["position"]) for record in raw_records], dtype=np.int64),
        "valid_source_lengths": np.asarray([record["attention"].shape[1] for record in raw_records], dtype=np.int64),
        "logical_heads": np.full((len(raw_records), max_heads), -1, dtype=np.int64),
        "q_norm": np.full((len(raw_records), max_heads), np.nan, dtype=np.float32),
    }
    for metric in ("k_norm", "value_norm", "cosine", "raw_dot", "scaled_logits", "final_logits", "attention"):
        payload[metric] = np.full((len(raw_records), max_heads, max_source), np.nan, dtype=np.float32)
    for time_index, record in enumerate(raw_records):
        head_count, source_count = record["attention"].shape
        payload["logical_heads"][time_index, :head_count] = record["heads"]
        payload["q_norm"][time_index, :head_count] = record["q_norm"]
        for metric in ("k_norm", "value_norm", "cosine", "raw_dot", "scaled_logits", "final_logits", "attention"):
            payload[metric][time_index, :head_count, :source_count] = record[metric]
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(raw_path, **payload)
    audit = {
        "layer_index": layer,
        "tensor_shapes": layer_state["tensor_shapes"],
        "query_to_kv_group": layer_state["query_to_kv_group"],
        "wo_bias_present": bool(layer_state["wo_bias_present"]),
        "eager_reconstruction": layer_state["reconstruction"],
        "maximum_source_mass_absolute_error": maximum_source_mass_error,
        "maximum_alpha_v_reconstruction_absolute_error": maximum_alpha_v_error,
        "maximum_wo_reconstruction_absolute_error": maximum_wo_error,
        "all_values_finite": all_finite,
        "raw_tensor_path": str(raw_path.relative_to(ROOT)),
        "raw_tensor_granularity": "per condition, layer, temporal checkpoint, logical query head, and individual causally visible source-token position",
    }
    return head_rows, set_rows, audit


@torch.inference_mode()
def capture_condition(
    *,
    model: Any,
    prepared: dict[str, Any],
    context: Sequence[int],
    positions_by_layer: dict[int, list[int]],
    heads_by_layer: dict[int, list[int]],
    seed: int,
) -> tuple[torch.Tensor, dict[int, dict[str, Any]]]:
    capture = MultiLayerAttentionCapture(
        model=model,
        positions_by_layer=positions_by_layer,
        heads_by_layer=heads_by_layer,
    )
    with capture:
        logits = next_token_logits(
            model=model,
            prepared=prepared,
            prefix_token_ids=context,
            seed=seed,
        )
    return logits, capture.complete_states()


def tensor_state_signature(states: dict[int, dict[str, Any]]) -> list[torch.Tensor]:
    tensors: list[torch.Tensor] = []
    for layer in sorted(states):
        state = states[layer]
        tensors.extend([state["key"], state["value"]])
        for position in state["positions"]:
            row = state["rows"][position]
            tensors.extend(row[name] for name in ("query", "raw_dot", "scaled_logits", "final_logits", "attention", "head_output"))
    return tensors


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.relative_to(OUT.resolve())
    config = read_json(args.config)
    manifest = read_jsonl(args.manifest)
    if args.shard_count < 1 or not 0 <= args.shard_index < args.shard_count:
        raise ValueError("Invalid shard specification")
    manifest = manifest[args.shard_index :: args.shard_count]
    if args.max_bases:
        manifest = manifest[: args.max_bases]
    annotations = {str(row["base_problem_id"]): row for row in read_jsonl(args.annotations)}
    rois = {str(row["base_problem_id"]): row for row in read_jsonl(args.roi_mapping)}
    data = {str(row["sample_index"]): row for row in load_mathverse_rows(args.dataset_root)}
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "run_config.json", {
        "config": str(args.config.resolve()),
        "manifest": str(args.manifest.resolve()),
        "shard_index": args.shard_index,
        "shard_count": args.shard_count,
        "base_problem_ids": [str(row["base_problem_id"]) for row in manifest],
        "baseline_audit": args.baseline_audit,
        "repeat_first": args.repeat_first,
    })

    processor, model = load_runtime(args.model_checkpoint, device="cuda")
    environment = runtime_environment(args.model_checkpoint, model, 40_960)
    if "A5000" not in str(environment["gpu_name"]):
        raise RuntimeError(f"Stage 3C.1 requires A5000, observed {environment['gpu_name']}")
    observed = {
        "language_layers": int(model.config.text_config.num_hidden_layers),
        "logical_query_heads": int(model.config.text_config.num_attention_heads),
        "kv_heads": int(model.config.text_config.num_key_value_heads),
        "query_heads_per_kv_group": int(model.config.text_config.num_attention_heads // model.config.text_config.num_key_value_heads),
        "head_dimension": int(model.config.text_config.head_dim),
    }
    if observed != config["architecture_expected"]:
        raise RuntimeError(f"Architecture mismatch: {observed}")
    write_json(output_dir / "environment.json", {**environment, "architecture_observed": observed})

    completed = 0
    for item_index, item in enumerate(manifest):
        base = str(item["base_problem_id"])
        result_path = output_dir / "examples" / base / "result.json"
        if result_path.is_file():
            if not args.resume:
                raise FileExistsError(result_path)
            completed += 1
            print(f"[{completed}/{len(manifest)}] resume skip base {base}", flush=True)
            continue
        annotation = annotations[base]
        roi = rois[base]
        if not bool(roi["manual_overlay_validation"]["status"] == "pass"):
            raise RuntimeError(f"ROI validation did not pass for base {base}")
        context = [int(value) for value in annotation["history_before_ed_token_ids"]]
        ed = int(annotation["ed_generated_index"])
        if len(context) != ed:
            raise RuntimeError(f"E_d history mismatch for base {base}")
        source_row = data[str(item["example_id"])]
        prepared: dict[str, dict[str, Any]] = {}
        metadata: dict[str, dict[str, Any]] = {}
        for condition, path in condition_paths(base).items():
            prepared[condition], metadata[condition] = prepare_custom_image(
                processor, source_row, path, device="cuda"
            )
        prompt_ids = [metadata[condition]["prompt_token_ids"] for condition in CONDITIONS]
        visual_positions = [metadata[condition]["visual_token_indices"] for condition in CONDITIONS]
        grids = [metadata[condition]["image_grid_thw"] for condition in CONDITIONS]
        layout_exact = bool(
            all(value == prompt_ids[0] for value in prompt_ids[1:])
            and all(value == visual_positions[0] for value in visual_positions[1:])
            and all(value == grids[0] for value in grids[1:])
            and visual_positions[0] == roi["absolute_source_groups"]["V_all"]
        )
        if not layout_exact:
            raise RuntimeError(f"Frozen four-condition/ROI layout mismatch for base {base}")
        question = str(source_row.get("query_cot") or source_row.get("question") or "")
        token_groups = build_token_groups(
            prompt_token_ids=prompt_ids[0],
            visual_token_indices=visual_positions[0],
            question_token_ids=processor.tokenizer.encode(question, add_special_tokens=False),
        )
        prompt_length = len(prompt_ids[0])
        positions_by_layer, heads_by_layer = requested_layout(prompt_length, ed)
        full_token_ids = [*prompt_ids[0], *context]
        head_rows: list[dict[str, Any]] = []
        set_rows: list[dict[str, Any]] = []
        condition_audits: dict[str, Any] = {}
        instrumentation: dict[str, Any] | None = None
        determinism: dict[str, Any] | None = None
        started = time.perf_counter()
        for condition in CONDITIONS:
            baseline_logits = None
            if args.baseline_audit and item_index == 0 and condition == "O":
                baseline_logits = next_token_logits(
                    model=model,
                    prepared=prepared[condition],
                    prefix_token_ids=context,
                    seed=int(config["seed"]),
                )
            logits, states = capture_condition(
                model=model,
                prepared=prepared[condition],
                context=context,
                positions_by_layer=positions_by_layer,
                heads_by_layer=heads_by_layer,
                seed=int(config["seed"]),
            )
            if baseline_logits is not None:
                error = float((baseline_logits - logits).abs().max().item())
                instrumentation = {
                    "condition": condition,
                    "maximum_logit_absolute_error": error,
                    "tolerance": float(config["instrumentation_logit_tolerance"]),
                    "passed": error <= float(config["instrumentation_logit_tolerance"]),
                }
            if args.repeat_first and item_index == 0 and condition == "O":
                repeat_logits, repeat_states = capture_condition(
                    model=model,
                    prepared=prepared[condition],
                    context=context,
                    positions_by_layer=positions_by_layer,
                    heads_by_layer=heads_by_layer,
                    seed=int(config["seed"]),
                )
                pairs = zip(tensor_state_signature(states), tensor_state_signature(repeat_states), strict=True)
                tensor_errors = [float((left - right).abs().max().item()) for left, right in pairs]
                logit_error = float((logits - repeat_logits).abs().max().item())
                maximum = max([logit_error, *tensor_errors], default=logit_error)
                determinism = {
                    "maximum_absolute_error": maximum,
                    "logit_maximum_absolute_error": logit_error,
                    "exact": maximum == 0.0,
                    "passed": maximum <= float(config["deterministic_repeat_tolerance"]),
                }
            condition_audits[condition] = {}
            for layer, state in states.items():
                raw_root = (
                    output_dir / "raw_tensors"
                    if any(part.startswith("smoke") for part in output_dir.parts)
                    else OUT / "extraction/raw_tensors"
                )
                raw_path = raw_root / base / f"{condition}_layer{layer}.npz"
                rows, aggregates, audit = analyze_layer(
                    base=base,
                    example_id=str(item["example_id"]),
                    condition=condition,
                    layer_state=state,
                    prompt_length=prompt_length,
                    ed=ed,
                    question_positions=token_groups["Q"],
                    roi=roi,
                    token_ids=full_token_ids,
                    tokenizer=processor.tokenizer,
                    raw_path=raw_path,
                )
                head_rows.extend(rows)
                set_rows.extend(aggregates)
                condition_audits[condition][str(layer)] = audit
            del states, logits
            gc.collect()
            torch.cuda.empty_cache()
        elapsed = time.perf_counter() - started
        result = {
            "base_problem_id": base,
            "example_id": str(item["example_id"]),
            "evidence_type": item["edit_tier"],
            "prefix_sha256": item["prefix_sha256"],
            "ed_generated_index": ed,
            "conditions": list(CONDITIONS),
            "condition_layout_exact": layout_exact,
            "question_positions": token_groups["Q"],
            "roi_source_groups": roi["absolute_source_groups"],
            "head_rows": head_rows,
            "head_set_rows": set_rows,
            "audits": condition_audits,
            "instrumentation_faithfulness": instrumentation,
            "deterministic_repeat": determinism,
            "runtime_seconds": elapsed,
            "selection_used_stage3c1_attention": False,
            "attention_manipulated": False,
        }
        write_json(result_path, result)
        completed += 1
        print(f"[{completed}/{len(manifest)}] completed base {base} seconds={elapsed:.1f}", flush=True)
        del prepared, metadata, result, head_rows, set_rows
        gc.collect()
        torch.cuda.empty_cache()
    print(json.dumps({"completed": completed, "requested": len(manifest)}, indent=2), flush=True)


if __name__ == "__main__":
    main()
