"""Calibration outcome reporting that preserves prospective stop semantics."""

from __future__ import annotations

from .metrics import CRITERION_NAMES


def f1_acceptance_review() -> dict:
    """Return the frozen 20-point review after a prospective F1 stop."""

    evidence = {
        1: ("PARTIAL_PASS", "Three-repeat smoke replay was exact; the frozen cohort was not run."),
        2: ("FAIL", "Full versus bounded scores exceeded the frozen 1e-5 tolerance."),
        3: ("FAIL", "One-shot cached versus full recomputation exceeded the frozen 1e-5 tolerance."),
        4: ("PARTIAL_PASS", "Full-path K, V, KV, and residual self patches passed; matched-path event-span validation was not completed."),
        5: ("PARTIAL_PASS", "Smoke patch audits were selective; cohort-wide validation was stopped."),
        6: ("PARTIAL_PASS", "The smoke observed 36 layers, 32 query heads, 8 KV heads, and 128 head dimension; cohort-wide replay was stopped."),
        7: ("PARTIAL_PASS", "Every executed smoke and diagnostic score was finite; later layers were not run."),
    }
    criteria = []
    for criterion_id in range(1, 21):
        status, detail = evidence.get(
            criterion_id,
            ("NOT_RUN", "Not run because the prospective F1 full/cached parity stop fired in Layer A."),
        )
        criteria.append({
            "criterion_id": criterion_id,
            "criterion": CRITERION_NAMES[criterion_id],
            "status": status,
            "passed": status == "PASS",
            "detail": detail,
        })
    return {
        "overall_status": "FAIL",
        "failure_code": "F1",
        "failure_reason": "full/cached scoring parity failure under prospectively frozen tolerance",
        "stage3c9_restart_authorized": False,
        "criteria": criteria,
    }


__all__ = ["f1_acceptance_review"]
