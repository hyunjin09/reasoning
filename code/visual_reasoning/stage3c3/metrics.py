"""Routing and Value-influx summaries for Stage 3C.3."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any

import torch

from visual_reasoning.stage3c1.metrics import _repeat_kv


def _group_indices(
    groups: Mapping[str, Sequence[int]], *, source_length: int
) -> dict[str, list[int]]:
    result = {str(name): sorted({int(value) for value in values}) for name, values in groups.items()}
    for name, values in result.items():
        if not values:
            raise ValueError(f"Routing group {name} is empty")
        if values[0] < 0 or values[-1] >= source_length:
            raise ValueError(f"Routing group {name} is outside the visible source sequence")
    return result


def summarize_routing_state(
    state: Mapping[str, Any],
    *,
    groups: Mapping[str, Sequence[int]],
    selected_heads: Sequence[int],
) -> dict[str, Any]:
    """Summarize QK, probability, alpha-V, and post-W_O routing readouts."""

    query = state["post_rope_query"].detach()
    key = state["key"].detach()
    value = state["value"].detach()
    attention = state["attention"].detach()
    wo = state["wo_weight"].detach()
    if query.ndim != 3 or key.ndim != 4 or value.shape != key.shape or attention.ndim != 3:
        raise ValueError("Unexpected query/K/V/attention layout")
    if int(query.shape[0]) != 1 or int(key.shape[0]) != 1 or int(attention.shape[0]) != 1:
        raise ValueError("Stage 3C.3 expects batch size one")
    repeated_key = _repeat_kv(key, int(state["num_key_value_groups"]))[0]
    repeated_value = _repeat_kv(value, int(state["num_key_value_groups"]))[0]
    query = query[0]
    attention = attention[0]
    visible_source_tokens = int(attention.shape[-1])
    stored_kv_tokens = int(repeated_key.shape[1])
    if visible_source_tokens > stored_kv_tokens:
        raise ValueError("Attention exposes more source positions than stored K/V")
    repeated_key = repeated_key[:, :visible_source_tokens, :]
    repeated_value = repeated_value[:, :visible_source_tokens, :]
    if query.shape[0] != repeated_key.shape[0] or attention.shape != repeated_key.shape[:2]:
        raise ValueError("Logical query heads do not align with expanded K/V and attention")
    heads = sorted({int(value) for value in selected_heads})
    if not heads or heads[0] < 0 or heads[-1] >= int(query.shape[0]):
        raise ValueError("Selected logical query head is outside the model")
    validated = _group_indices(groups, source_length=int(attention.shape[-1]))
    entropy = -(attention.float().clamp_min(1e-30) * attention.float().clamp_min(1e-30).log()).sum(dim=-1)
    head_dimension = int(query.shape[-1])
    per_head = []
    for head in heads:
        head_groups: dict[str, Any] = {}
        for name, indices in validated.items():
            idx = torch.tensor(indices, dtype=torch.long, device=query.device)
            keys = repeated_key[head, idx]
            values = repeated_value[head, idx]
            alpha = attention[head, idx]
            raw = torch.matmul(keys, query[head])
            scaled = raw * float(state["scaling"])
            cosine = raw.float() / (keys.float().norm(dim=-1) * query[head].float().norm()).clamp_min(1e-30)
            alpha_v = (alpha[:, None].to(values.dtype) * values).sum(dim=0)
            start = head * head_dimension
            post_wo = torch.nn.functional.linear(alpha_v.to(wo.dtype), wo[:, start:start + head_dimension])
            head_groups[name] = {
                "token_count": len(indices),
                "mean_qk_cosine": float(cosine.float().mean().item()),
                "mean_raw_qk_dot": float(raw.float().mean().item()),
                "mean_scaled_logit": float(scaled.float().mean().item()),
                "attention_mass": float(alpha.float().sum().item()),
                "attention_density": float(alpha.float().mean().item()),
                "alpha_v_vector": alpha_v.detach().float().cpu().tolist(),
                "alpha_v_norm": float(alpha_v.float().norm().item()),
                "post_wo_norm": float(post_wo.float().norm().item()),
                "_post_wo": post_wo,
            }
        per_head.append({
            "logical_query_head": head,
            "attention_entropy": float(entropy[head].item()),
            "groups": head_groups,
        })

    aggregate_groups: dict[str, Any] = {}
    for name, indices in validated.items():
        rows = [row["groups"][name] for row in per_head]
        post_sum = torch.stack([row["_post_wo"] for row in rows]).sum(dim=0)
        aggregate_groups[name] = {
            "token_count": len(indices),
            "mean_qk_cosine": float(sum(row["mean_qk_cosine"] for row in rows) / len(rows)),
            "mean_raw_qk_dot": float(sum(row["mean_raw_qk_dot"] for row in rows) / len(rows)),
            "mean_scaled_logit": float(sum(row["mean_scaled_logit"] for row in rows) / len(rows)),
            "mean_attention_mass": float(sum(row["attention_mass"] for row in rows) / len(rows)),
            "mean_attention_density": float(sum(row["attention_density"] for row in rows) / len(rows)),
            "mean_alpha_v_norm": float(sum(row["alpha_v_norm"] for row in rows) / len(rows)),
            "mean_post_wo_norm": float(sum(row["post_wo_norm"] for row in rows) / len(rows)),
            "head_set_post_wo_sum_norm": float(post_sum.float().norm().item()),
        }
    for row in per_head:
        for metrics in row["groups"].values():
            del metrics["_post_wo"]
    required = {"T", "M", "I", "sink"}
    if not required.issubset(aggregate_groups):
        raise ValueError("Routing summary requires T, M, I, and sink groups")
    result = {
        "selected_heads": heads,
        "visible_source_token_count": visible_source_tokens,
        "stored_kv_token_count": stored_kv_tokens,
        "groups": aggregate_groups,
        "mean_attention_entropy": float(sum(row["attention_entropy"] for row in per_head) / len(per_head)),
        "RDS_T_vs_M": aggregate_groups["T"]["mean_scaled_logit"] - aggregate_groups["M"]["mean_scaled_logit"],
        "ADG_T_vs_M": aggregate_groups["T"]["mean_attention_density"] - aggregate_groups["M"]["mean_attention_density"],
        "RDS_T_vs_I": aggregate_groups["T"]["mean_scaled_logit"] - aggregate_groups["I"]["mean_scaled_logit"],
        "ADG_T_vs_I": aggregate_groups["T"]["mean_attention_density"] - aggregate_groups["I"]["mean_attention_density"],
        "per_head": per_head,
    }
    scalars = [
        result["RDS_T_vs_M"], result["ADG_T_vs_M"], result["RDS_T_vs_I"], result["ADG_T_vs_I"],
        *[value for metrics in aggregate_groups.values() for key, value in metrics.items() if key != "token_count"],
    ]
    result["all_values_finite"] = all(math.isfinite(float(value)) for value in scalars)
    return result


__all__ = ["summarize_routing_state"]
