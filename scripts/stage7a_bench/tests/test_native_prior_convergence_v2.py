from copy import deepcopy

import pytest

from scripts.stage7a_bench.native_prior_convergence_v2 import review_condition, compile_convergence


def fixture():
    entry = dict(id='base__e00', physical_demanded_source='cell-T',
                 reviewed_claim=dict(readout='75.68'))
    raw = 'The requested cell reads 75.68.'
    tokens = [dict(token_index=i, generation_position=4+i, token_id=i+10, decoded_token=s)
              for i, s in enumerate(['The requested cell reads ', '75', '.', '68', '.'])]
    generation = dict(raw_decoded_response=raw, generated_token_ids=[t['token_id'] for t in tokens],
                      generated_token_count=len(tokens))
    meta = dict(prompt_token_count=4, prompt_token_ids=[1, 2, 3, 4])
    result = dict(complete=True, truncated=False, token_count=len(tokens),
                  generation_sha256='g', tokens_sha256='t')
    review = dict(status='MANUALLY_REVIEWED_FULL_NATIVE_CONTROL', entry_id=entry['id'],
        full_native_text_reviewed=True, causal_or_passive_scores_used=False,
        behavior='explicit_evidence', notes='Read all reasoning and final text.',
        generation_sha256='g', tokens_sha256='t', input_sha256='i', result_sha256='r',
        claims=[dict(source_id='cell-T', kind='primary', demand='singleton', quote=raw,
            readout='75.68', question_provided=False, conditional=False, arithmetic_result=False,
            actual_visual_evidence_assertion=True, same_requested_evidence=True)])
    return entry, generation, tokens, meta, result, review, dict(generation='g', tokens='t', input='i', result='r')


def test_full_exact_same_source_review_can_support_convergence():
    args = fixture(); row = review_condition(*args)
    assert row['valid'] and row['readouts'] == ['75.68']
    evidence = compile_convergence(args[0], {c:row for c in ('mask', 'unrelated', 'no_image')})
    assert evidence['converges'] and evidence['available']


@pytest.mark.parametrize('change', ['missing', 'different_value', 'different_source', 'multiple',
    'conditional', 'question_provided', 'arithmetic_result', 'not_asserted', 'wrong_demand',
    'incomplete', 'not_primary'])
def test_nonconvergent_semantics_remain_negative_evidence(change):
    args = list(fixture()); review = args[5]; claim = review['claims'][0]
    if change == 'missing': review['claims'] = []; review['behavior'] = 'abstention'
    if change == 'different_value': args[0]['reviewed_claim']['readout'] = '75.63'
    if change == 'different_source': claim['source_id'] = 'other'
    if change == 'multiple': review['claims'].append(deepcopy(claim))
    if change in ('conditional', 'question_provided', 'arithmetic_result'): claim[change] = True
    if change == 'not_asserted': claim['actual_visual_evidence_assertion'] = False
    if change == 'wrong_demand': claim['same_requested_evidence'] = False
    if change == 'incomplete': args[4].update(complete=False, truncated=True)
    if change == 'not_primary': claim['kind'] = 'incidental'
    row = review_condition(*args)
    assert row['valid'] is False
    assert not compile_convergence(args[0], {c:row for c in ('mask', 'unrelated', 'no_image')})['converges']


@pytest.mark.parametrize('change', ['raw', 'ids', 'position', 'count', 'hash', 'entry',
    'not_full', 'scores', 'span', 'no_notes'])
def test_corrupt_or_unreviewed_evidence_rejected(change):
    args = list(fixture())
    if change == 'raw': args[1]['raw_decoded_response'] += ' extra'
    if change == 'ids': args[2][0]['token_id'] = 99
    if change == 'position': args[2][0]['generation_position'] = 100
    if change == 'count': args[1]['generated_token_count'] = 99
    if change == 'hash': args[5]['generation_sha256'] = 'other'
    if change == 'entry': args[5]['entry_id'] = 'other'
    if change == 'not_full': args[5]['full_native_text_reviewed'] = False
    if change == 'scores': args[5]['causal_or_passive_scores_used'] = True
    if change == 'span': args[5]['claims'][0]['quote'] = 'not in response'
    if change == 'no_notes': args[5]['notes'] = ''
    with pytest.raises(ValueError): review_condition(*args)


def test_partial_bank_cannot_supply_all_three_condition_gate():
    args = fixture(); row = review_condition(*args)
    evidence = compile_convergence(args[0], dict(no_image=row))
    assert evidence['available'] is False and evidence['converges'] is False
    assert evidence['conditions']['mask']['valid'] is False


def test_greek_surface_forms_cannot_converge_via_empty_legacy_normalization():
    args = list(fixture()); args[0]['reviewed_claim']['readout'] = 'α'
    args[5]['claims'][0]['readout'] = '.'
    args[5]['claims'][0]['readout_occurrence'] = 1
    assert review_condition(*args)['valid'] is False


def test_unicode_prefix_does_not_collapse_into_same_numeric_text_key():
    args = list(fixture()); args[0]['reviewed_claim']['readout'] = 'α1'
    chunks = ['The requested cell reads ', 'β', '1', '.']
    args[2] = [dict(token_index=i, generation_position=4+i, token_id=i+10, decoded_token=s)
               for i, s in enumerate(chunks)]
    args[1].update(raw_decoded_response=''.join(chunks), generated_token_ids=[10, 11, 12, 13],
                   generated_token_count=4)
    args[4]['token_count'] = 4
    args[5]['claims'][0].update(quote=''.join(chunks), readout='β1')
    assert review_condition(*args)['valid'] is False
