from copy import deepcopy

import pytest

from scripts.stage7a_bench.causal_provenance_v2 import (
    object_sha, verify_native_evidence, verified_families, verify_numeric_values)


def evidence():
    raw = 'After inspecting the actual plot, the requested value is 12.'
    quote = 'the requested value is 12.'
    start = raw.index('12')
    claim = dict(quote=quote, readout='12', source_id='requested_series',
        ground_truth='10', locally_correct=False, demand='singleton',
        question_provided=False, conditional=False, arithmetic_result=False,
        char_start=raw.index(quote), char_end=len(raw), readout_char_start=start,
        readout_char_end=start+2)
    row = dict(event_id='chart__image_present', base_id='chart', benchmark='charxiv',
        condition='image_present', prompt='Read the requested series.', no_image=False,
        image_assets=[dict(slot='image_1', decoded_sha256='pixels', size=[20, 20])])
    meta = dict(event_id=row['event_id'], condition=row['condition'], prompt=row['prompt'],
        no_image=False, prompt_token_ids=[5, 6, 7], prompt_token_count=3,
        visual_token_indices=[1], image_assets=deepcopy(row['image_assets']))
    tokens = [dict(token_index=i, token_id=ord(c), decoded_token=c,
                   generation_position=3+i) for i, c in enumerate(raw)]
    generation = dict(raw_decoded_response=raw, generated_token_ids=[ord(c) for c in raw],
                      generated_token_count=len(raw))
    hashes = {k: k+'_hash' for k in ('manifest', 'input', 'generation', 'tokens')}
    result = dict(event_id=row['event_id'], base_id=row['base_id'], benchmark=row['benchmark'],
        condition=row['condition'], generation_sha256=hashes['generation'],
        tokens_sha256=hashes['tokens'], token_count=len(raw), truncated=False)
    review = dict(event_id=row['event_id'], base_id=row['base_id'], benchmark=row['benchmark'],
        condition=row['condition'], manifest_sha256=hashes['manifest'],
        generation_sha256=hashes['generation'], tokens_sha256=hashes['tokens'], truncation=False,
        causal_or_passive_scores_used=False, causal_state=None, eligible_causal_event=None,
        screen_label='F1', final_correctness=True, local_visual_claim_present=True,
        local_visual_claim_correctness=False, binding_claim_present=False,
        binding_claim_correctness=None, unsupported_evidence_claim=False,
        correct_local_read_followed_by_later_error=False, abstention_or_caveat=False,
        guessed_answer=False, final_correctness_reason='Final answer is independently correct.',
        review_note='Full response read.', source_review_note='The requested series says10.',
        task_quality='Usable.', output_confidence='Asserted.', claims=[claim])
    annotation = dict(event_id=row['event_id'], native_input_sha256=hashes['input'],
        generation_sha256=hashes['generation'], tokens_sha256=hashes['tokens'],
        semantic_review_sha256=object_sha(review), causal_or_passive_scores_used=False)
    return row, meta, generation, tokens, result, review, annotation, hashes


def test_exact_native_evidence_retains_wrong_local_read_with_correct_final():
    args = evidence()
    verify_native_evidence(*args)
    assert args[5]['final_correctness'] is True
    assert args[5]['claims'][0]['locally_correct'] is False


@pytest.mark.parametrize('problem', ['response', 'token_ids', 'token_index', 'position',
    'prompt', 'source_pixels', 'row_identity', 'review_hash', 'input_hash', 'scores',
    'claim_span', 'truncation', 'missing_annotation_identity', 'result_hash'])
def test_corrupted_or_unbound_evidence_is_rejected(problem):
    args = list(evidence())
    if problem == 'response': args[2]['raw_decoded_response'] += 'unrecorded'
    if problem == 'token_ids': args[2]['generated_token_ids'][0] += 1
    if problem == 'token_index': args[3][0]['token_index'] = 1
    if problem == 'position': args[3][0]['generation_position'] = 100
    if problem == 'prompt': args[1]['prompt'] = 'Read another series.'
    if problem == 'source_pixels': args[1]['image_assets'][0]['decoded_sha256'] = 'changed'
    if problem == 'row_identity': args[4]['base_id'] = 'other_chart'
    if problem == 'review_hash': args[5]['review_note'] = 'Changed after source annotation.'
    if problem == 'input_hash': args[6]['native_input_sha256'] = 'other_input'
    if problem == 'scores': args[6]['causal_or_passive_scores_used'] = True
    if problem == 'claim_span':
        args[5]['claims'][0]['readout_char_start'] -= 1
        args[6]['semantic_review_sha256'] = object_sha(args[5])
    if problem == 'truncation': args[4]['truncated'] = True
    if problem == 'missing_annotation_identity': del args[6]['event_id']
    if problem == 'result_hash': args[4]['generation_sha256'] = 'changed_generation'
    with pytest.raises(ValueError): verify_native_evidence(*args)


def test_truncated_but_reviewed_native_prefix_is_not_silently_discarded():
    args = list(evidence())
    args[4]['truncated'] = args[5]['truncation'] = True
    args[6]['semantic_review_sha256'] = object_sha(args[5])
    verify_native_evidence(*args)


def test_unavailable_input_is_never_a_causal_native_claim():
    args = list(evidence())
    args[4]['unavailable'] = True
    with pytest.raises(ValueError, match='unavailable'): verify_native_evidence(*args)


def test_review_hash_does_not_depend_on_dictionary_key_order():
    a = {'z': [1, 2], 'a': {'β': '10'}}
    assert object_sha(a) == object_sha({'a': {'β': '10'}, 'z': [1, 2]})


def test_document_pages_cannot_be_silently_replaced_or_reordered():
    args = list(evidence())
    fields = dict(document_path='frozen.pdf', document_sha256='pdf_hash',
                  renderer_version='fixed', render_scale=1.6)
    args[0].update(fields, page_count=2)
    args[1].update(fields, visual_images=[dict(physical_page=1), dict(physical_page=2)])
    args[0]['image_assets'] = []
    del args[1]['image_assets']
    verify_native_evidence(*args)
    args[1]['visual_images'].reverse()
    with pytest.raises(ValueError, match='document'): verify_native_evidence(*args)
    args[1]['visual_images'].reverse()
    args[1]['document_sha256'] = 'replacement_pdf'
    with pytest.raises(ValueError, match='document'): verify_native_evidence(*args)


def test_family_certificate_requires_this_manifest_and_no_identity_conflict():
    certificate = dict(status='PASS', manifest_sha256={'cohort.jsonl': 'hash'},
        causal_scores_read=False, native_outputs_read=False,
        benchmarks={'chart': dict(cross_family_identity_conflicts=[],
            paired_conditions_stay_together=True, per_base_source_family={'x': 'merged_pdf_family'})})
    assert verified_families(certificate, 'cohort.jsonl', 'hash', 'chart') == {'x': 'merged_pdf_family'}
    with pytest.raises(ValueError): verified_families(certificate, 'another.jsonl', 'hash', 'chart')
    certificate['benchmarks']['chart']['cross_family_identity_conflicts'] = ['same_image_in_two_families']
    with pytest.raises(ValueError): verified_families(certificate, 'cohort.jsonl', 'hash', 'chart')


def test_value_candidates_cannot_drift_toward_the_emitted_error():
    annotation = dict(target_ground_truth='1.9', source_domain_review=dict(lower='0', upper='100'),
        alternative=dict(source_id='other'), candidates=dict(correct='1.9', foil='1.4',
            target_semantic='1.4', alternative_original='1.5', alternative_semantic='1.0'))
    verify_numeric_values(annotation)
    annotation['candidates']['foil'] = '1.5'
    with pytest.raises(ValueError, match='source-only'): verify_numeric_values(annotation)
