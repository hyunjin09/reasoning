"""Exact selected-head query intervention for Qwen3-VL eager Attention."""

from __future__ import annotations

import time
from collections.abc import Iterable, Sequence
from contextlib import AbstractContextManager
from types import MethodType
from typing import Any

import torch

from visual_reasoning.stage0.modeling import _reset_generation_state
from visual_reasoning.stage2b.runtime import extend_prepared_inputs
from visual_reasoning.stage3a.runtime import summarize_candidate_log_probs
from visual_reasoning.stage3a.runtime import next_token_logits
from visual_reasoning.stage3b4.runtime import absolute_intervention_position
from visual_reasoning.stage3b5.boundaries import CurrentPositionBoundaryPatch
from visual_reasoning.stage3b6.heads import _attention_module, _project_attention_output


def splice_current_query_heads(
    recipient_query: torch.Tensor,
    donor_current_query: torch.Tensor,
    *,
    recipient_position: int,
    selected_heads: Sequence[int],
) -> tuple[torch.Tensor, dict[str, Any]]:
    """Replace selected logical Q heads at exactly one recipient position."""

    if recipient_query.ndim != 4:
        raise ValueError("Recipient query must be [batch, head, sequence, dimension]")
    expected = (
        int(recipient_query.shape[0]),
        int(recipient_query.shape[1]),
        int(recipient_query.shape[3]),
    )
    if donor_current_query.ndim != 3 or tuple(donor_current_query.shape) != expected:
        raise ValueError("Donor current query must match recipient [batch, head, dimension]")
    position = int(recipient_position)
    if position < 0 or position >= int(recipient_query.shape[2]):
        raise ValueError("Recipient position is outside the query sequence")
    heads = sorted({int(value) for value in selected_heads})
    if not heads or heads[0] < 0 or heads[-1] >= int(recipient_query.shape[1]):
        raise ValueError("Selected logical query head is outside the model")

    patched = recipient_query.clone()
    patched[:, heads, position, :] = donor_current_query[:, heads, :].to(
        device=patched.device, dtype=patched.dtype
    )
    delta = patched - recipient_query
    per_head = delta.abs().amax(dim=(0, 2, 3))
    per_position = delta.abs().amax(dim=(0, 1, 3))
    changed_heads = torch.nonzero(per_head > 0, as_tuple=False).flatten().tolist()
    changed_positions = torch.nonzero(per_position > 0, as_tuple=False).flatten().tolist()
    nonselected = [head for head in range(int(delta.shape[1])) if head not in heads]
    nonselected_error = (
        float(delta[:, nonselected, :, :].abs().max().item()) if nonselected else 0.0
    )
    return patched, {
        "selected_query_heads": heads,
        "changed_query_heads": [int(value) for value in changed_heads],
        "changed_sequence_positions": [int(value) for value in changed_positions],
        "nonselected_head_max_abs_delta": nonselected_error,
        "selected_head_max_abs_delta": float(delta[:, heads, position, :].abs().max().item()),
        "recipient_query_shape": list(recipient_query.shape),
        "donor_current_query_shape": list(donor_current_query.shape),
    }


def evidence_suffix_logit_rows(
    *, prompt_length: int, prefix_length: int, bridge_length: int, suffix_length: int
) -> list[int]:
    """Rows that predict only the divergent suffix after a native bridge."""

    if prompt_length <= 0 or prefix_length <= 0 or bridge_length < 0 or suffix_length <= 0:
        raise ValueError("Invalid prompt/prefix/bridge/suffix lengths")
    start = int(prompt_length) + int(prefix_length) + int(bridge_length) - 1
    return list(range(start, start + int(suffix_length)))


@torch.inference_mode()
def score_evidence_suffix(
    *,
    model: Any,
    prepared: dict[str, Any],
    prefix_token_ids: Iterable[int],
    bridge_token_ids: Iterable[int],
    suffix_token_ids: Sequence[int],
    seed: int,
) -> dict[str, Any]:
    """Score the evidence suffix while retaining the state's native bridge."""

    prefix = [int(value) for value in prefix_token_ids]
    bridge = [int(value) for value in bridge_token_ids]
    suffix = [int(value) for value in suffix_token_ids]
    prompt_length = int(prepared["input_ids"].shape[1])
    rows = evidence_suffix_logit_rows(
        prompt_length=prompt_length,
        prefix_length=len(prefix),
        bridge_length=len(bridge),
        suffix_length=len(suffix),
    )
    batch = extend_prepared_inputs(prepared, [*prefix, *bridge, *suffix])
    row_tensor = torch.tensor(rows, dtype=torch.long, device=batch["input_ids"].device)
    target = torch.tensor(suffix, dtype=torch.long, device=batch["input_ids"].device)
    _reset_generation_state(model, seed=int(seed))
    started = time.perf_counter()
    output = model(**batch, use_cache=False, return_dict=True, logits_to_keep=row_tensor)
    log_probs = torch.log_softmax(output.logits[0].float(), dim=-1)
    selected = log_probs.gather(-1, target[:, None]).squeeze(-1)
    if torch.cuda.is_available():
        torch.cuda.synchronize()
    summary = summarize_candidate_log_probs(selected.detach().cpu().tolist())
    summary.update({
        "candidate_token_ids": suffix,
        "native_bridge_token_ids": bridge,
        "logit_rows": rows,
        "runtime_seconds": time.perf_counter() - started,
        "finite": bool(torch.isfinite(selected).all().item()),
        "distribution_definition": "raw model next-token distribution; only divergent suffix rows are summarized",
    })
    del output, log_probs, selected
    return summary


def _projection_parts(
    module: torch.nn.Module,
    hidden_states: torch.Tensor,
    position_embeddings: tuple[torch.Tensor, torch.Tensor],
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    """Return pre-RoPE Q/K, post-RoPE Q/K, and projected V."""

    from transformers.models.qwen3_vl import modeling_qwen3_vl as qwen_impl

    input_shape = hidden_states.shape[:-1]
    hidden_shape = (*input_shape, -1, int(module.head_dim))
    pre_query = module.q_norm(module.q_proj(hidden_states).view(hidden_shape)).transpose(1, 2)
    pre_key = module.k_norm(module.k_proj(hidden_states).view(hidden_shape)).transpose(1, 2)
    value = module.v_proj(hidden_states).view(hidden_shape).transpose(1, 2)
    query, key = qwen_impl.apply_rotary_pos_emb(pre_query, pre_key, *position_embeddings)
    return pre_query, pre_key, query, key, value


def _run_attention(
    module: torch.nn.Module,
    query: torch.Tensor,
    key: torch.Tensor,
    value: torch.Tensor,
    attention_mask: torch.Tensor | None,
    kwargs: dict[str, Any],
) -> tuple[torch.Tensor, torch.Tensor]:
    from transformers.models.qwen3_vl import modeling_qwen3_vl as qwen_impl

    interface = qwen_impl.ALL_ATTENTION_FUNCTIONS.get_interface(
        module.config._attn_implementation, qwen_impl.eager_attention_forward
    )
    output, weights = interface(
        module,
        query,
        key,
        value,
        attention_mask,
        dropout=0.0 if not module.training else module.attention_dropout,
        scaling=module.scaling,
        **kwargs,
    )
    if weights is None:
        raise RuntimeError("Stage 3C.3 requires eager Attention weights")
    return output, weights


class CurrentHPreCapture(AbstractContextManager["CurrentHPreCapture"]):
    """Capture the raw decoder-block input at one current sequence position."""

    def __init__(self, *, model: Any, layer_index: int, position: int) -> None:
        self.layer_index = int(layer_index)
        self.position = int(position)
        self.layer = model.model.language_model.layers[self.layer_index]
        self.state: torch.Tensor | None = None
        self._handle: Any | None = None

    def _hook(self, module: torch.nn.Module, args: tuple[Any, ...]) -> None:
        hidden = args[0]
        if self.state is not None:
            raise RuntimeError("h_pre capture executed more than once")
        if hidden.ndim != 3 or not 0 <= self.position < int(hidden.shape[1]):
            raise ValueError("h_pre capture position is outside the sequence")
        self.state = hidden[:, self.position, :].detach().clone()

    def __enter__(self) -> "CurrentHPreCapture":
        self._handle = self.layer.register_forward_pre_hook(self._hook)
        return self

    def complete_state(self) -> torch.Tensor:
        if self.state is None:
            raise RuntimeError("h_pre capture did not execute")
        return self.state

    def close(self) -> None:
        if self._handle is not None:
            self._handle.remove()
            self._handle = None

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()


class CurrentHPreMultiCapture(AbstractContextManager["CurrentHPreMultiCapture"]):
    """Capture raw block inputs at several frozen positions in one forward pass."""

    def __init__(self, *, model: Any, layer_index: int, positions: dict[str, int]) -> None:
        self.layer = model.model.language_model.layers[int(layer_index)]
        self.positions = {str(name): int(position) for name, position in positions.items()}
        self.states: dict[str, torch.Tensor] | None = None
        self._handle: Any | None = None

    def _hook(self, module: torch.nn.Module, args: tuple[Any, ...]) -> None:
        hidden = args[0]
        if self.states is not None:
            raise RuntimeError("multi-position h_pre capture executed more than once")
        if hidden.ndim != 3 or any(
            position < 0 or position >= int(hidden.shape[1])
            for position in self.positions.values()
        ):
            raise ValueError("multi-position h_pre capture position is outside the sequence")
        self.states = {
            name: hidden[:, position, :].detach().clone()
            for name, position in self.positions.items()
        }

    def __enter__(self) -> "CurrentHPreMultiCapture":
        self._handle = self.layer.register_forward_pre_hook(self._hook)
        return self

    def complete_states(self) -> dict[str, torch.Tensor]:
        if self.states is None:
            raise RuntimeError("multi-position h_pre capture did not execute")
        return self.states

    def close(self) -> None:
        if self._handle is not None:
            self._handle.remove()
            self._handle = None

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()


class AttentionStateCapture(AbstractContextManager["AttentionStateCapture"]):
    """Transparently capture native pre/post-RoPE Q and recipient K/V."""

    def __init__(self, *, model: Any, layer_index: int, position: int) -> None:
        self.layer_index = int(layer_index)
        self.position = int(position)
        self.module = _attention_module(model, self.layer_index)
        self.state: dict[str, Any] | None = None
        self._original_forward: Any | None = None

    def _run(
        self,
        module: torch.nn.Module,
        hidden_states: torch.Tensor,
        position_embeddings: tuple[torch.Tensor, torch.Tensor],
        attention_mask: torch.Tensor | None,
        past_key_values: Any | None = None,
        **kwargs: Any,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        if self.state is not None:
            raise RuntimeError("Attention state capture executed more than once")
        pre_q, pre_k, query, key, value = _projection_parts(module, hidden_states, position_embeddings)
        if past_key_values is not None:
            key, value = past_key_values.update(key, value, int(module.layer_idx))
        output, weights = _run_attention(module, query, key, value, attention_mask, kwargs)
        if not 0 <= self.position < int(query.shape[2]):
            raise ValueError("Attention capture position is outside the sequence")
        self.state = {
            "pre_rope_query": pre_q[:, :, self.position, :].detach().clone(),
            "post_rope_query": query[:, :, self.position, :].detach().clone(),
            "key": key.detach().clone(),
            "value": value.detach().clone(),
            "attention": weights[:, :, self.position, : self.position + 1].detach().clone(),
            "head_output": output[:, self.position, :, :].detach().clone(),
            "wo_weight": module.o_proj.weight.detach().clone(),
            "scaling": float(module.scaling),
            "num_key_value_groups": int(module.num_key_value_groups),
            "position": self.position,
            "layer_index": self.layer_index,
            "tensor_shapes": {
                "pre_rope_query": list(pre_q.shape),
                "post_rope_query": list(query.shape),
                "key": list(key.shape),
                "value": list(value.shape),
                "attention": list(weights.shape),
                "head_output": list(output.shape),
            },
        }
        return _project_attention_output(module, output, hidden_states), weights

    def __enter__(self) -> "AttentionStateCapture":
        self._original_forward = self.module.forward

        def forward(
            module: torch.nn.Module,
            hidden_states: torch.Tensor,
            position_embeddings: tuple[torch.Tensor, torch.Tensor],
            attention_mask: torch.Tensor | None,
            past_key_values: Any | None = None,
            **kwargs: Any,
        ):
            return self._run(module, hidden_states, position_embeddings, attention_mask, past_key_values, **kwargs)

        self.module.forward = MethodType(forward, self.module)
        return self

    def complete_state(self) -> dict[str, Any]:
        if self.state is None:
            raise RuntimeError("Attention state capture did not execute")
        return self.state

    def close(self) -> None:
        if self._original_forward is not None:
            self.module.forward = self._original_forward
            self._original_forward = None

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()


class AttentionStateMultiCapture(AbstractContextManager["AttentionStateMultiCapture"]):
    """Capture multiple current-position routing states in one exact candidate pass."""

    def __init__(self, *, model: Any, layer_index: int, positions: dict[str, int]) -> None:
        self.layer_index = int(layer_index)
        self.positions = {str(name): int(position) for name, position in positions.items()}
        self.module = _attention_module(model, self.layer_index)
        self.states: dict[str, dict[str, Any]] | None = None
        self._original_forward: Any | None = None

    def _run(
        self,
        module: torch.nn.Module,
        hidden_states: torch.Tensor,
        position_embeddings: tuple[torch.Tensor, torch.Tensor],
        attention_mask: torch.Tensor | None,
        past_key_values: Any | None = None,
        **kwargs: Any,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        if self.states is not None:
            raise RuntimeError("multi-position Attention capture executed more than once")
        pre_q, pre_k, query, key, value = _projection_parts(module, hidden_states, position_embeddings)
        if past_key_values is not None:
            key, value = past_key_values.update(key, value, int(module.layer_idx))
        output, weights = _run_attention(module, query, key, value, attention_mask, kwargs)
        if any(position < 0 or position >= int(query.shape[2]) for position in self.positions.values()):
            raise ValueError("multi-position Attention capture position is outside the sequence")
        key_snapshot = key.detach().clone()
        value_snapshot = value.detach().clone()
        self.states = {}
        for name, position in self.positions.items():
            self.states[name] = {
                "pre_rope_query": pre_q[:, :, position, :].detach().clone(),
                "post_rope_query": query[:, :, position, :].detach().clone(),
                "key": key_snapshot,
                "value": value_snapshot,
                "attention": weights[:, :, position, : position + 1].detach().clone(),
                "head_output": output[:, position, :, :].detach().clone(),
                "wo_weight": module.o_proj.weight.detach(),
                "scaling": float(module.scaling),
                "num_key_value_groups": int(module.num_key_value_groups),
                "position": position,
                "layer_index": self.layer_index,
                "tensor_shapes": {
                    "pre_rope_query": list(pre_q.shape),
                    "post_rope_query": list(query.shape),
                    "key": list(key.shape),
                    "value": list(value.shape),
                    "attention": list(weights.shape),
                    "head_output": list(output.shape),
                },
            }
        return _project_attention_output(module, output, hidden_states), weights

    def __enter__(self) -> "AttentionStateMultiCapture":
        self._original_forward = self.module.forward

        def forward(
            module: torch.nn.Module,
            hidden_states: torch.Tensor,
            position_embeddings: tuple[torch.Tensor, torch.Tensor],
            attention_mask: torch.Tensor | None,
            past_key_values: Any | None = None,
            **kwargs: Any,
        ):
            return self._run(module, hidden_states, position_embeddings, attention_mask, past_key_values, **kwargs)

        self.module.forward = MethodType(forward, self.module)
        return self

    def complete_states(self) -> dict[str, dict[str, Any]]:
        if self.states is None:
            raise RuntimeError("multi-position Attention capture did not execute")
        return self.states

    def close(self) -> None:
        if self._original_forward is not None:
            self.module.forward = self._original_forward
            self._original_forward = None

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()


class SelectedHeadQueryPatch(AbstractContextManager["SelectedHeadQueryPatch"]):
    """Patch selected current-position Q heads while keeping recipient K/V exact."""

    FORMS = {"direct_post_rope", "content_recipient_rope"}

    def __init__(
        self,
        *,
        model: Any,
        layer_index: int,
        position: int,
        selected_heads: Sequence[int],
        donor_pre_rope_query: torch.Tensor,
        donor_post_rope_query: torch.Tensor,
        formulation: str,
    ) -> None:
        self.layer_index = int(layer_index)
        self.position = int(position)
        self.selected_heads = sorted({int(value) for value in selected_heads})
        self.donor_pre = donor_pre_rope_query
        self.donor_post = donor_post_rope_query
        if formulation not in self.FORMS:
            raise ValueError(f"Unknown query formulation: {formulation}")
        self.formulation = formulation
        self.module = _attention_module(model, self.layer_index)
        self.state: dict[str, Any] | None = None
        self.audit: dict[str, Any] | None = None
        self._original_forward: Any | None = None

    def _run(
        self,
        module: torch.nn.Module,
        hidden_states: torch.Tensor,
        position_embeddings: tuple[torch.Tensor, torch.Tensor],
        attention_mask: torch.Tensor | None,
        past_key_values: Any | None = None,
        **kwargs: Any,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        if self.state is not None:
            raise RuntimeError("Query patch executed more than once")
        pre_q, pre_k, native_q, native_k, value = _projection_parts(module, hidden_states, position_embeddings)
        rope_key_error = 0.0
        if self.formulation == "direct_post_rope":
            patched_q, splice_audit = splice_current_query_heads(
                native_q,
                self.donor_post,
                recipient_position=self.position,
                selected_heads=self.selected_heads,
            )
        else:
            from transformers.models.qwen3_vl import modeling_qwen3_vl as qwen_impl

            patched_pre_q, splice_audit = splice_current_query_heads(
                pre_q,
                self.donor_pre,
                recipient_position=self.position,
                selected_heads=self.selected_heads,
            )
            patched_q, repeated_native_k = qwen_impl.apply_rotary_pos_emb(
                patched_pre_q, pre_k, *position_embeddings
            )
            rope_key_error = float((repeated_native_k - native_k).abs().max().item())
        if past_key_values is not None:
            native_k, value = past_key_values.update(native_k, value, int(module.layer_idx))
        native_output, native_weights = _run_attention(
            module, native_q, native_k, value, attention_mask, kwargs
        )
        patched_output, patched_weights = _run_attention(
            module, patched_q, native_k, value, attention_mask, kwargs
        )
        heads = self.selected_heads
        nonselected = [head for head in range(int(native_q.shape[1])) if head not in heads]
        nonselected_attention_error = (
            float((patched_weights[:, nonselected] - native_weights[:, nonselected]).abs().max().item())
            if nonselected else 0.0
        )
        nonselected_output_error = (
            float((patched_output[:, :, nonselected] - native_output[:, :, nonselected]).abs().max().item())
            if nonselected else 0.0
        )
        self.audit = {
            "layer_index": self.layer_index,
            "recipient_position": self.position,
            "formulation": self.formulation,
            **splice_audit,
            "recipient_key_max_abs_delta": 0.0,
            "recipient_value_max_abs_delta": 0.0,
            "content_rope_key_reconstruction_max_abs_error": rope_key_error,
            "nonselected_attention_max_abs_delta": nonselected_attention_error,
            "nonselected_head_output_max_abs_delta": nonselected_output_error,
            "visual_kv_recipient_native": True,
            "all_nonvisual_kv_recipient_native": True,
            "past_cache_recipient_native": True,
        }
        self.state = {
            "pre_rope_query": pre_q[:, :, self.position, :].detach().clone(),
            "post_rope_query": patched_q[:, :, self.position, :].detach().clone(),
            "native_post_rope_query": native_q[:, :, self.position, :].detach().clone(),
            "key": native_k.detach().clone(),
            "value": value.detach().clone(),
            "attention": patched_weights[:, :, self.position, : self.position + 1].detach().clone(),
            "native_attention": native_weights[:, :, self.position, : self.position + 1].detach().clone(),
            "head_output": patched_output[:, self.position, :, :].detach().clone(),
            "native_head_output": native_output[:, self.position, :, :].detach().clone(),
            "wo_weight": module.o_proj.weight.detach().clone(),
            "scaling": float(module.scaling),
            "num_key_value_groups": int(module.num_key_value_groups),
            "position": self.position,
            "layer_index": self.layer_index,
        }
        return _project_attention_output(module, patched_output, hidden_states), patched_weights

    def __enter__(self) -> "SelectedHeadQueryPatch":
        self._original_forward = self.module.forward

        def forward(
            module: torch.nn.Module,
            hidden_states: torch.Tensor,
            position_embeddings: tuple[torch.Tensor, torch.Tensor],
            attention_mask: torch.Tensor | None,
            past_key_values: Any | None = None,
            **kwargs: Any,
        ):
            return self._run(module, hidden_states, position_embeddings, attention_mask, past_key_values, **kwargs)

        self.module.forward = MethodType(forward, self.module)
        return self

    def complete(self) -> tuple[dict[str, Any], dict[str, Any]]:
        if self.state is None or self.audit is None:
            raise RuntimeError("Query patch did not execute")
        return self.state, self.audit

    def close(self) -> None:
        if self._original_forward is not None:
            self.module.forward = self._original_forward
            self._original_forward = None

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()


@torch.inference_mode()
def capture_native_state(
    *,
    model: Any,
    prepared: dict[str, Any],
    prefix_token_ids: Sequence[int],
    generated_index: int,
    layer_index: int,
    seed: int,
) -> dict[str, Any]:
    """Capture native Q/K/V and raw h_pre at one frozen state."""

    position = absolute_intervention_position(
        prompt_length=int(prepared["input_ids"].shape[1]),
        intervention_generated_index=int(generated_index),
    )
    attention_capture = AttentionStateCapture(
        model=model, layer_index=layer_index, position=position
    )
    hpre_capture = CurrentHPreCapture(
        model=model, layer_index=layer_index, position=position
    )
    with hpre_capture, attention_capture:
        logits = next_token_logits(
            model=model,
            prepared=prepared,
            prefix_token_ids=prefix_token_ids,
            seed=seed,
        )
    return {
        "next_token_logits": logits,
        "attention_state": attention_capture.complete_state(),
        "h_pre": hpre_capture.complete_state(),
        "absolute_position": position,
    }


def _preference(original: dict[str, Any], counterfactual: dict[str, Any]) -> dict[str, Any]:
    return {
        "original_candidate": original,
        "counterfactual_candidate": counterfactual,
        "L_o": float(original["mean_log_probability"]),
        "L_c": float(counterfactual["mean_log_probability"]),
        "D": float(original["mean_log_probability"] - counterfactual["mean_log_probability"]),
        "finite": bool(original["finite"] and counterfactual["finite"]),
    }


@torch.inference_mode()
def score_native_preference(
    *,
    model: Any,
    prepared: dict[str, Any],
    prefix_token_ids: Sequence[int],
    bridge_token_ids: Sequence[int],
    original_suffix_ids: Sequence[int],
    counterfactual_suffix_ids: Sequence[int],
    generated_index: int,
    layer_index: int,
    seed: int,
) -> dict[str, Any]:
    """Score a native state and retain its current-position routing tensors."""

    position = absolute_intervention_position(
        prompt_length=int(prepared["input_ids"].shape[1]),
        intervention_generated_index=int(generated_index),
    )
    capture = AttentionStateCapture(model=model, layer_index=layer_index, position=position)
    with capture:
        original = score_evidence_suffix(
            model=model, prepared=prepared, prefix_token_ids=prefix_token_ids,
            bridge_token_ids=bridge_token_ids, suffix_token_ids=original_suffix_ids, seed=seed,
        )
    counterfactual = score_evidence_suffix(
        model=model, prepared=prepared, prefix_token_ids=prefix_token_ids,
        bridge_token_ids=bridge_token_ids, suffix_token_ids=counterfactual_suffix_ids, seed=seed,
    )
    return {**_preference(original, counterfactual), "attention_state": capture.complete_state()}


@torch.inference_mode()
def score_native_state_pair_preference(
    *,
    model: Any,
    prepared: dict[str, Any],
    prefix_token_ids: Sequence[int],
    bridge_token_ids: Sequence[int],
    original_suffix_ids: Sequence[int],
    counterfactual_suffix_ids: Sequence[int],
    generated_indices: dict[str, int],
    layer_index: int,
    seed: int,
) -> dict[str, Any]:
    """Score both candidates and capture M/R from each exact scoring sequence.

    Full-sequence and prefix-only matrix shapes can follow different low-precision
    kernels. Capturing donor and recipient states in the exact candidate pass makes
    self controls compare like with like while all captured positions remain
    causally before the scored suffix.
    """

    prompt_length = int(prepared["input_ids"].shape[1])
    positions = {
        name: absolute_intervention_position(
            prompt_length=prompt_length,
            intervention_generated_index=int(index),
        )
        for name, index in generated_indices.items()
    }
    if len(prefix_token_ids) != min(int(value) for value in generated_indices.values()):
        raise ValueError("State-pair scoring prefix must end at the earliest frozen state")
    results: dict[str, Any] = {}
    attention_states: dict[str, dict[str, dict[str, Any]]] = {}
    h_pre_states: dict[str, dict[str, torch.Tensor]] = {}
    for candidate_name, suffix in (
        ("original_candidate", original_suffix_ids),
        ("counterfactual_candidate", counterfactual_suffix_ids),
    ):
        attention_capture = AttentionStateMultiCapture(
            model=model, layer_index=layer_index, positions=positions
        )
        hpre_capture = CurrentHPreMultiCapture(
            model=model, layer_index=layer_index, positions=positions
        )
        with hpre_capture, attention_capture:
            results[candidate_name] = score_evidence_suffix(
                model=model,
                prepared=prepared,
                prefix_token_ids=prefix_token_ids,
                bridge_token_ids=bridge_token_ids,
                suffix_token_ids=suffix,
                seed=seed,
            )
        attention_states[candidate_name] = attention_capture.complete_states()
        h_pre_states[candidate_name] = hpre_capture.complete_states()
    return {
        **_preference(results["original_candidate"], results["counterfactual_candidate"]),
        **results,
        "attention_states": attention_states,
        "h_pre_states": h_pre_states,
        "absolute_positions": positions,
    }


@torch.inference_mode()
def score_query_patched_preference(
    *,
    model: Any,
    prepared: dict[str, Any],
    prefix_token_ids: Sequence[int],
    bridge_token_ids: Sequence[int],
    original_suffix_ids: Sequence[int],
    counterfactual_suffix_ids: Sequence[int],
    generated_index: int,
    layer_index: int,
    selected_heads: Sequence[int],
    donor_states: dict[str, dict[str, Any]],
    formulation: str,
    seed: int,
) -> dict[str, Any]:
    """Score reciprocal selected-head Q substitution with recipient-native K/V."""

    position = absolute_intervention_position(
        prompt_length=int(prepared["input_ids"].shape[1]),
        intervention_generated_index=int(generated_index),
    )
    results: dict[str, Any] = {}
    for name, suffix in (
        ("original_candidate", original_suffix_ids),
        ("counterfactual_candidate", counterfactual_suffix_ids),
    ):
        patch = SelectedHeadQueryPatch(
            model=model,
            layer_index=layer_index,
            position=position,
            selected_heads=selected_heads,
            donor_pre_rope_query=donor_states[name]["pre_rope_query"],
            donor_post_rope_query=donor_states[name]["post_rope_query"],
            formulation=formulation,
        )
        with patch:
            score = score_evidence_suffix(
                model=model, prepared=prepared, prefix_token_ids=prefix_token_ids,
                bridge_token_ids=bridge_token_ids, suffix_token_ids=suffix, seed=seed,
            )
        state, audit = patch.complete()
        results[name] = score
        results[f"{name}_state"] = state
        results[f"{name}_audit"] = audit
    preference = _preference(results["original_candidate"], results["counterfactual_candidate"])
    return {**preference, **results}


@torch.inference_mode()
def score_hpre_patched_preference(
    *,
    model: Any,
    prepared: dict[str, Any],
    prefix_token_ids: Sequence[int],
    bridge_token_ids: Sequence[int],
    original_suffix_ids: Sequence[int],
    counterfactual_suffix_ids: Sequence[int],
    generated_index: int,
    layer_index: int,
    donor_h_pre: torch.Tensor,
    seed: int,
) -> dict[str, Any]:
    """Patch only current-position h_pre and capture naturally recomputed routing."""

    position = absolute_intervention_position(
        prompt_length=int(prepared["input_ids"].shape[1]),
        intervention_generated_index=int(generated_index),
    )
    results: dict[str, Any] = {}
    for name, suffix in (
        ("original_candidate", original_suffix_ids),
        ("counterfactual_candidate", counterfactual_suffix_ids),
    ):
        hpre_patch = CurrentPositionBoundaryPatch(
            model=model,
            position=position,
            layer_index=layer_index,
            boundary="h_pre",
            source_state=donor_h_pre,
        )
        attention_capture = AttentionStateCapture(
            model=model, layer_index=layer_index, position=position
        )
        with hpre_patch, attention_capture:
            score = score_evidence_suffix(
                model=model, prepared=prepared, prefix_token_ids=prefix_token_ids,
                bridge_token_ids=bridge_token_ids, suffix_token_ids=suffix, seed=seed,
            )
        results[name] = score
        results[f"{name}_state"] = attention_capture.complete_state()
        results[f"{name}_audit"] = hpre_patch.audit[0]
    preference = _preference(results["original_candidate"], results["counterfactual_candidate"])
    return {**preference, **results}


__all__ = [
    "AttentionStateCapture",
    "AttentionStateMultiCapture",
    "CurrentHPreCapture",
    "CurrentHPreMultiCapture",
    "SelectedHeadQueryPatch",
    "evidence_suffix_logit_rows",
    "capture_native_state",
    "score_evidence_suffix",
    "score_hpre_patched_preference",
    "score_native_preference",
    "score_native_state_pair_preference",
    "score_query_patched_preference",
    "splice_current_query_heads",
]
