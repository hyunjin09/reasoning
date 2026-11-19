import pytest

from scripts.stage3b9.analyze_phase_a import select_confirmation_results
from scripts.stage3b9.analyze_secondary import select_cohort_results
from scripts.stage3b9.finalize_stage import classify_geometry


def test_full_v_screening_extras_are_filtered_after_applicability_freeze() -> None:
    rows = {"10": {"value": 10}, "11": {"value": 11}, "12": {"value": 12}}

    selected = select_confirmation_results(
        rows, ["10", "12"], name="full", allow_screening_extras=True
    )

    assert selected == {"10": {"value": 10}, "12": {"value": 12}}


def test_projected_results_require_exact_frozen_cohort() -> None:
    with pytest.raises(RuntimeError, match=r"missing=\['12'\], extras=\['11'\]"):
        select_confirmation_results(
            {"10": {}, "11": {}}, ["10", "12"], name="learned"
        )


def test_secondary_filters_pre_gate_full_v_extras() -> None:
    rows = {"10": {"value": 10}, "11": {"value": 11}, "12": {"value": 12}}

    assert select_cohort_results(rows, ["10", "12"]) == {
        "10": {"value": 10},
        "12": {"value": 12},
    }


def test_joint_geometry_classification_uses_frozen_outcome_matrix() -> None:
    shared = {
        "targets": {
            "target_a": {"k_shared": None, "geometry_label": "No-Robust-Shared-Compression"},
            "target_b_r": {"k_shared": None, "geometry_label": "No-Robust-Shared-Compression"},
        }
    }
    local = {
        "targets": {
            "target_a": {"local_low_dimensional": True},
            "target_b_r": {"local_low_dimensional": True},
        }
    }

    assert classify_geometry(shared, local)["joint_label"] == (
        "G2 — Local low-dimensional / global heterogeneous"
    )
