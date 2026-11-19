import numpy as np
from visual_reasoning.stage7a.metrics import source_effect, semantic_effect, distribution_similarity


def test_wrong_token_and_truth_margin_can_point_opposite_directions():
    # Correct=-2, wrong=-1 initially; after removing X correct=-5, wrong=-3.
    # X promotes the wrong token, but promotes the correct token even more.
    native = dict(D=-1., observed_claim_log_probability=-1., observed_minus_correct=1.,
                  first_wrong_token_log_probability=-1., wrong_minus_correct_token_margin=1.)
    off = dict(D=-2., observed_claim_log_probability=-3., observed_minus_correct=2.,
               first_wrong_token_log_probability=-3., wrong_minus_correct_token_margin=2.)
    effect = source_effect(native, off)
    assert effect['EP_token'] == 2 and effect['EP_margin'] == -1 and effect['VSD'] == 1


def test_full_claim_margin_cannot_replace_a_missing_correct_token():
    native = dict(D=-1., observed_claim_log_probability=-1., observed_minus_correct=1.,
                  first_wrong_token_log_probability=-1., wrong_minus_correct_token_margin=None)
    off = dict(D=-2., observed_claim_log_probability=-3., observed_minus_correct=-1.,
               first_wrong_token_log_probability=-3., wrong_minus_correct_token_margin=None)
    effect = source_effect(native, off)
    assert effect['EP_margin'] is None and effect['EP_claim_margin'] == 2


def test_sham_movement_cannot_be_claimed_as_semantic_followability():
    def arm(new, old):
        return dict(D=old-new, candidates={'target_semantic': {'mean_log_probability': new},
                                          'correct': {'mean_log_probability': old}})
    effect = semantic_effect(arm(-4, -1), arm(-1, -2), arm(-1, -2), 'T')
    assert effect['semantic_shift'] == 4 and effect['net_semantic_beyond_sham'] == 0


def test_alternative_semantic_effect_uses_its_own_original_value():
    def arm(new, old, value_foil):
        return dict(D=0., candidates={'alternative_semantic': {'mean_log_probability': new},
                    'alternative_original': {'mean_log_probability': old},
                    'foil': {'mean_log_probability': value_foil}})
    effect = semantic_effect(arm(-4, -1, -9), arm(-4, -1, -2), arm(-1, -4, -10), 'X')
    assert effect['net_semantic_beyond_sham'] == 6 and effect['sham_shift'] == 0


def test_distribution_similarity_is_symmetric_and_zero_for_same_logits():
    a = np.linspace(-30, -1, 100)
    b = a[::-1].copy()
    same = distribution_similarity(a, a)
    assert same['JS_nats'] < 1e-12 and same['top50_overlap'] == 1
    assert abs(distribution_similarity(a, b)['JS_nats']-distribution_similarity(b, a)['JS_nats']) < 1e-12
