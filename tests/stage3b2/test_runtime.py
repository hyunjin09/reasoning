from visual_reasoning.stage3b2.runtime import (
    classify_first_discriminative_token,
    stage3a_divergent_tail_exact,
)


def test_stage3a_divergent_tail_exact_matches_candidate_tail() -> None:
    observed = {
        "candidate_token_ids": [30, 31],
        "token_log_probabilities": [-0.2, -0.3],
    }
    expected = {
        "candidate_token_ids": [10, 11, 30, 31],
        "token_log_probabilities": [-0.7, -0.8, -0.2, -0.3],
    }

    assert stage3a_divergent_tail_exact(observed, expected, common_prefix_token_count=2)


def test_stage3a_divergent_tail_exact_rejects_score_change() -> None:
    observed = {
        "candidate_token_ids": [30],
        "token_log_probabilities": [-0.2001],
    }
    expected = {
        "candidate_token_ids": [10, 30],
        "token_log_probabilities": [-0.7, -0.2],
    }

    assert not stage3a_divergent_tail_exact(observed, expected, common_prefix_token_count=1)


def test_classify_first_discriminative_token_uses_frozen_identity_tokens() -> None:
    assert classify_first_discriminative_token([24, 9], original_token_id=24, counterfactual_token_id=48) == "original"
    assert classify_first_discriminative_token([48], original_token_id=24, counterfactual_token_id=48) == "counterfactual"
    assert classify_first_discriminative_token([7], original_token_id=24, counterfactual_token_id=48) == "other"
    assert classify_first_discriminative_token([], original_token_id=24, counterfactual_token_id=48) == "no_token"
