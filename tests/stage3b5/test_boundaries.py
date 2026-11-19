from __future__ import annotations

import torch

from visual_reasoning.stage3b5.boundaries import (
    BOUNDARIES,
    CaptureCurrentBlockBoundaries,
    CurrentPositionBoundaryPatch,
    valid_boundary_capture_audit,
    valid_boundary_patch_audit,
)


class Scale(torch.nn.Module):
    def __init__(self, factor: float) -> None:
        super().__init__()
        self.factor = factor

    def forward(self, hidden_states: torch.Tensor) -> torch.Tensor:
        return hidden_states * self.factor


class FakeAttention(torch.nn.Module):
    def forward(self, hidden_states: torch.Tensor, **kwargs):
        return hidden_states + 1.0, None


class FakeMLP(torch.nn.Module):
    def forward(self, hidden_states: torch.Tensor) -> torch.Tensor:
        return hidden_states - 2.0


class FakeLayer(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.input_layernorm = Scale(2.0)
        self.self_attn = FakeAttention()
        self.post_attention_layernorm = Scale(3.0)
        self.mlp = FakeMLP()

    def forward(self, hidden_states: torch.Tensor) -> torch.Tensor:
        residual = hidden_states
        hidden_states = self.input_layernorm(hidden_states)
        hidden_states, _ = self.self_attn(hidden_states)
        hidden_states = residual + hidden_states
        residual = hidden_states
        hidden_states = self.post_attention_layernorm(hidden_states)
        hidden_states = self.mlp(hidden_states)
        return residual + hidden_states


class FakeLanguageModel(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.layers = torch.nn.ModuleList([FakeLayer(), FakeLayer()])


class FakeInnerModel(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.language_model = FakeLanguageModel()


class FakeModel(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.model = FakeInnerModel()

    def forward(self, hidden_states: torch.Tensor) -> torch.Tensor:
        for layer in self.model.language_model.layers:
            hidden_states = layer(hidden_states)
        return hidden_states


def capture(model: FakeModel, inputs: torch.Tensor):
    observer = CaptureCurrentBlockBoundaries(
        model=model,
        position=1,
        layer_indices=(0, 1),
    )
    with observer:
        output = model(inputs)
    return output, observer


def test_capture_records_exact_qwen_boundaries_and_shapes() -> None:
    model = FakeModel()
    inputs = torch.arange(12, dtype=torch.float32).reshape(1, 3, 4)
    _, observer = capture(model, inputs)
    states = observer.complete_states()

    assert tuple(states) == BOUNDARIES
    assert torch.equal(states["h_pre"][0], inputs[:, 1, :])
    assert torch.equal(states["pre_attn_norm"][0], inputs[:, 1, :] * 2.0)
    expected_post_attn = inputs[:, 1, :] + inputs[:, 1, :] * 2.0 + 1.0
    assert torch.equal(states["h_post_attn"][0], expected_post_attn)
    assert torch.equal(states["pre_mlp_norm"][0], expected_post_attn * 3.0)
    expected_post_block = expected_post_attn + expected_post_attn * 3.0 - 2.0
    assert torch.equal(states["h_post_block"][0], expected_post_block)
    assert torch.equal(states["h_post_block"][0], states["h_pre"][1])
    assert valid_boundary_capture_audit(
        observer.audit,
        layer_indices=(0, 1),
        position=1,
    )
    assert all(row["state_shape"] == [1, 4] for row in observer.audit)
    assert observer.residual_addition_audit == [
        {"layer_index": 0, "position": 1, "post_attn_sum_exact": True},
        {"layer_index": 1, "position": 1, "post_attn_sum_exact": True},
    ]


def test_every_boundary_self_patch_is_exact_and_recomputes_expected_modules() -> None:
    model = FakeModel()
    inputs = torch.arange(12, dtype=torch.float32).reshape(1, 3, 4)
    baseline, observer = capture(model, inputs)
    states = observer.complete_states()
    expected_downstream = {
        "h_pre": ["attention", "mlp"],
        "pre_attn_norm": ["attention", "mlp"],
        "h_post_attn": ["mlp"],
        "pre_mlp_norm": ["mlp"],
        "h_post_block": [],
    }

    for boundary in BOUNDARIES:
        patcher = CurrentPositionBoundaryPatch(
            model=model,
            position=1,
            layer_index=0,
            boundary=boundary,
            source_state=states[boundary][0],
        )
        with patcher:
            observed = model(inputs)
        assert torch.equal(observed, baseline), boundary
        assert valid_boundary_patch_audit(
            patcher.audit,
            layer_index=0,
            boundary=boundary,
            position=1,
            expected_downstream=expected_downstream[boundary],
        )


def test_post_attention_patch_achieves_source_residual_then_recomputes_mlp() -> None:
    model = FakeModel()
    recipient = torch.arange(12, dtype=torch.float32).reshape(1, 3, 4)
    donor = recipient + 100.0
    _, source_capture = capture(model, donor)
    source = source_capture.complete_states()["h_post_attn"][0]

    patcher = CurrentPositionBoundaryPatch(
        model=model,
        position=1,
        layer_index=0,
        boundary="h_post_attn",
        source_state=source,
    )
    with patcher:
        model(recipient)
    row = patcher.audit[0]
    assert row["current_position_exact_source_match"]
    assert row["achieved_post_attn_exact_source_match"]
    assert row["noncurrent_positions_changed"] == 0
    assert row["downstream_modules_reexecuted"] == ["mlp"]


def test_first_layer_post_block_and_second_layer_pre_patch_are_equivalent() -> None:
    model = FakeModel()
    recipient = torch.arange(12, dtype=torch.float32).reshape(1, 3, 4)
    donor = recipient + 10.0
    _, source_capture = capture(model, donor)
    states = source_capture.complete_states()
    assert torch.equal(states["h_post_block"][0], states["h_pre"][1])

    patch_first_output = CurrentPositionBoundaryPatch(
        model=model,
        position=1,
        layer_index=0,
        boundary="h_post_block",
        source_state=states["h_post_block"][0],
    )
    with patch_first_output:
        output_first = model(recipient)
    patch_second_input = CurrentPositionBoundaryPatch(
        model=model,
        position=1,
        layer_index=1,
        boundary="h_pre",
        source_state=states["h_pre"][1],
    )
    with patch_second_input:
        output_second = model(recipient)
    assert torch.equal(output_first, output_second)
