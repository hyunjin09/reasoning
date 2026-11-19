"""Exact current-position capture and patching at Qwen decoder block boundaries."""

from __future__ import annotations

from contextlib import AbstractContextManager
from types import MethodType
from typing import Any, Sequence

import torch

from visual_reasoning.stage3b3.residual import replace_current_position


BOUNDARIES = (
    "h_pre",
    "pre_attn_norm",
    "h_post_attn",
    "pre_mlp_norm",
    "h_post_block",
)

EXPECTED_DOWNSTREAM = {
    "h_pre": ("attention", "mlp"),
    "pre_attn_norm": ("attention", "mlp"),
    "h_post_attn": ("mlp",),
    "pre_mlp_norm": ("mlp",),
    "h_post_block": (),
}


def _hidden(output: Any) -> tuple[torch.Tensor, str]:
    if isinstance(output, torch.Tensor):
        return output, "tensor"
    if isinstance(output, tuple) and output and isinstance(output[0], torch.Tensor):
        return output[0], "tuple"
    raise TypeError("Expected a tensor or tuple beginning with a tensor")


def _layers(model: Any) -> Any:
    return model.model.language_model.layers


def _validate_layers(model: Any, layer_indices: Sequence[int]) -> tuple[int, ...]:
    requested = tuple(sorted({int(value) for value in layer_indices}))
    if not requested or any(index < 0 or index >= len(_layers(model)) for index in requested):
        raise ValueError("Requested boundary layer is outside the language model")
    return requested


def _current(hidden: torch.Tensor, position: int) -> torch.Tensor:
    if hidden.ndim != 3 or position < 0 or position >= int(hidden.shape[1]):
        raise ValueError("Boundary position is outside [batch, sequence, hidden]")
    return hidden[:, position, :].detach().clone()


def valid_boundary_capture_audit(
    audit: Sequence[dict[str, Any]],
    *,
    layer_indices: Sequence[int],
    position: int,
) -> bool:
    expected = {
        (int(layer_index), boundary)
        for layer_index in layer_indices
        for boundary in BOUNDARIES
    }
    observed = {(int(row["layer_index"]), str(row["boundary"])) for row in audit}
    return bool(
        len(audit) == len(expected)
        and observed == expected
        and all(
            int(row["position"]) == int(position)
            and row["state_shape"][0] == 1
            for row in audit
        )
    )


def valid_boundary_patch_audit(
    audit: Sequence[dict[str, Any]],
    *,
    layer_index: int,
    boundary: str,
    position: int,
    expected_downstream: Sequence[str] | None = None,
) -> bool:
    if len(audit) != 1:
        return False
    row = audit[0]
    downstream = tuple(EXPECTED_DOWNSTREAM[boundary] if expected_downstream is None else expected_downstream)
    return bool(
        int(row["layer_index"]) == int(layer_index)
        and str(row["boundary"]) == str(boundary)
        and int(row["position"]) == int(position)
        and row["positions_replaced"] == [int(position)]
        and int(row["noncurrent_positions_changed"]) == 0
        and bool(row["current_position_exact_source_match"])
        and tuple(row["downstream_modules_reexecuted"]) == downstream
        and bool(row["downstream_recompute_verified"])
        and (
            boundary != "h_post_attn"
            or bool(row.get("achieved_post_attn_exact_source_match"))
        )
    )


class CaptureCurrentBlockBoundaries(
    AbstractContextManager["CaptureCurrentBlockBoundaries"]
):
    """Capture the five exact block states at one absolute sequence position."""

    def __init__(
        self,
        *,
        model: Any,
        position: int,
        layer_indices: Sequence[int],
    ) -> None:
        self.model = model
        self.position = int(position)
        self.layer_indices = _validate_layers(model, layer_indices)
        self.states: dict[str, dict[int, torch.Tensor]] = {
            boundary: {} for boundary in BOUNDARIES
        }
        self.audit: list[dict[str, Any]] = []
        self.residual_addition_audit: list[dict[str, Any]] = []
        self._attention_outputs: dict[int, torch.Tensor] = {}
        self._handles: list[Any] = []

    def _record(self, layer_index: int, boundary: str, output: Any) -> None:
        hidden, container = _hidden(output)
        if layer_index in self.states[boundary]:
            raise RuntimeError(f"Captured {boundary} at layer {layer_index} more than once")
        state = _current(hidden, self.position)
        self.states[boundary][layer_index] = state
        self.audit.append({
            "layer_index": int(layer_index),
            "boundary": boundary,
            "position": self.position,
            "state_shape": list(state.shape),
            "hidden_shape": list(hidden.shape),
            "output_container": container,
        })

    def _layer_pre(self, layer_index: int):
        def hook(module: torch.nn.Module, args: tuple[Any, ...]):
            self._record(layer_index, "h_pre", args[0])
        return hook

    def _norm_output(self, layer_index: int, boundary: str):
        def hook(module: torch.nn.Module, args: tuple[Any, ...], output: Any):
            self._record(layer_index, boundary, output)
            return output
        return hook

    def _attention_output(self, layer_index: int):
        def hook(module: torch.nn.Module, args: tuple[Any, ...], output: Any):
            hidden, _ = _hidden(output)
            self._attention_outputs[layer_index] = _current(hidden, self.position)
            return output
        return hook

    def _post_attn_input(self, layer_index: int):
        def hook(module: torch.nn.Module, args: tuple[Any, ...]):
            self._record(layer_index, "h_post_attn", args[0])
            expected = (
                self.states["h_pre"][layer_index]
                + self._attention_outputs[layer_index]
            )
            observed = self.states["h_post_attn"][layer_index]
            self.residual_addition_audit.append({
                "layer_index": int(layer_index),
                "position": self.position,
                "post_attn_sum_exact": bool(torch.equal(expected, observed)),
            })
        return hook

    def _layer_output(self, layer_index: int):
        def hook(module: torch.nn.Module, args: tuple[Any, ...], output: Any):
            self._record(layer_index, "h_post_block", output)
            return output
        return hook

    def __enter__(self) -> "CaptureCurrentBlockBoundaries":
        for layer_index in self.layer_indices:
            layer = _layers(self.model)[layer_index]
            self._handles.extend([
                layer.register_forward_pre_hook(self._layer_pre(layer_index)),
                layer.input_layernorm.register_forward_hook(
                    self._norm_output(layer_index, "pre_attn_norm")
                ),
                layer.self_attn.register_forward_hook(self._attention_output(layer_index)),
                layer.post_attention_layernorm.register_forward_pre_hook(
                    self._post_attn_input(layer_index)
                ),
                layer.post_attention_layernorm.register_forward_hook(
                    self._norm_output(layer_index, "pre_mlp_norm")
                ),
                layer.register_forward_hook(self._layer_output(layer_index)),
            ])
        return self

    def complete_states(self) -> dict[str, dict[int, torch.Tensor]]:
        if not valid_boundary_capture_audit(
            self.audit,
            layer_indices=self.layer_indices,
            position=self.position,
        ):
            raise RuntimeError("Boundary capture did not visit every requested state once")
        if len(self.residual_addition_audit) != len(self.layer_indices) or not all(
            bool(row["post_attn_sum_exact"]) for row in self.residual_addition_audit
        ):
            raise RuntimeError("Post-attention residual-addition audit failed")
        return {
            boundary: dict(layer_states)
            for boundary, layer_states in self.states.items()
        }

    def close(self) -> None:
        for handle in self._handles:
            handle.remove()
        self._handles.clear()

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()


class CurrentPositionBoundaryPatch(
    AbstractContextManager["CurrentPositionBoundaryPatch"]
):
    """Patch one exact block state, retaining the recipient's unpatched residual branches."""

    def __init__(
        self,
        *,
        model: Any,
        position: int,
        layer_index: int,
        boundary: str,
        source_state: torch.Tensor,
    ) -> None:
        self.model = model
        self.position = int(position)
        self.layer_index = _validate_layers(model, (layer_index,))[0]
        if boundary not in BOUNDARIES:
            raise ValueError(f"Unsupported block boundary: {boundary}")
        self.boundary = boundary
        self.source_state = source_state
        self.audit: list[dict[str, Any]] = []
        self._row: dict[str, Any] | None = None
        self._handles: list[Any] = []
        self._recipient_h_pre: torch.Tensor | None = None
        self._downstream: list[str] = []
        self._events: list[str] = []
        self._original_forward: Any | None = None

    def _record_patch(self, row: dict[str, Any]) -> None:
        if self._row is not None:
            raise RuntimeError("Boundary patch executed more than once")
        row.update({
            "layer_index": self.layer_index,
            "boundary": self.boundary,
            "position": self.position,
            "downstream_modules_reexecuted": self._downstream,
            "event_order": self._events,
        })
        self._row = row
        self.audit.append(row)
        self._events.append("patch")

    def _patch_output(self):
        def hook(module: torch.nn.Module, args: tuple[Any, ...], output: Any):
            patched, row = replace_current_position(
                output,
                self.source_state,
                position=self.position,
            )
            self._record_patch(row)
            return patched
        return hook

    def _patch_input(self):
        def hook(module: torch.nn.Module, args: tuple[Any, ...]):
            patched, row = replace_current_position(
                args[0],
                self.source_state,
                position=self.position,
            )
            self._record_patch(row)
            return (patched, *args[1:])
        return hook

    def _install_post_attention_forward(self, layer: torch.nn.Module) -> None:
        """Replace the audited decoder forward so the raw residual itself is patched.

        A post-RMSNorm hook would change the MLP input but leave the local residual
        branch untouched. Reconstructing the frozen Qwen block forward is therefore
        required to make R3 an exact raw `h_post_attn` intervention.
        """
        self._original_forward = layer.forward
        owner = self

        def patched_forward(
            module: torch.nn.Module,
            hidden_states: torch.Tensor,
            position_embeddings: tuple[torch.Tensor, torch.Tensor] | None = None,
            attention_mask: torch.Tensor | None = None,
            position_ids: torch.LongTensor | None = None,
            past_key_values: Any | None = None,
            use_cache: bool | None = False,
            **kwargs: Any,
        ) -> torch.Tensor:
            residual = hidden_states
            hidden_states = module.input_layernorm(hidden_states)
            hidden_states, _ = module.self_attn(
                hidden_states=hidden_states,
                attention_mask=attention_mask,
                position_ids=position_ids,
                past_key_values=past_key_values,
                use_cache=use_cache,
                position_embeddings=position_embeddings,
                **kwargs,
            )
            hidden_states = residual + hidden_states
            hidden_states, row = replace_current_position(
                hidden_states,
                owner.source_state,
                position=owner.position,
            )
            row["achieved_post_attn_exact_source_match"] = bool(
                row["current_position_exact_source_match"]
            )
            row["implementation"] = "audited_decoder_forward_with_exact_raw_post_attn_patch"
            owner._record_patch(row)
            residual = hidden_states
            hidden_states = module.post_attention_layernorm(hidden_states)
            hidden_states = module.mlp(hidden_states)
            hidden_states = residual + hidden_states
            return hidden_states

        layer.forward = MethodType(patched_forward, layer)

    def _observe_downstream(self, name: str):
        def hook(module: torch.nn.Module, args: tuple[Any, ...], output: Any):
            if self._row is not None:
                self._downstream.append(name)
                self._events.append(name)
            return output
        return hook

    def __enter__(self) -> "CurrentPositionBoundaryPatch":
        layer = _layers(self.model)[self.layer_index]
        if self.boundary == "h_pre":
            self._handles.append(layer.register_forward_pre_hook(self._patch_input()))
        elif self.boundary == "pre_attn_norm":
            self._handles.append(layer.input_layernorm.register_forward_hook(self._patch_output()))
        elif self.boundary == "h_post_attn":
            self._install_post_attention_forward(layer)
        elif self.boundary == "pre_mlp_norm":
            self._handles.append(
                layer.post_attention_layernorm.register_forward_hook(self._patch_output())
            )
        elif self.boundary == "h_post_block":
            self._handles.append(layer.register_forward_hook(self._patch_output()))

        if self.boundary in {"h_pre", "pre_attn_norm"}:
            self._handles.append(
                layer.self_attn.register_forward_hook(self._observe_downstream("attention"))
            )
        if self.boundary in {"h_pre", "pre_attn_norm", "h_post_attn", "pre_mlp_norm"}:
            self._handles.append(layer.mlp.register_forward_hook(self._observe_downstream("mlp")))
        return self

    def close(self) -> None:
        if self._original_forward is not None:
            _layers(self.model)[self.layer_index].forward = self._original_forward
            self._original_forward = None
        for handle in self._handles:
            handle.remove()
        self._handles.clear()
        if self._row is not None:
            expected = list(EXPECTED_DOWNSTREAM[self.boundary])
            self._row["downstream_recompute_verified"] = self._downstream == expected

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()
