"""Current-query-position residual capture and patching."""

from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Any, Sequence

import torch


def _hidden_output(output: Any) -> tuple[torch.Tensor, str]:
    if isinstance(output, torch.Tensor):
        return output, "tensor"
    if isinstance(output, tuple) and output and isinstance(output[0], torch.Tensor):
        return output[0], "tuple"
    raise TypeError("Language layer output must be a tensor or a tuple beginning with one")


def replace_current_position(
    output: Any,
    source_state: torch.Tensor,
    *,
    position: int,
) -> tuple[Any, dict[str, Any]]:
    hidden, container = _hidden_output(output)
    index = int(position)
    if hidden.ndim != 3 or index < 0 or index >= int(hidden.shape[1]):
        raise ValueError("Current residual position is outside [batch, sequence, hidden]")
    expected = (int(hidden.shape[0]), int(hidden.shape[2]))
    if tuple(source_state.shape) != expected:
        raise ValueError(f"Source residual shape mismatch: expected {expected}, got {tuple(source_state.shape)}")
    patched_hidden = hidden.clone()
    patched_hidden[:, index, :] = source_state.to(device=hidden.device, dtype=hidden.dtype)
    noncurrent = torch.ones(int(hidden.shape[1]), dtype=torch.bool, device=hidden.device)
    noncurrent[index] = False
    noncurrent_changed = int(
        torch.count_nonzero(patched_hidden[:, noncurrent, :] != hidden[:, noncurrent, :]).item()
    )
    patched = patched_hidden if container == "tensor" else (patched_hidden, *output[1:])
    return patched, {
        "output_container": container,
        "positions_replaced": [index],
        "source_shape": list(source_state.shape),
        "hidden_shape": list(hidden.shape),
        "noncurrent_positions_changed": noncurrent_changed,
        "current_position_exact_source_match": bool(
            torch.equal(patched_hidden[:, index, :], source_state.to(hidden.device, hidden.dtype))
        ),
    }


def valid_residual_patch_audit(
    audit: Sequence[dict[str, Any]],
    *,
    layer_index: int,
    position: int,
) -> bool:
    return bool(
        len(audit) == 1
        and int(audit[0]["layer_index"]) == int(layer_index)
        and audit[0]["positions_replaced"] == [int(position)]
        and int(audit[0]["noncurrent_positions_changed"]) == 0
        and bool(audit[0]["current_position_exact_source_match"])
    )


class CaptureCurrentResiduals(AbstractContextManager["CaptureCurrentResiduals"]):
    def __init__(self, *, model: Any, position: int, layer_indices: Sequence[int]) -> None:
        self.model = model
        self.position = int(position)
        self.layer_indices = tuple(sorted({int(value) for value in layer_indices}))
        self.states: dict[int, torch.Tensor] = {}
        self.audit: list[dict[str, Any]] = []
        self._handles: list[Any] = []

    def _hook(self, layer_index: int):
        def hook(module: torch.nn.Module, args: tuple[Any, ...], output: Any):
            hidden, container = _hidden_output(output)
            if self.position < 0 or self.position >= int(hidden.shape[1]):
                raise ValueError("Residual capture position is outside the layer output")
            if layer_index in self.states:
                raise RuntimeError(f"Residual layer {layer_index} captured more than once")
            state = hidden[:, self.position, :].detach().clone()
            self.states[layer_index] = state
            self.audit.append(
                {
                    "layer_index": layer_index,
                    "position": self.position,
                    "state_shape": list(state.shape),
                    "output_container": container,
                }
            )
            return output

        return hook

    def __enter__(self) -> "CaptureCurrentResiduals":
        layers = self.model.model.language_model.layers
        if any(index < 0 or index >= len(layers) for index in self.layer_indices):
            raise ValueError("Residual capture layer is outside the language model")
        for index in self.layer_indices:
            self._handles.append(layers[index].register_forward_hook(self._hook(index)))
        return self

    def close(self) -> None:
        for handle in self._handles:
            handle.remove()
        self._handles.clear()

    def complete_states(self) -> dict[int, torch.Tensor]:
        if sorted(self.states) != list(self.layer_indices):
            raise RuntimeError("Residual capture did not visit every requested layer")
        return dict(self.states)

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()


class CurrentPositionResidualPatch(AbstractContextManager["CurrentPositionResidualPatch"]):
    def __init__(
        self,
        *,
        model: Any,
        layer_index: int,
        position: int,
        source_state: torch.Tensor,
    ) -> None:
        self.model = model
        self.layer_index = int(layer_index)
        self.position = int(position)
        self.source_state = source_state
        self.audit: list[dict[str, Any]] = []
        self._handle: Any = None

    def _hook(self, module: torch.nn.Module, args: tuple[Any, ...], output: Any):
        patched, audit = replace_current_position(
            output,
            self.source_state,
            position=self.position,
        )
        audit["layer_index"] = self.layer_index
        self.audit.append(audit)
        return patched

    def __enter__(self) -> "CurrentPositionResidualPatch":
        layers = self.model.model.language_model.layers
        if self.layer_index < 0 or self.layer_index >= len(layers):
            raise ValueError("Residual patch layer is outside the language model")
        self._handle = layers[self.layer_index].register_forward_hook(self._hook)
        return self

    def close(self) -> None:
        if self._handle is not None:
            self._handle.remove()
            self._handle = None

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()
