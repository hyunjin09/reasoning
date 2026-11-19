"""A shard union must verify the same native evidence as a serial screen."""
from copy import deepcopy

import pytest

from scripts.stage7a_bench.reviewed_units_v5 import verify_unit, ordered_owners
from scripts.stage7a_bench.image_semantic_reviews_v2 import BOOLEAN, UNKNOWN_OK


def bundle():
    row = dict(event_id='e0', base_id='b0', benchmark='mathvision_wild',
               condition='photo', prompt='Read image', no_image=False)
    result = dict(row, truncated=False, token_count=2,
                  generation_sha256='gen', tokens_sha256='tok')
    review = dict(row, native_index=0, truncation=False, claims=[], screen_label='F6',
                  manifest_sha256='manifest', generation_sha256='gen', tokens_sha256='tok',
                  causal_state=None, eligible_causal_event=None, causal_or_passive_scores_used=False)
    review.update({k: None if k in UNKNOWN_OK else False for k in BOOLEAN})
    review.update({k: 'Explicit full response review' for k in ('final_correctness_reason',
        'review_note', 'source_review_note', 'task_quality', 'output_confidence')})
    meta = dict(row, prompt_token_ids=[8, 9], prompt_token_count=2)
    generation = dict(raw_decoded_response='OK', generated_token_ids=[1, 2], generated_token_count=2)
    tokens = [dict(decoded_token=c, token_id=i+1, token_index=i, generation_position=i+2)
              for i, c in enumerate('OK')]
    return dict(row=row, index=0, manifest_sha256='manifest', result=result, review=review,
                meta=meta, generation=generation, tokens=tokens,
                generation_sha256='gen', tokens_sha256='tok')


def test_verified_native_unit_accepts_complete_response_evidence():
    verify_unit(**bundle())


@pytest.mark.parametrize('mutation', ['claim', 'index', 'causal', 'tokens', 'position',
                                    'response', 'hash', 'prompt', 'condition', 'truncation'])
def test_damaged_native_or_review_evidence_is_rejected(mutation):
    packet = deepcopy(bundle())
    if mutation == 'claim': packet['review']['screen_label'] = 'F0'
    elif mutation == 'index': packet['review']['native_index'] = 1
    elif mutation == 'causal': packet['review']['causal_state'] = 'FAITHFUL_READ'
    elif mutation == 'tokens': packet['tokens'][0]['token_id'] = 99
    elif mutation == 'position': packet['tokens'][0]['generation_position'] = 99
    elif mutation == 'response': packet['generation']['raw_decoded_response'] = 'BAD'
    elif mutation == 'hash': packet['tokens_sha256'] = 'changed'
    elif mutation == 'prompt': packet['meta']['prompt'] = 'different'
    elif mutation == 'condition': packet['result']['condition'] = 'screenshot'
    else: packet['review']['truncation'] = True
    with pytest.raises(ValueError):
        verify_unit(**packet)


def test_union_is_ordered_by_frozen_ids_not_worker_completion():
    assert ordered_owners(['e0', 'e1', 'e2'], {'old': ['e0'], 's1': ['e2'], 's0': ['e1']}) == [
        ('e0', 'old'), ('e1', 's0'), ('e2', 's1')]


@pytest.mark.parametrize('owners', [
    {'old': ['e0'], 's1': ['e2']},
    {'old': ['e0'], 's1': ['e1', 'e1']},
    {'old': ['e0'], 's1': ['e0', 'e1']},
    {'old': ['e0'], 's1': ['e1', 'e96']},
])
def test_duplicate_missing_or_out_of_scope_union_is_rejected(owners):
    with pytest.raises(ValueError):
        ordered_owners(['e0', 'e1'], owners)
