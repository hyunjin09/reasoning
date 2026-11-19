import pytest
from transformers import AutoTokenizer

from scripts.stage7a.common import ROOT, read_json
from scripts.stage7a_bench.causal_readouts_v2 import compile_readout


@pytest.fixture(scope='module')
def tokenizer():
    checkpoint = read_json(ROOT / 'outputs/stage7a_bench_v2/config/runtime.json')['model_checkpoint']
    return AutoTokenizer.from_pretrained(checkpoint, local_files_only=True)


def example(tokenizer, value, **changes):
    raw = 'First I identify the requested series and then inspect its displayed label. The value is ' + value + '.'
    ids = tokenizer.encode(raw, add_special_tokens=False)
    tokens, previous = [], ''
    for i, token in enumerate(ids):
        decoded = tokenizer.decode(ids[:i+1], skip_special_tokens=False, clean_up_tokenization_spaces=False)
        # The runtime uses a rolling decode with delayed incomplete UTF8 pieces.
        stable = decoded.rstrip('\ufffd')
        assert stable.startswith(previous)
        tokens.append(dict(token_id=token, decoded_token=stable[len(previous):]))
        previous = stable
    assert previous == raw
    start = raw.index(value, raw.index('The value is'))
    claim = dict(readout=value, readout_char_start=start, readout_char_end=start+len(value),
        demand='singleton', question_provided=False, conditional=False, arithmetic_result=False,
        locally_correct=False, ground_truth='independently reviewed source truth', source_id='T')
    claim.update(changes)
    return tokens, claim


def test_wrong_native_is_preserved_separately_from_truth_and_source_semantics(tokenizer):
    tokens, claim = example(tokenizer, '12')
    event = compile_readout(tokens, claim, dict(correct='10', foil='14', target_semantic='14',
        alternative_original='12', alternative_semantic='16'), tokenizer)
    assert event['native_claim_semantic_value'] == '12'
    assert event['correct_semantic_value'] == '10'
    assert event['candidate_ids']['native'] == event['candidate_ids']['alternative_original']
    assert event['candidate_ids']['foil'] == event['candidate_ids']['target_semantic']
    assert event['orientation_audit']['wrong_token_offset'] is not None
    n = event['ed_generated_index']
    assert event['history_before_ed_token_ids'] == [t['token_id'] for t in tokens[:n]]
    assert event['causal_state'] is None


def test_faithful_formatted_native_surface_is_not_normalized_or_retokenized(tokenizer):
    tokens, claim = example(tokenizer, '1,000', locally_correct=True)
    event = compile_readout(tokens, claim, dict(correct='1,000', foil='2,000'), tokenizer)
    assert event['candidate_ids']['correct'] == event['candidate_ids']['native']
    assert event['orientation_audit']['wrong_token_offset'] is None
    with pytest.raises(ValueError, match='literal'):
        compile_readout(tokens, claim, dict(correct='1000', foil='2000'), tokenizer)


def test_nonascii_candidate_identity_does_not_collapse_to_empty_normalized_text(tokenizer):
    tokens, claim = example(tokenizer, 'β')
    event = compile_readout(tokens, claim, dict(correct='α', foil='γ'), tokenizer)
    assert len({tuple(v) for v in event['candidate_ids'].values()}) == 3
    assert event['native_claim_semantic_value'] == 'β'
    assert event['prefix_ends_at_token_boundary'] is True


@pytest.mark.parametrize('change', [dict(question_provided=True), dict(conditional=True),
    dict(arithmetic_result=True), dict(demand='multi'), dict(locally_correct=None)])
def test_unadjudicated_or_nonlocal_claim_cannot_enter_primary_readout(tokenizer, change):
    tokens, claim = example(tokenizer, '12', **change)
    with pytest.raises(ValueError): compile_readout(tokens, claim, dict(correct='10', foil='14'), tokenizer)


def test_native_override_and_unsupported_candidate_or_early_readout_are_rejected(tokenizer):
    tokens, claim = example(tokenizer, '12')
    for candidates in (dict(correct='10', foil='14', native='10'), dict(correct='10', foil='10')):
        with pytest.raises(ValueError): compile_readout(tokens, claim, candidates, tokenizer)
    first = [dict(token_id=i, decoded_token=tokenizer.decode([i])) for i in tokenizer.encode('12', add_special_tokens=False)]
    claim.update(readout_char_start=0, readout_char_end=2)
    with pytest.raises(ValueError, match='eight'): compile_readout(first, claim, dict(correct='10', foil='14'), tokenizer)
