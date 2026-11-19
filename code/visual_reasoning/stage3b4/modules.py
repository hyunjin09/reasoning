"""Current-position capture and restoration at Qwen decoder module surfaces."""

from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Any, Sequence

import torch

from visual_reasoning.stage3b3.residual import replace_current_position


MODULE_KINDS = ("attention", "mlp", "block")


def _hidden_output(output: Any) -> torch.Tensor:
    if isinstance(output, torch.Tensor):
        return output
    if isinstance(output, tuple) and output and isinstance(output[0], torch.Tensor):
        return output[0]
    raise TypeError("Module output must be a tensor or a tuple beginning with one")


def _module(model: Any, layer_index: int, module_kind: str) -> torch.nn.Module:
    layer = model.model.language_model.layers[int(layer_index)]
    if module_kind == "attention":
        return layer.self_attn
    if module_kind == "mlp":
        return layer.mlp
    if module_kind == "block":
        return layer
    raise ValueError(f"Unsupported module kind: {module_kind}")


def _validate_request(
    model: Any,
    *,
    layer_indices: Sequence[int],
    module_kinds: Sequence[str],
) -> tuple[tuple[int, ...], tuple[str, ...]]:
    layers = tuple(sorted({int(value) for value in layer_indices}))
    kinds = tuple(dict.fromkeys(str(value) for value in module_kinds))
    layer_count = len(model.model.language_model.layers)
    if not layers or any(value < 0 or value >= layer_count for value in layers):
        raise ValueError("Requested module layer is outside the language model")
    if not kinds or any(value not in MODULE_KINDS for value in kinds):
        raise ValueError("Requested module kind is unsupported")
    return layers, kinds


def _expected_keys(
    *, layer_indices: Sequence[int], module_kinds: Sequence[str]
) -> set[tuple[int, str]]:
    return {
        (int(layer_index), str(module_kind))
        for layer_index in layer_indices
        for module_kind in module_kinds
    }


def valid_module_capture_audit(
    audit: Sequence[dict[str, Any]],
    *,
    layer_indices: Sequence[int],
    module_kinds: Sequence[str],
    position: int,
) -> bool:
    expected = _expected_keys(layer_indices=layer_indices, module_kinds=module_kinds)
    observed = {(int(row["layer_index"]), str(row["module_kind"])) for row in audit}
    return bool(
        len(audit) == len(expected)
        and observed == expected
        and all(int(row["position"]) == int(position) for row in audit)
    )


def valid_module_patch_audit(
    audit: Sequence[dict[str, Any]],
    *,
    layer_indices: Sequence[int],
    module_kinds: Sequence[str],
    position: int,
) -> bool:
    expected = _expected_keys(layer_indices=layer_indices, module_kinds=module_kinds)
    observed = {(int(row["layer_index"]), str(row["module_kind"])) for row in audit}
    return bool(
        len(audit) == len(expected)
        and observed == expected
        and all(
            int(row["position"]) == int(position)
            and row["positions_replaced"] == [int(position)]
            and int(row["noncurrent_positions_changed"]) == 0
            and bool(row["current_position_exact_source_match"])
            for row in audit
        )
    )


class CaptureCurrentModuleContributions(
    AbstractContextManager["CaptureCurrentModuleContributions"]
):
    def __init__(
        self,
        *,
        model: Any,
        position: int,
        layer_indices: Sequence[int],
        module_kinds: Sequence[str],
    ) -> None:
        self.model = model
        self.position = int(position)
        self.layer_indices, self.module_kinds = _validate_request(
            model,
            layer_indices=layer_indices,
            module_kinds=module_kinds,
        )
        self.states: dict[str, dict[int, torch.Tensor]] = {
            kind: {} for kind in self.module_kinds
        }
        self.audit: list[dict[str, Any]] = []
        self._handles: list[Any] = []

    def _hook(self, layer_index: int, module_kind: str):
        def hook(module: torch.nn.Module, args: tuple[Any, ...], output: Any):
            hidden = _hidden_output(output)
            if self.position < 0 or self.position >= int(hidden.shape[1]):
                raise ValueError("Module capture position is outside the sequence")
            if layer_index in self.states[module_kind]:
                raise RuntimeError(f"{module_kind} layer {layer_index} captured more than once")
            state = hidden[:, self.position, :].detach().clone()
            self.states[module_kind][layer_index] = state
            self.audit.append({
                "layer_index": layer_index,
                "module_kind": module_kind,
                "position": self.position,
                "state_shape": list(state.shape),
                "output_shape": list(hidden.shape),
                "output_container": "tuple" if isinstance(output, tuple) else "tensor",
            })
            return output

        return hook

    def __enter__(self) -> "CaptureCurrentModuleContributions":
        for layer_index in self.layer_indices:
            for module_kind in self.module_kinds:
                handle = _module(self.model, layer_index, module_kind).register_forward_hook(
                    self._hook(layer_index, module_kind)
                )
                self._handles.append(handle)
        return self

    def complete_states(self) -> dict[str, dict[int, torch.Tensor]]:
        if not valid_module_capture_audit(
            self.audit,
            layer_indices=self.layer_indices,
            module_kinds=self.module_kinds,
            position=self.position,
        ):
            raise RuntimeError("Module capture did not visit every requested hook exactly once")
        return {kind: dict(values) for kind, values in self.states.items()}

    def close(self) -> None:
        for handle in self._handles:
            handle.remove()
        self._handles.clear()

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()


class CurrentPositionModulePatch(AbstractContextManager["CurrentPositionModulePatch"]):
    def __init__(
        self,
        *,
        model: Any,
        position: int,
        source_states: dict[str, dict[int, torch.Tensor]],
        layer_indices: Sequence[int],
        module_kinds: Sequence[str],
    ) -> None:
        self.model = model
        self.position = int(position)
        self.layer_indices, self.module_kinds = _validate_request(
            model,
            layer_indices=layer_indices,
            module_kinds=module_kinds,
        )
        if "block" in self.module_kinds and len(self.module_kinds) > 1:
            raise ValueError("Full-block restoration cannot be combined with component hooks")
        self.source_states = source_states
        for module_kind in self.module_kinds:
            if module_kind not in source_states:
                raise ValueError(f"Missing source states for {module_kind}")
            missing = set(self.layer_indices) - set(source_states[module_kind])
            if missing:
                raise ValueError(f"Missing {module_kind} source layers: {sorted(missing)}")
        self.audit: list[dict[str, Any]] = []
        self._handles: list[Any] = []

    def _hook(self, layer_index: int, module_kind: str):
        def hook(module: torch.nn.Module, args: tuple[Any, ...], output: Any):
            patched, row = replace_current_position(
                output,
                self.source_states[module_kind][layer_index],
                position=self.position,
            )
            row.update({"layer_index": layer_index, "module_kind": module_kind, "position": self.position})
            self.audit.append(row)
            return patched

        return hook

    def __enter__(self) -> "CurrentPositionModulePatch":
        for layer_index in self.layer_indices:
            for module_kind in self.module_kinds:
                handle = _module(self.model, layer_index, module_kind).register_forward_hook(
                    self._hook(layer_index, module_kind)
                )
                self._handles.append(handle)
        return self

    def close(self) -> None:
        for handle in self._handles:
            handle.remove()
        self._handles.clear()

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()
