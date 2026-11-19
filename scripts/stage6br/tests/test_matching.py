import json
from pathlib import Path

from scripts.stage6br.matching import match_priority, maximum_matching


RULES = json.loads(Path('outputs/stage6br/config/hold_matching_rules.json').read_text())


def row(name, **kwargs):
    return dict(id=name, base_id='a', dataset='d', condition='intact', split='discovery',
                readout_type='V', evidence_class='LENGTH_LABEL', token_gap=10,
                normalized_progress=.1, demand_after=['A']) | kwargs


def test_cross_base_fold_and_gap_constraints():
    assert match_priority(row('t'), row('h', base_id='b'), RULES) is not None
    assert match_priority(row('t'), row('h', split='confirmation'), RULES) is None
    assert match_priority(row('t'), row('h', token_gap=21), RULES) is None
    assert match_priority(row('t'), row('h', base_id='b', normalized_progress=.3), RULES) is None


def test_augmenting_path_recovers_a_pair_greedy_would_lose():
    transitions = [row('t1'), row('t2', token_gap=30)]
    holds = [row('h1', token_gap=20), row('h2', token_gap=5)]
    pairs, _ = maximum_matching(transitions, holds, RULES)
    assert set(pairs) == {('t1', 'h2'), ('t2', 'h1')}


def test_no_hold_reuse():
    pairs, _ = maximum_matching([row('t1'), row('t2')], [row('h')], RULES)
    assert len(pairs) == 1
