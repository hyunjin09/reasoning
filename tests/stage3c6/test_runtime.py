from __future__ import annotations

import pytest
import torch

from scripts.stage3c6 import run_phase_a
from visual_reasoning.stage3c6.runtime import (
    boundary_equivalence,
    interpolate_residual,
    residual_delta_summaries,
)


def test_residual_interpolation_has_exact_endpoints() -> None:
    suppressed = torch.tensor([[1.0, 2.0]])
    native = torch.tensor([[5.0, 10.0]])
    assert torch.equal(interpolate_residual(suppressed, native, 0.0), suppressed)
    assert torch.equal(interpolate_residual(suppressed, native, 1.0), native)
    assert torch.equal(interpolate_residual(suppressed, native, 0.5), torch.tensor([[3.0, 6.0]]))
    with pytest.raises(ValueError):
        interpolate_residual(suppressed, native, 1.1)


def test_residual_delta_summary_is_layerwise_and_finite() -> None:
    native = {"h_pre": {0: torch.tensor([[3.0, 4.0]]), 1: torch.tensor([[0.0, 2.0]])}}
    suppressed = {"h_pre": {0: torch.tensor([[0.0, 0.0]]), 1: torch.tensor([[0.0, 1.0]])}}
    rows = residual_delta_summaries(native, suppressed, boundary="h_pre")
    assert rows[0]["layer"] == 0
    assert rows[0]["delta_l2"] == pytest.approx(5.0)
    assert rows[0]["relative_delta_l2"] == pytest.approx(1.0)
    assert rows[1]["delta_l2"] == pytest.approx(1.0)


def test_post_block_equals_next_pre_boundary() -> None:
    states = {
        "h_post_block": {0: torch.tensor([[1.0]]), 1: torch.tensor([[2.0]])},
        "h_pre": {0: torch.tensor([[0.0]]), 1: torch.tensor([[1.0]])},
    }
    audit = boundary_equivalence(states)
    assert audit == [{"layer": 0, "next_layer": 1, "exact": True, "max_abs_delta": 0.0}]


def test_prior_stage3c5_resolver_accepts_validation_family(tmp_path, monkeypatch) -> None:
    path = tmp_path / "outputs/stage3c5/raw/phase_a_validation/shard_0/examples/141/result.json"
    path.parent.mkdir(parents=True)
    path.write_text('{"base_problem_id": "141"}\n', encoding="utf-8")
    monkeypatch.setattr(run_phase_a, "ROOT", tmp_path)
    assert run_phase_a.prior_stage3c5("141")["base_problem_id"] == "141"


def test_reproduction_record_defers_p4_when_validation_family_did_not_store_it() -> None:
    native = {"D": 1.0, "original_candidate": {"token_log_probabilities": [1]}, "counterfactual_candidate": {"token_log_probabilities": [2]}}
    suppressed = {"D": 0.5, "original_candidate": {"token_log_probabilities": [3]}, "counterfactual_candidate": {"token_log_probabilities": [4]}}
    old = {"native_A0": native, "arms": {"P5": suppressed}}
    result = run_phase_a.reproduction_record(native, suppressed, old)
    assert result["native_exact"] is True
    assert result["P4_comparison_available"] is False
    assert result["P4_suppressed_exact"] is None
