from copy import deepcopy

from visual_reasoning.stage8c.analysis_fp32 import development_decision as original
from visual_reasoning.stage8c.analysis_fp32_reviewed import development_decision


def fixture():
    row = dict(correct=False, normal_eos=True, at_length_cap=False,
               reasoning_tokens=100, tokens=110, actual_interventions=0, elapsed_seconds=1)
    arms = {g: {str(i): dict(row, correct=i < 64) for i in range(128)}
            for g in (1., 1.25, 1.5, 2.)}
    metadata = {str(i): {'subject': str(i % 4)} for i in range(128)}
    return arms, metadata


def test_review_must_be_closed_and_unresolved_stays_unresolved():
    arms, metadata = fixture()
    for arm in arms.values():
        arm['127']['correct'] = None
    arms[1.25]['126']['correct'] = True
    saved = deepcopy(arms)
    assert development_decision(arms, metadata)['status'] == 'awaiting_blind_extraction'
    result = development_decision(arms, metadata, extraction_review_closed=True)
    assert result['dose'] == 1.25
    assert result['details'][1.25]['transitions'] == dict(WtoC=1, CtoW=0, CtoC=64, WtoW=62, unresolved=1)
    assert result['details'][1.25]['summary']['accuracy'] == 65/128
    assert arms == saved


def test_resolving_unknown_to_correct_is_not_a_wrong_to_correct_rescue():
    arms, metadata = fixture()
    for arm in arms.values():
        arm['127']['correct'] = None
    arms[1.25]['127']['correct'] = True
    result = development_decision(arms, metadata, extraction_review_closed=True)
    assert result['status'] == 'stop_dev_no_go'
    assert result['details'][1.25]['transitions']['WtoC'] == 0
    assert result['details'][1.25]['transitions']['unresolved'] == 1


def test_fully_resolved_decisions_match_frozen_rules():
    arms, metadata = fixture()
    for gain in (1.25, 1.5, 2.):
        arms[gain]['126']['correct'] = True
    assert development_decision(arms, metadata, extraction_review_closed=True) == original(arms, metadata)
    assert development_decision(arms, metadata, extraction_review_closed=True)['dose'] == 1.25
