from visual_reasoning.stage3b2.annotations import discriminative_event


def test_discriminative_event_uses_longest_common_token_prefix() -> None:
    event = discriminative_event(
        e0_start_token=26,
        original_candidate_ids=[10, 11, 24, 99],
        counterfactual_candidate_ids=[10, 11, 48, 99],
    )

    assert event["common_prefix_token_ids"] == [10, 11]
    assert event["original_divergent_suffix_ids"] == [24, 99]
    assert event["counterfactual_divergent_suffix_ids"] == [48, 99]
    assert event["ed_generated_index"] == 28
    assert event["first_original_divergent_token_id"] == 24
    assert event["first_counterfactual_divergent_token_id"] == 48


def test_discriminative_event_rejects_identical_candidates() -> None:
    try:
        discriminative_event(
            e0_start_token=3,
            original_candidate_ids=[1, 2],
            counterfactual_candidate_ids=[1, 2],
        )
    except ValueError as error:
        assert "must diverge" in str(error)
    else:
        raise AssertionError("Identical evidence candidates must be rejected")
