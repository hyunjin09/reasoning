"""Frozen-coordinate helpers shared by Stage 3C.9 GPU runners."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any


CONDITIONS = ("O", "O_sham", "C", "C_sham")
SEMANTIC_CONDITIONS = ("O", "C")


def exact_readout_sequences(
    tokens: Sequence[Mapping[str, Any]], readout: Mapping[str, Any],
) -> dict[str, Any]:
    """Rebuild and verify the exact frozen prefix and candidate suffixes."""

    index = int(readout["token_index"])
    if not 0 < index <= len(tokens):
        raise ValueError("Frozen readout token lies outside the trajectory")
    prefix = [int(row["token_id"]) for row in tokens[:index]]
    payload = json.dumps(prefix, separators=(",", ":")).encode("ascii")
    observed_hash = hashlib.sha256(payload).hexdigest()
    expected_hash = str(readout["history_before_ed_sha256"])
    if observed_hash != expected_hash:
        raise RuntimeError("Frozen readout prefix hash does not match persisted generation tokens")
    original = [int(value) for value in readout["original_divergent_suffix_ids"]]
    counterfactual = [int(value) for value in readout["counterfactual_divergent_suffix_ids"]]
    if not original or not counterfactual or original == counterfactual:
        raise RuntimeError("Frozen evidence candidates must be nonempty and distinct")
    return {
        "prefix_token_ids": prefix,
        "original_suffix_ids": original,
        "counterfactual_suffix_ids": counterfactual,
        "prefix_sha256": observed_hash,
        "prefix_hash_exact": True,
        "readout_generated_index": index,
    }


def source_window_indices(*, span_start_token: int, width: int) -> list[int]:
    """Return the prospective W8/W16 window immediately before an event span."""

    start, window = int(span_start_token), int(width)
    if window not in {8, 16} or start < window:
        raise ValueError("Source window must be W8/W16 and fit before the event")
    return list(range(start - window, start))


__all__ = [
    "CONDITIONS",
    "SEMANTIC_CONDITIONS",
    "exact_readout_sequences",
    "source_window_indices",
]
