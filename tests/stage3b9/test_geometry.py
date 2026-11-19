from __future__ import annotations

import numpy as np
import pytest

from visual_reasoning.stage3b9.geometry import (
    fit_uncentered_rank_family,
    principal_angle_degrees,
    projector_similarity,
    random_rank_family,
)


def test_fit_uncentered_rank_family_uses_only_identifiable_frozen_ranks() -> None:
    rows = np.asarray(
        [
            [3.0, 0.0, 0.0, 0.0],
            [2.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
        ],
        dtype=np.float64,
    )
    family, audit = fit_uncentered_rank_family(rows, frozen_ranks=[1, 2, 4])

    assert sorted(family) == [1, 2]
    assert audit["identifiable_rank"] == 2
    assert audit["ineligible_ranks"] == [4]
    np.testing.assert_allclose(family[2].T @ family[2], np.eye(2), atol=1e-12)


def test_random_rank_family_is_seeded_nested_and_orthonormal() -> None:
    first = random_rank_family(dimension=12, ranks=[1, 2, 4], seed=71)
    second = random_rank_family(dimension=12, ranks=[1, 2, 4], seed=71)

    assert first.keys() == second.keys()
    for rank, basis in first.items():
        np.testing.assert_array_equal(basis, second[rank])
        np.testing.assert_allclose(basis.T @ basis, np.eye(rank), atol=1e-12)
    np.testing.assert_array_equal(first[1], first[4][:, :1])
    np.testing.assert_array_equal(first[2], first[4][:, :2])


def test_random_rank_family_rejects_rank_above_dimension() -> None:
    with pytest.raises(ValueError, match="rank"):
        random_rank_family(dimension=3, ranks=[1, 4], seed=1)


def test_principal_angles_and_projector_similarity_handle_equal_subspaces() -> None:
    left = np.eye(5, dtype=np.float64)[:, :2]
    right = left.copy()

    np.testing.assert_allclose(principal_angle_degrees(left, right), [0.0, 0.0], atol=1e-12)
    assert projector_similarity(left, right) == pytest.approx(1.0)


def test_projector_similarity_is_zero_for_orthogonal_subspaces() -> None:
    left = np.eye(4, dtype=np.float64)[:, :2]
    right = np.eye(4, dtype=np.float64)[:, 2:]

    np.testing.assert_allclose(principal_angle_degrees(left, right), [90.0, 90.0], atol=1e-12)
    assert projector_similarity(left, right) == pytest.approx(0.0)
