from __future__ import annotations

import hashlib
import json

import pytest

from visual_reasoning.stage3c9.assay import (
    exact_readout_sequences,
    source_window_indices,
)


def _event(readout: int, original: list[int], counterfactual: list[int], history: list[int]) -> dict:
    digest = hashlib.sha256(json.dumps(history, separators=(",", ":")).encode("ascii")).hexdigest()
    return {
        "span_start_token": 20,
        "span_end_token": 22,
        "local_use_readout": {
            "token_index": readout,
            "history_before_ed_sha256": digest,
            "original_divergent_suffix_ids": original,
            "counterfactual_divergent_suffix_ids": counterfactual,
        },
    }


def test_exact_readout_sequences_verifies_frozen_prefix_hash() -> None:
    tokens = [{"token_id": value} for value in range(1, 31)]
    event = _event(25, [26], [99], list(range(1, 26)))
    result = exact_readout_sequences(tokens, event["local_use_readout"])
    assert result["prefix_token_ids"] == list(range(1, 26))
    assert result["original_suffix_ids"] == [26]
    assert result["counterfactual_suffix_ids"] == [99]
    assert result["prefix_hash_exact"]


def test_exact_readout_sequences_rejects_drifted_prefix() -> None:
    tokens = [{"token_id": value} for value in range(1, 31)]
    event = _event(25, [26], [99], [1, 2, 3])
    with pytest.raises(RuntimeError, match="prefix hash"):
        exact_readout_sequences(tokens, event["local_use_readout"])


def test_source_windows_end_immediately_before_frozen_span() -> None:
    assert source_window_indices(span_start_token=20, width=8) == list(range(12, 20))
    assert source_window_indices(span_start_token=20, width=16) == list(range(4, 20))
    with pytest.raises(ValueError):
        source_window_indices(span_start_token=7, width=8)

