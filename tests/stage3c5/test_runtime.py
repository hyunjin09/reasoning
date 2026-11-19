from __future__ import annotations

import torch

from visual_reasoning.stage3c5.runtime import summarize_state


def test_state_summary_is_finite_and_reproducible() -> None:
    state = torch.tensor([[1.0, -2.0, 3.0]])
    summary = summarize_state(state)
    assert summary["shape"] == [1, 3]
    assert summary["l2_norm"] == torch.linalg.vector_norm(state).item()
    assert summary["mean"] == state.mean().item()
    assert summary["finite"] is True
    assert len(summary["sha256_float32"]) == 64
