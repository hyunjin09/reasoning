from __future__ import annotations

import torch
import pytest

from visual_reasoning.stage3c3.protocol import (
    choose_query_formulation,
    phase_a_target_passes,
    split_validation_primary,
)
from visual_reasoning.stage3c3.metrics import summarize_routing_state
from visual_reasoning.stage3c3.runtime import (
    evidence_suffix_logit_rows,
    splice_current_query_heads,
)


def test_split_is_deterministic_disjoint_and_preserves_24_primary_bases() -> None:
    bases = [str(value) for value in range(31)]
    first = split_validation_primary(bases, validation_count=7, seed=20260903)
    second = split_validation_primary(bases, validation_count=7, seed=20260903)

    assert first == second
    assert len(first["validation"]) == 7
    assert len(first["primary"]) == 24
    assert set(first["validation"]).isdisjoint(first["primary"])
    assert set(first["validation"]) | set(first["primary"]) == set(bases)


def test_query_splice_changes_only_selected_heads_at_recipient_position() -> None:
    recipient = torch.arange(1 * 4 * 5 * 3, dtype=torch.float32).reshape(1, 4, 5, 3)
    donor = torch.full((1, 4, 3), -7.0)

    patched, audit = splice_current_query_heads(
        recipient,
        donor,
        recipient_position=3,
        selected_heads=[1, 3],
    )

    assert torch.equal(patched[:, :, :3], recipient[:, :, :3])
    assert torch.equal(patched[:, :, 4:], recipient[:, :, 4:])
    assert torch.equal(patched[:, 0, 3], recipient[:, 0, 3])
    assert torch.equal(patched[:, 2, 3], recipient[:, 2, 3])
    assert torch.equal(patched[:, 1, 3], donor[:, 1])
    assert torch.equal(patched[:, 3, 3], donor[:, 3])
    assert audit["changed_sequence_positions"] == [3]
    assert audit["changed_query_heads"] == [1, 3]
    assert audit["nonselected_head_max_abs_delta"] == 0.0


def test_query_splice_rejects_incompatible_donor_layout() -> None:
    recipient = torch.zeros((1, 4, 5, 3))
    donor = torch.zeros((1, 3, 3))
    try:
        splice_current_query_heads(
            recipient,
            donor,
            recipient_position=3,
            selected_heads=[1],
        )
    except ValueError as error:
        assert "donor" in str(error).lower()
    else:
        raise AssertionError("an incompatible donor query must be rejected")


def test_evidence_rows_score_only_suffix_after_native_bridge() -> None:
    assert evidence_suffix_logit_rows(
        prompt_length=100,
        prefix_length=15,
        bridge_length=16,
        suffix_length=3,
    ) == [130, 131, 132]


def test_routing_summary_keeps_per_head_and_region_normalization() -> None:
    state = {
        "post_rope_query": torch.tensor([[[1.0, 0.0], [0.0, 1.0]]]),
        "key": torch.tensor([[[[1.0, 0.0], [0.0, 1.0], [1.0, 1.0], [-1.0, 0.0]]]]),
        "value": torch.ones((1, 1, 4, 2)),
        "attention": torch.tensor([[[0.4, 0.2, 0.3, 0.1], [0.1, 0.5, 0.2, 0.2]]]),
        "wo_weight": torch.eye(4),
        "scaling": 2.0**-0.5,
        "num_key_value_groups": 2,
    }
    groups = {"T": [0], "M": [1], "I": [2], "sink": [3]}

    result = summarize_routing_state(state, groups=groups, selected_heads=[0, 1])

    assert result["groups"]["T"]["token_count"] == 1
    assert result["groups"]["T"]["mean_attention_mass"] == pytest.approx(0.25)
    assert result["groups"]["M"]["mean_attention_density"] == pytest.approx(0.35)
    assert result["RDS_T_vs_M"] == pytest.approx(0.0)
    assert result["ADG_T_vs_M"] == pytest.approx(-0.1)
    assert len(result["per_head"]) == 2
    assert evidence_suffix_logit_rows(
        prompt_length=100,
        prefix_length=31,
        bridge_length=0,
        suffix_length=3,
    ) == [130, 131, 132]


def test_routing_summary_uses_only_causally_visible_kv_prefix() -> None:
    """Candidate scoring includes future suffix K/V, but the frozen row cannot see it."""

    state = {
        "post_rope_query": torch.tensor([[[1.0, 0.0], [0.0, 1.0]]]),
        "key": torch.ones((1, 1, 5, 2)),
        "value": torch.ones((1, 1, 5, 2)),
        "attention": torch.tensor([[[0.4, 0.2, 0.3, 0.1], [0.1, 0.5, 0.2, 0.2]]]),
        "wo_weight": torch.eye(4),
        "scaling": 2.0**-0.5,
        "num_key_value_groups": 2,
    }

    result = summarize_routing_state(
        state,
        groups={"T": [0], "M": [1], "I": [2], "sink": [3]},
        selected_heads=[0, 1],
    )

    assert result["visible_source_token_count"] == 4
    assert result["stored_kv_token_count"] == 5


def test_content_space_form_is_selected_from_mechanics_not_effect_size() -> None:
    audits = {
        "direct_post_rope": {
            "self_exact": True,
            "kv_exact": True,
            "nonselected_heads_exact": True,
            "deterministic": True,
            "routing_effect": 1000.0,
        },
        "content_recipient_rope": {
            "self_exact": True,
            "kv_exact": True,
            "nonselected_heads_exact": True,
            "deterministic": True,
            "routing_effect": -1000.0,
        },
    }

    selected = choose_query_formulation(audits)

    assert selected == "content_recipient_rope"


def test_formulation_selection_rejects_mechanically_invalid_forms() -> None:
    invalid = {
        "direct_post_rope": {
            "self_exact": False,
            "kv_exact": True,
            "nonselected_heads_exact": True,
            "deterministic": True,
        },
        "content_recipient_rope": {
            "self_exact": True,
            "kv_exact": False,
            "nonselected_heads_exact": True,
            "deterministic": True,
        },
    }
    try:
        choose_query_formulation(invalid)
    except ValueError as error:
        assert "mechanically valid" in str(error)
    else:
        raise AssertionError("invalid formulations must stop the protocol")


def test_phase_a_gate_requires_every_chain_and_control_condition() -> None:
    passing = {
        "necessity": {
            "routing_median": 0.2,
            "routing_positive_fraction": 0.75,
            "alpha_v_median": 0.1,
            "evidence_median": 0.05,
        },
        "sufficiency": {
            "routing_median": 0.3,
            "routing_positive_fraction": 0.75,
            "alpha_v_median": 0.2,
            "evidence_median": 0.04,
        },
        "causal_minus_noncausal_median": 0.1,
        "self_exact": True,
    }
    assert phase_a_target_passes(passing)

    for field in ("routing_median", "alpha_v_median", "evidence_median"):
        failing = {
            **passing,
            "necessity": {**passing["necessity"], field: -0.01},
        }
        assert not phase_a_target_passes(failing)
    assert not phase_a_target_passes({**passing, "causal_minus_noncausal_median": -0.01})
    assert not phase_a_target_passes({**passing, "self_exact": False})
