"""Within-problem local Value-geometry helpers for Stage 3B.9."""

from __future__ import annotations

import numpy as np


def phase_b_condition_aliases(value_index: int) -> dict[str, str]:
    if value_index not in (1, 2, 3, 4):
        raise ValueError("Phase-B value index must be 1--4")
    return {
        "O": "O",
        "O_sham": "O_sham",
        "C": f"C{value_index}",
        "C_sham": f"C{value_index}_sham",
    }


def fit_leave_one_out_bases(deltas: np.ndarray) -> dict[int, dict[int, np.ndarray]]:
    """Fit rank 1--3 uncentered SVD bases from the three non-held-out values."""
    values = np.asarray(deltas, dtype=np.float64)
    if values.ndim != 2 or values.shape[0] != 4:
        raise ValueError("Expected four semantic delta vectors")
    fitted: dict[int, dict[int, np.ndarray]] = {}
    for held_out in range(4):
        training = np.delete(values, held_out, axis=0)
        _, _, vh = np.linalg.svd(training, full_matrices=False)
        fitted[held_out] = {rank: vh[:rank].T.copy() for rank in (1, 2, 3)}
    return fitted


__all__ = ["fit_leave_one_out_bases", "phase_b_condition_aliases"]
