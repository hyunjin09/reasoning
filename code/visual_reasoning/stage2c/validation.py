"""Schema checks for Stage 2C event annotations."""

from __future__ import annotations


def validate_event_annotation(row: dict, token_count: int) -> list[str]:
    failures: list[str] = []
    total = int(token_count)
    try:
        e0_start = int(row["e0"]["start_token"])
        e0_end = int(row["e0"]["end_token"])
        fact_start = int(row["e1"]["fact_start_token"])
        e1 = int(row["e1"]["completion_token"])
        e2_start = int(row["e2"]["start_token"])
        e2_end = int(row["e2"]["end_token"])
    except (KeyError, TypeError, ValueError) as exc:
        return [f"missing or invalid event field: {exc}"]
    if not 0 <= e0_start < e0_end <= total:
        failures.append("E0 interval is outside the trace")
    if not 0 <= e0_start <= fact_start <= e1 < total:
        failures.append("E1 must complete at or after E0 inside the trace")
    if not e1 < e2_start < e2_end <= total:
        failures.append("E2 must be a later nonempty downstream-use interval")
    for index, mention in enumerate(row.get("repeated_mentions", [])):
        start, end = int(mention["start_token"]), int(mention["end_token"])
        if not e1 < start < end <= total:
            failures.append(f"repeated mention {index} must occur after E1")
    return failures
