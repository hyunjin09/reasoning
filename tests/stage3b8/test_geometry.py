from __future__ import annotations

import torch

from visual_reasoning.stage3b8.geometry import (
    fit_right_singular_subspace,
    interpolate_head_delta,
    project_rows,
    roi_value_contribution,
    select_discovery_rank,
    symmetric_semantic_delta,
)


def test_random_orthonormal_basis_is_reproducible_and_orthonormal() -> None:
    from visual_reasoning.stage3b8.geometry import random_orthonormal_basis

    first = random_orthonormal_basis(dimension=12, rank=4, seed=19)
    second = random_orthonormal_basis(dimension=12, rank=4, seed=19)
    assert torch.equal(first, second)
    assert torch.allclose(first.T @ first, torch.eye(4, dtype=first.dtype), atol=1e-12)
from visual_reasoning.stage3b8.heads import roi_head_delta_from_states


def test_roi_value_contribution_respects_gqa_and_roi_positions() -> None:
    weights = torch.zeros(1, 4, 2, 5)
    weights[0, 0, 1, [1, 3]] = torch.tensor([0.25, 0.75])
    weights[0, 2, 1, [1, 3]] = torch.tensor([0.6, 0.4])
    values = torch.zeros(1, 2, 5, 2)
    values[0, 0, 1] = torch.tensor([2.0, 4.0])
    values[0, 0, 3] = torch.tensor([6.0, 8.0])
    values[0, 1, 1] = torch.tensor([10.0, 12.0])
    values[0, 1, 3] = torch.tensor([14.0, 16.0])

    result = roi_value_contribution(
        attention_weights=weights,
        values=values,
        current_position=1,
        selected_query_heads=[0, 2],
        roi_positions=[1, 3],
    )

    assert result.shape == (1, 2, 2)
    torch.testing.assert_close(result[0, 0], torch.tensor([5.0, 7.0]))
    torch.testing.assert_close(result[0, 1], torch.tensor([11.6, 13.6]))


def test_interpolate_head_delta_changes_only_selected_current_heads() -> None:
    native = torch.zeros(1, 3, 4, 2)
    delta = torch.tensor([[[2.0, 4.0], [6.0, 8.0]]])
    patched, audit = interpolate_head_delta(
        native,
        delta,
        current_position=2,
        selected_query_heads=[1, 3],
        dose=0.25,
    )
    expected = torch.zeros_like(native)
    expected[0, 2, 1] = torch.tensor([0.5, 1.0])
    expected[0, 2, 3] = torch.tensor([1.5, 2.0])
    torch.testing.assert_close(patched, expected)
    assert audit["changed_sequence_positions"] == [2]
    assert audit["changed_query_heads"] == [1, 3]
    assert audit["nonselected_head_max_abs_delta"] == 0.0


def test_symmetric_delta_and_projection_are_consistent() -> None:
    z_oo = torch.tensor([1.0, 3.0, 5.0])
    z_oc = torch.tensor([0.0, 1.0, 4.0])
    z_co = torch.tensor([4.0, 2.0, 2.0])
    z_cc = torch.tensor([2.0, 1.0, 0.0])
    delta = symmetric_semantic_delta(z_oo=z_oo, z_oc=z_oc, z_co=z_co, z_cc=z_cc)
    torch.testing.assert_close(delta, torch.tensor([1.5, 1.5, 1.5]))

    rows = torch.tensor([[3.0, 0.0], [2.0, 0.0], [0.0, 1.0]])
    basis, singular_values = fit_right_singular_subspace(rows)
    assert basis.shape == (2, 2)
    assert singular_values[0] > singular_values[1]
    parallel = project_rows(rows, basis[:, :1])
    perpendicular = rows - parallel
    torch.testing.assert_close(parallel[:, 1], torch.zeros(3), atol=1e-6, rtol=0)
    torch.testing.assert_close(perpendicular[:, 0], torch.zeros(3), atol=1e-6, rtol=0)


def test_rank_selection_uses_smallest_passing_rank_or_best_tradeoff() -> None:
    passing = [
        {"rank": 1, "median_projected_ratio": 0.70, "median_complement_ratio": 0.20},
        {"rank": 2, "median_projected_ratio": 0.82, "median_complement_ratio": 0.29},
        {"rank": 4, "median_projected_ratio": 0.91, "median_complement_ratio": 0.10},
    ]
    assert select_discovery_rank(passing) == {
        "rank": 2,
        "rule_satisfied": True,
        "selection_reason": "smallest rank meeting projected>=0.80 and complement<=0.30",
    }

    partial = [
        {"rank": 1, "median_projected_ratio": 0.60, "median_complement_ratio": 0.30},
        {"rank": 2, "median_projected_ratio": 0.72, "median_complement_ratio": 0.42},
        {"rank": 4, "median_projected_ratio": 0.76, "median_complement_ratio": 0.38},
    ]
    selected = select_discovery_rank(partial)
    assert selected["rank"] == 4
    assert selected["rule_satisfied"] is False


def test_roi_head_delta_uses_recipient_routing_and_optional_projector() -> None:
    attention = torch.zeros(1, 4, 5)
    attention[0, 0, [1, 3]] = torch.tensor([0.25, 0.75])
    attention[0, 2, [1, 3]] = torch.tensor([0.5, 0.5])
    recipient_value = torch.zeros(1, 2, 5, 2)
    donor_value = recipient_value.clone()
    donor_value[0, 0, 1] = torch.tensor([2.0, 0.0])
    donor_value[0, 0, 3] = torch.tensor([6.0, 0.0])
    donor_value[0, 1, 1] = torch.tensor([0.0, 4.0])
    donor_value[0, 1, 3] = torch.tensor([0.0, 8.0])
    recipient = {"current_attention_weights": attention, "value": recipient_value}
    donor = {"current_attention_weights": attention, "value": donor_value}

    full, audit = roi_head_delta_from_states(
        recipient_state=recipient,
        donor_state=donor,
        selected_query_heads=[0, 2],
        roi_positions=[1, 3],
    )
    torch.testing.assert_close(full, torch.tensor([[[5.0, 0.0], [0.0, 6.0]]]))
    assert audit["flattened_dimension"] == 4
    basis = torch.tensor([[1.0], [0.0], [0.0], [0.0]])
    projected, projected_audit = roi_head_delta_from_states(
        recipient_state=recipient,
        donor_state=donor,
        selected_query_heads=[0, 2],
        roi_positions=[1, 3],
        projector_basis=basis,
    )
    torch.testing.assert_close(projected, torch.tensor([[[5.0, 0.0], [0.0, 0.0]]]))
    assert projected_audit["projector_rank"] == 1
    complement, complement_audit = roi_head_delta_from_states(
        recipient_state=recipient,
        donor_state=donor,
        selected_query_heads=[0, 2],
        roi_positions=[1, 3],
        projector_basis=basis,
        projector_complement=True,
    )
    torch.testing.assert_close(complement, full - projected)
    assert complement_audit["projector_component"] == "orthogonal_complement"
