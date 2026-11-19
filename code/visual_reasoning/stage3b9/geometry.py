"""Frozen linear-geometry operations for Stage 3B.9."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import numpy as np


def _validated_ranks(ranks: Iterable[int], *, dimension: int) -> list[int]:
    values = sorted({int(rank) for rank in ranks})
    if not values or values[0] < 1 or values[-1] > int(dimension):
        raise ValueError("Every rank must be between one and the ambient dimension")
    return values


def _orthonormal_columns(basis: np.ndarray) -> np.ndarray:
    array = np.asarray(basis, dtype=np.float64)
    if array.ndim != 2 or min(array.shape) < 1:
        raise ValueError("A subspace basis must be a nonempty rank-two array")
    q, _ = np.linalg.qr(array, mode="reduced")
    return q


def fit_uncentered_rank_family(
    rows: np.ndarray,
    *,
    frozen_ranks: Iterable[int],
) -> tuple[dict[int, np.ndarray], dict[str, Any]]:
    """Fit nested uncentered right-singular bases at identifiable ranks only."""

    matrix = np.asarray(rows, dtype=np.float64)
    if matrix.ndim != 2 or min(matrix.shape) < 1:
        raise ValueError("The delta matrix must be a nonempty rank-two array")
    ranks = _validated_ranks(frozen_ranks, dimension=int(matrix.shape[1]))
    _, singular_values, vh = np.linalg.svd(matrix, full_matrices=False)
    tolerance = np.finfo(np.float64).eps * max(matrix.shape) * singular_values[0]
    identifiable_rank = int(np.sum(singular_values > tolerance))
    eligible = [rank for rank in ranks if rank <= identifiable_rank]
    family = {rank: vh[:rank].T.copy() for rank in eligible}
    energy = np.square(singular_values)
    fractions = energy / energy.sum() if float(energy.sum()) else np.zeros_like(energy)
    return family, {
        "row_count": int(matrix.shape[0]),
        "dimension": int(matrix.shape[1]),
        "identifiable_rank": identifiable_rank,
        "eligible_ranks": eligible,
        "ineligible_ranks": [rank for rank in ranks if rank not in eligible],
        "singular_values": singular_values.tolist(),
        "explained_energy_fraction": fractions.tolist(),
        "cumulative_explained_energy_fraction": np.cumsum(fractions).tolist(),
        "fit": "uncentered SVD",
    }


def random_rank_family(
    *,
    dimension: int,
    ranks: Iterable[int],
    seed: int,
) -> dict[int, np.ndarray]:
    """Materialize a deterministic nested Haar rank family from one QR draw."""

    width = int(dimension)
    values = _validated_ranks(ranks, dimension=width)
    generator = np.random.default_rng(int(seed))
    matrix = generator.standard_normal((width, values[-1]), dtype=np.float64)
    q, r = np.linalg.qr(matrix, mode="reduced")
    signs = np.where(np.diag(r) < 0.0, -1.0, 1.0)
    q = q * signs
    return {rank: q[:, :rank].copy() for rank in values}


def principal_angle_degrees(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    """Return canonical principal angles in degrees for two column subspaces."""

    left_q = _orthonormal_columns(left)
    right_q = _orthonormal_columns(right)
    if int(left_q.shape[0]) != int(right_q.shape[0]):
        raise ValueError("Subspaces must have the same ambient dimension")
    cosines = np.linalg.svd(left_q.T @ right_q, compute_uv=False)
    return np.degrees(np.arccos(np.clip(cosines, -1.0, 1.0)))


def projector_similarity(left: np.ndarray, right: np.ndarray) -> float:
    """Return normalized projector overlap in [0, 1]."""

    left_q = _orthonormal_columns(left)
    right_q = _orthonormal_columns(right)
    if int(left_q.shape[0]) != int(right_q.shape[0]):
        raise ValueError("Subspaces must have the same ambient dimension")
    denominator = min(int(left_q.shape[1]), int(right_q.shape[1]))
    return float(np.square(left_q.T @ right_q).sum() / denominator)


__all__ = [
    "fit_uncentered_rank_family",
    "principal_angle_degrees",
    "projector_similarity",
    "random_rank_family",
]
