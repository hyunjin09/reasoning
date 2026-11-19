from visual_reasoning.stage3b3_redesign.primary import (
    apply_redesign_fine_rule,
    balanced_primary_shards,
    evaluate_localization_decision,
)


def test_balanced_primary_shards_preserves_every_base_once():
    rows = [
        {"base_problem_id": str(index), "edit_tier": "tier1_local_numeric_label"}
        for index in range(7)
    ] + [
        {"base_problem_id": "s0", "edit_tier": "tier2_structural_edit"},
        {"base_problem_id": "s1", "edit_tier": "tier2_structural_edit"},
    ]

    shards = balanced_primary_shards(rows, shard_count=3)

    observed = [row["base_problem_id"] for shard in shards for row in shard]
    assert sorted(observed) == sorted(row["base_problem_id"] for row in rows)
    assert len(observed) == len(set(observed))


def test_balanced_primary_shards_keeps_estimated_load_close():
    rows = [
        {"base_problem_id": str(index), "edit_tier": "tier1_local_numeric_label"}
        for index in range(8)
    ] + [
        {"base_problem_id": f"s{index}", "edit_tier": "tier2_structural_edit"}
        for index in range(4)
    ]

    shards = balanced_primary_shards(rows, shard_count=4)
    loads = [
        sum(0.55 if "structural" in row["edit_tier"] else 1.0 for row in shard)
        for shard in shards
    ]

    assert max(loads) - min(loads) <= 0.55


def _stat(coordinate: str, name: str, *, bws: float = 0.0, bsrc: float = 0.0):
    def metric(value: float):
        return {"median": value, "median_bootstrap_95_ci": [value - 0.01, value + 0.01]}

    return {
        "coordinate": coordinate,
        "name": name,
        "statistics": {
            "BWS_normalized": metric(bws),
            "BSRC_normalized": metric(bsrc),
        },
    }


def test_redesign_fine_rule_uses_primary_bws_and_semantic_restoration_only():
    rows = [
        _stat(coordinate, f"W{index}", bws=0.21 if coordinate == "Ed" and index == 2 else 0.0)
        for coordinate in ("Ed_minus_1", "Ed")
        for index in range(6)
    ]

    gate = apply_redesign_fine_rule(rows)

    assert gate["qualified_by_coordinate"] == {"Ed": ["W2"]}
    assert gate["qualifying_union"] == ["W2"]
    assert {row["parent_window"] for row in gate["fine_windows"]} == {"W1", "W2", "W3"}
    assert gate["restoration_metric_replacing_original_BWN"] == "BSRC_normalized"


def _decision_row(coordinate: str, name: str, bws: float, bsrc: float):
    return {
        "coordinate": coordinate,
        "name": name,
        "BWS_median": bws,
        "BWS_ci_low": bws - 0.01,
        "BSRC_median": bsrc,
        "BSRC_ci_low": bsrc - 0.01,
        "sufficiency_bidirectional_fraction": 0.8,
        "restoration_bidirectional_fraction": 0.8,
        "selective_sham_to_target_ratio": 0.05,
        "restoration_render_to_semantic_ratio": 0.05,
    }


def test_localization_decision_prioritizes_validated_narrow_hotspot():
    coarse = [_decision_row("Ed", "W2", 0.3, 0.25)]
    fine = [{"coordinate": "Ed", "parent_window": "W2", "BWS_median": 0.16, "BSRC_median": 0.10}]

    decision = evaluate_localization_decision(coarse, fine, [], controls_pass=True)

    assert decision["recommendation"] == "GO — Module/path localization"


def test_localization_decision_uses_distributed_rule_when_no_narrow_hotspot():
    coarse = [_decision_row("Ed", f"W{index}", 0.11, 0.05) for index in range(3)]

    decision = evaluate_localization_decision(coarse, [], [], controls_pass=True)

    assert decision["recommendation"] == "GO — Distributed layer mechanism analysis"


def test_localization_decision_redesigns_when_controls_fail():
    decision = evaluate_localization_decision([], [], [], controls_pass=False)

    assert decision["recommendation"] == "REDESIGN"
