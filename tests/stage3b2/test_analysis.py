from visual_reasoning.stage3b2.analysis import (
    bootstrap_interval,
    checkpoint_passes_go_rule,
    match_switch_and_cutoff_timings,
    retrieval_category,
)


def _row(index: int, normalized: float | None, *, labels: list[str], both: bool = True) -> dict:
    return {
        "switch_generated_index": index,
        "labels": labels,
        "normalized_BRI_raw": normalized,
        "bidirectionally_source_consistent": both,
    }


def test_retrieval_category_identifies_persistent_late_source_control() -> None:
    curve = [
        _row(0, 0.2, labels=["generation_start"]),
        _row(9, 0.6, labels=["Ed_minus_1"]),
        _row(10, 0.7, labels=["Ed"]),
    ]

    assert retrieval_category(curve) == "R1_persistent_late_retrieval"


def test_retrieval_category_identifies_weak_identity_specific_retrieval() -> None:
    curve = [
        _row(0, 0.05, labels=["generation_start"]),
        _row(9, 0.10, labels=["Ed_minus_1"], both=False),
        _row(10, 0.20, labels=["Ed"], both=False),
    ]

    assert retrieval_category(curve) == "R4_weak_identity_specific_retrieval"


def test_bootstrap_interval_is_deterministic() -> None:
    first = bootstrap_interval([1.0, 2.0, 3.0], statistic="median", resamples=1000, seed=9)
    second = bootstrap_interval([1.0, 2.0, 3.0], statistic="median", resamples=1000, seed=9)

    assert first == second
    assert first[0] <= 2.0 <= first[1]


def test_matching_timings_requires_identical_query_index() -> None:
    switch = [
        {"switch_generated_index": 0, "BRI": 1.0},
        {"switch_generated_index": 8, "BRI": 2.0},
    ]
    cutoff = [
        {"cutoff_generated_index": 0, "CE": 0.1},
        {"cutoff_generated_index": 7, "CE": 0.2},
    ]

    matched = match_switch_and_cutoff_timings(switch, cutoff)

    assert len(matched) == 1
    assert matched[0]["generated_index"] == 0


def test_checkpoint_go_rule_enforces_sham_and_bidirectional_controls() -> None:
    summary = {
        "BRI": {"median_bootstrap_ci": {"ci_low": 1.0, "ci_high": 2.0}},
        "bidirectional_source_consistency": {"proportion": 0.80},
        "normalized_BRI_raw": {"median": 0.75},
        "median_absolute_S_O_to_C": 2.0,
        "median_absolute_sham": 0.1,
        "all_self_switches_exact": True,
    }

    assert checkpoint_passes_go_rule(summary)
    summary["median_absolute_sham"] = 0.5
    assert not checkpoint_passes_go_rule(summary)
