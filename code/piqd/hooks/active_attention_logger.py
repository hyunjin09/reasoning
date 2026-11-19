from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Callable

import torch
import torch.nn.functional as F
from transformers.models.qwen3_vl.modeling_qwen3_vl import apply_rotary_pos_emb


@dataclass
class ActiveAttentionRecord:
    step: int
    token_id: int | None
    similarity: float
    entropy: float
    top_active_indices: list[int]


@dataclass
class ActiveBankAttentionLogger:
    layer_idx: int
    visual_positions: torch.Tensor
    active_visual_indices: list[int]
    generated_step: int = -1
    anchor_probs: torch.Tensor | None = None
    k_active: torch.Tensor | None = None
    latest_visual_scores: torch.Tensor | None = None
    records: list[ActiveAttentionRecord] = field(default_factory=list)

    _module: Any = None
    _original_forward: Callable[..., Any] | None = None
    _current_token_id: int | None = None

    def attach(self, model: Any) -> None:
        if self._original_forward is not None:
            return
        self._module = model.model.language_model.layers[self.layer_idx].self_attn
        self._original_forward = self._module.forward
        logger = self

        def wrapped_forward(hidden_states, position_embeddings, attention_mask, past_key_values=None, **kwargs):
            logger.capture_qk(logger._module, hidden_states, position_embeddings)
            return logger._original_forward(
                hidden_states,
                position_embeddings,
                attention_mask,
                past_key_values=past_key_values,
                **kwargs,
            )

        self._module.forward = wrapped_forward

    def detach(self) -> None:
        if self._module is not None and self._original_forward is not None:
            self._module.forward = self._original_forward
        self._module = None
        self._original_forward = None

    def set_current_token(self, token_id: int | None) -> None:
        self._current_token_id = token_id

    def capture_qk(self, module: Any, hidden_states: torch.Tensor, position_embeddings) -> None:
        with torch.no_grad():
            input_shape = hidden_states.shape[:-1]
            hidden_shape = (*input_shape, -1, module.head_dim)
            query_states = module.q_norm(module.q_proj(hidden_states).view(hidden_shape)).transpose(1, 2)
            key_states = module.k_norm(module.k_proj(hidden_states).view(hidden_shape)).transpose(1, 2)
            cos, sin = position_embeddings
            query_states, key_states = apply_rotary_pos_emb(query_states, key_states, cos, sin)

            query_states = _mean_query_groups(query_states, key_states.shape[1])
            q_last = query_states[0, :, -1, :].detach()

            if hidden_states.shape[1] > 1:
                positions = self.visual_positions.to(key_states.device)
                self.k_active = key_states[0, :, positions, :].detach()
                probs, scores = _active_distribution(q_last, self.k_active, return_scores=True)
                self.anchor_probs = probs.detach()
                self.latest_visual_scores = scores.detach().mean(dim=0).float().cpu()
                self.records.append(_make_record(-1, self._current_token_id, probs, probs, self.active_visual_indices))
                return

            if self.k_active is None or self.anchor_probs is None:
                return
            probs, _ = _active_distribution(q_last, self.k_active, return_scores=True)
            self.generated_step += 1
            self.records.append(
                _make_record(
                    self.generated_step,
                    self._current_token_id,
                    probs,
                    self.anchor_probs.to(probs.device),
                    self.active_visual_indices,
                )
            )

    def generated_records(self) -> list[dict[str, Any]]:
        return [
            {
                "step": record.step,
                "token_id": record.token_id,
                "risd_similarity_active": record.similarity,
                "active_attention_entropy": record.entropy,
                "active_top_indices": record.top_active_indices,
            }
            for record in self.records
            if record.step >= 0
        ]


def _mean_query_groups(query_states: torch.Tensor, num_kv_heads: int) -> torch.Tensor:
    num_query_heads = query_states.shape[1]
    if num_query_heads == num_kv_heads:
        return query_states
    groups = num_query_heads // num_kv_heads
    return query_states.view(query_states.shape[0], num_kv_heads, groups, query_states.shape[2], query_states.shape[3]).mean(dim=2)


def _active_distribution(q_heads: torch.Tensor, k_active: torch.Tensor, return_scores: bool = False):
    scores = torch.einsum("hd,hnd->hn", q_heads.float(), k_active.float()) / math.sqrt(q_heads.shape[-1])
    probs_by_head = torch.softmax(scores, dim=-1)
    probs = probs_by_head.mean(dim=0)
    probs = probs / probs.sum().clamp_min(1e-12)
    if return_scores:
        return probs, scores
    return probs


def _make_record(
    step: int,
    token_id: int | None,
    probs: torch.Tensor,
    anchor_probs: torch.Tensor,
    active_visual_indices: list[int],
) -> ActiveAttentionRecord:
    similarity = F.cosine_similarity(probs.float(), anchor_probs.float(), dim=0).item()
    entropy = (-(probs.float() * probs.float().clamp_min(1e-12).log()).sum()).item()
    top_k = min(5, probs.numel())
    top_local = torch.topk(probs.float(), k=top_k).indices.tolist()
    top_indices = [active_visual_indices[idx] for idx in top_local]
    return ActiveAttentionRecord(
        step=step,
        token_id=token_id,
        similarity=float(similarity),
        entropy=float(entropy),
        top_active_indices=top_indices,
    )

