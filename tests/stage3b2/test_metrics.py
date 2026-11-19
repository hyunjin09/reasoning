import pytest

from visual_reasoning.stage3b2.metrics import normalize_by_evidence_gap, switch_metrics


def test_switch_metrics_are_positive_when_both_directions_follow_source() -> None:
    metrics = switch_metrics(d_oo=2.0, d_oc=-1.0, d_cc=-2.0, d_co=1.0, d_os=1.9)

    assert metrics["S_O_to_C"] == 3.0
    assert metrics["S_C_to_O"] == 3.0
    assert metrics["BRI"] == 3.0
    assert metrics["S_O_to_Sham"] == pytest.approx(0.1)
    assert metrics["O_to_C_source_consistent"] is True
    assert metrics["C_to_O_source_consistent"] is True
    assert metrics["bidirectionally_source_consistent"] is True


def test_normalization_is_undefined_for_nonpositive_evidence_gap() -> None:
    assert normalize_by_evidence_gap(0.5, -0.002) is None
    assert normalize_by_evidence_gap(0.5, 0.0) is None
    assert normalize_by_evidence_gap(0.5, 2.0) == 0.25
