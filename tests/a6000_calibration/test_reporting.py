from __future__ import annotations

from visual_reasoning.a6000_calibration.reporting import f1_acceptance_review


def test_f1_acceptance_review_stops_after_required_parity_failures() -> None:
    review = f1_acceptance_review()
    assert review["overall_status"] == "FAIL"
    assert review["failure_code"] == "F1"
    assert len(review["criteria"]) == 20
    assert review["criteria"][1]["status"] == "FAIL"
    assert review["criteria"][2]["status"] == "FAIL"
    assert all(row["status"] == "NOT_RUN" for row in review["criteria"][7:])
    assert review["stage3c9_restart_authorized"] is False
