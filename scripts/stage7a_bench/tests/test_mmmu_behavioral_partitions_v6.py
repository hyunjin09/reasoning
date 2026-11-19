from copy import deepcopy

import pytest

from scripts.stage7a_bench.mmmu_behavioral_partitions_v6 import CONDITIONS, summarize_pairs


def packet():
    groups = {c: [] for c in CONDITIONS}
    finals = {'a': (True, False, False), 'b': (False, True, False),
              'c': (True, None, False), 'd': (True, False, False)}
    for base, triple in finals.items():
        for c, final in zip(CONDITIONS, triple):
            groups[c].append(dict(base_id=base, benchmark='mmmu_pro', condition=c,
                event_id=base+'__'+c, final_correctness=final,
                truncation=base == 'd' and c == 'silent_no_image',
                local_visual_claim_present=True, unsupported_evidence_claim=c != 'image_present'))
    return groups, list(finals), dict(a='f1', b='f1', c='f2', d='f3')


def test_partial_unknown_and_capped_answers_do_not_become_clean_failures():
    result = summarize_pairs(*packet())
    assert result['partitions']['both_absent_conditions_wrong']['base_ids'] == ['a']
    assert result['partitions']['some_absent_condition_correct']['base_ids'] == ['b']
    assert result['partitions']['unresolved_absent_conditions']['base_ids'] == ['c', 'd']
    assert result['visual_correct_and_both_absent_wrong']['base_ids'] == ['a']
    assert result['paired_universe']['source_families'] == 3
    assert result['paired_universe']['bases_by_source_family']['f1'] == 2
    assert result['causal_states_assigned'] is False
    assert result['subset_selected'] is False
    b = result['paired_evidence'][1]['conditions']['silent_no_image']
    assert b['outcome'] == 'correct' and b['unsupported_claim'] is True


def test_missing_response_stays_missing_and_extra_visual_bases_are_unpaired():
    groups, ids, families = packet()
    groups['explicit_guess'] = groups['explicit_guess'][1:]
    extra = deepcopy(groups['image_present'][0])
    extra.update(base_id='unpaired', event_id='unpaired__image_present')
    groups['image_present'].append(extra)
    result = summarize_pairs(groups, ids, families)
    assert result['paired_universe']['bases'] == 4
    assert result['condition_outcomes']['explicit_guess']['missing'] == 1
    assert result['partitions']['both_absent_conditions_wrong']['bases'] == 0


@pytest.mark.parametrize('defect', ['duplicate_base', 'wrong_condition', 'new_absent_base',
    'duplicate_universe', 'missing_family', 'integer_correctness', 'missing_condition'])
def test_unverified_pair_structure_is_rejected(defect):
    groups, ids, families = packet()
    if defect == 'duplicate_base':
        groups['image_present'].append(deepcopy(groups['image_present'][0]))
    elif defect == 'wrong_condition':
        groups['image_present'][0]['condition'] = 'explicit_guess'
    elif defect == 'new_absent_base':
        groups['explicit_guess'][0]['base_id'] = 'extra'
    elif defect == 'duplicate_universe':
        ids.append(ids[0])
    elif defect == 'missing_family':
        families.pop('a')
    elif defect == 'integer_correctness':
        groups['image_present'][0]['final_correctness'] = 1
    else:
        groups.pop('explicit_guess')
    with pytest.raises(ValueError):
        summarize_pairs(groups, ids, families)
