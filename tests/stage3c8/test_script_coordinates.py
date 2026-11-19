from __future__ import annotations

from scripts.stage3c8.run_phase_a import coordinates


def test_validation_manifest_without_state_pairs_uses_fresh_like_coordinates() -> None:
    event = {"ed_generated_index": 230}
    assert coordinates({"base_problem_id": "3"}, event, "validation") == [
        ("a_like", 230),
        ("b_like", 229),
    ]


def test_validation_manifest_with_state_pairs_preserves_historical_coordinates() -> None:
    item = {
        "state_pairs": [
            {"target_id": "target_a", "state_R": {"generated_index": 99}},
            {"target_id": "target_b", "state_R": {"generated_index": 98}},
        ]
    }
    assert coordinates(item, {"ed_generated_index": 100}, "validation") == [
        ("target_a", 99),
        ("target_b", 98),
    ]
