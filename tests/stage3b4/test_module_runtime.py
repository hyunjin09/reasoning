from __future__ import annotations

import torch
from unittest.mock import patch

from visual_reasoning.stage3b4.modules import (
    CaptureCurrentModuleContributions,
    CurrentPositionModulePatch,
    valid_module_capture_audit,
    valid_module_patch_audit,
)
from visual_reasoning.stage3b4.runtime import (
    absolute_intervention_position,
    capture_preference_current_modules,
    score_preference_with_current_modules,
)


class FakeAttention(torch.nn.Module):
    def forward(self, hidden_states: torch.Tensor):
        return hidden_states + 1.0, None


class FakeMLP(torch.nn.Module):
    def forward(self, hidden_states: torch.Tensor):
        return hidden_states * 2.0


class FakeLayer(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.self_attn = FakeAttention()
        self.mlp = FakeMLP()

    def forward(self, hidden_states: torch.Tensor) -> torch.Tensor:
        residual = hidden_states
        attention, _ = self.self_attn(hidden_states)
        hidden_states = residual + attention
        residual = hidden_states
        mlp = self.mlp(hidden_states)
        return residual + mlp


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


def test_capture_records_attention_mlp_and_block_current_position() -> None:
    model = FakeModel()
    inputs = torch.arange(12, dtype=torch.float32).reshape(1, 3, 4)

    capture = CaptureCurrentModuleContributions(
        model=model,
        position=1,
        layer_indices=(0, 1),
        module_kinds=("attention", "mlp", "block"),
    )
    with capture:
        model(inputs)

    states = capture.complete_states()
    assert set(states) == {"attention", "mlp", "block"}
    assert set(states["attention"]) == {0, 1}
    assert states["attention"][0].shape == (1, 4)
    assert valid_module_capture_audit(
        capture.audit,
        layer_indices=(0, 1),
        module_kinds=("attention", "mlp", "block"),
        position=1,
    )


def test_self_patch_is_transparent_for_each_module_surface() -> None:
    model = FakeModel()
    inputs = torch.arange(12, dtype=torch.float32).reshape(1, 3, 4)
    capture = CaptureCurrentModuleContributions(
        model=model,
        position=1,
        layer_indices=(0, 1),
        module_kinds=("attention", "mlp", "block"),
    )
    with capture:
        baseline = model(inputs)

    for module_kinds in (("attention",), ("mlp",), ("attention", "mlp"), ("block",)):
        patch = CurrentPositionModulePatch(
            model=model,
            position=1,
            source_states=capture.complete_states(),
            layer_indices=(0, 1),
            module_kinds=module_kinds,
        )
        with patch:
            patched = model(inputs)
        assert torch.equal(patched, baseline)
        assert valid_module_patch_audit(
            patch.audit,
            layer_indices=(0, 1),
            module_kinds=module_kinds,
            position=1,
        )


def test_patch_changes_only_the_selected_current_module_positions() -> None:
    model = FakeModel()
    inputs = torch.zeros((1, 3, 4), dtype=torch.float32)
    source_states = {
        "attention": {0: torch.full((1, 4), 7.0)},
        "mlp": {0: torch.full((1, 4), 11.0)},
        "block": {},
    }
    patch = CurrentPositionModulePatch(
        model=model,
        position=1,
        source_states=source_states,
        layer_indices=(0,),
        module_kinds=("attention", "mlp"),
    )

    with patch:
        patched = model(inputs)

    assert not torch.equal(patched, model(inputs))
    assert valid_module_patch_audit(
        patch.audit,
        layer_indices=(0,),
        module_kinds=("attention", "mlp"),
        position=1,
    )
    assert all(row["noncurrent_positions_changed"] == 0 for row in patch.audit)


def test_runtime_uses_distinct_absolute_positions_and_self_restores_exactly() -> None:
    model = FakeModel()
    prepared = {
        "input_ids": torch.ones((1, 5), dtype=torch.long),
        "hidden_states": torch.arange(40, dtype=torch.float32).reshape(1, 10, 4),
    }

    def fake_score_candidate(*, model, prepared, prefix_token_ids, candidate_token_ids, seed):
        output = model(prepared["hidden_states"])
        value = float(output.sum().item()) + float(sum(candidate_token_ids))
        return {
            "mean_log_probability": value,
            "token_log_probabilities": [value],
            "finite": True,
        }

    with patch("visual_reasoning.stage3b4.runtime.score_candidate", fake_score_candidate):
        capture = capture_preference_current_modules(
            model=model,
            prepared=prepared,
            context_token_ids=(1, 2, 3, 4),
            candidate_original_ids=(5,),
            candidate_counterfactual_ids=(6,),
            intervention_generated_index=3,
            layer_indices=(0, 1),
            module_kinds=("attention", "mlp", "block"),
            seed=1234,
        )
        restored = score_preference_with_current_modules(
            model=model,
            prepared=prepared,
            context_token_ids=(1, 2, 3, 4),
            candidate_original_ids=(5,),
            candidate_counterfactual_ids=(6,),
            intervention_generated_index=3,
            layer_indices=(0, 1),
            module_kinds=("attention", "mlp"),
            source_states_by_candidate=capture["states"],
            seed=1234,
        )

    assert absolute_intervention_position(prompt_length=5, intervention_generated_index=3) == 7
    assert capture["current_absolute_position"] == 7
    assert capture["all_module_capture_audits_valid"]
    assert restored["all_module_patch_audits_valid"]
    assert restored["D"] == capture["D"]
