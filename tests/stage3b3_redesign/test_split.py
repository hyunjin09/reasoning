from visual_reasoning.stage3b3_redesign.split import freeze_method_validation_split


def test_split_is_seeded_numeric_only_and_reserves_the_remainder() -> None:
    rows = [
        {"base_problem_id": str(index), "edit_tier": "tier1_local_numeric_label"}
        for index in range(10)
    ] + [
        {"base_problem_id": "99", "edit_tier": "tier3_structural_visual_edit"}
    ]
    exact = {"0", "1", "2"}

    first = freeze_method_validation_split(rows, exact_base_ids=exact, seed=20260901)
    second = freeze_method_validation_split(rows, exact_base_ids=exact, seed=20260901)

    assert first == second
    assert len(first["validation_base_problem_ids"]) == 8
    assert len(set(first["validation_base_problem_ids"]) & exact) >= 2
    assert "99" not in first["validation_base_problem_ids"]
    assert set(first["validation_base_problem_ids"]) | set(first["primary_base_problem_ids"]) == {
        str(index) for index in range(10)
    } | {"99"}
    assert not set(first["validation_base_problem_ids"]) & set(first["primary_base_problem_ids"])

