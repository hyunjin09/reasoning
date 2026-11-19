"""Compile reviewed literal values on the unchanged native-token assay path.

This primary singleton-V adapter does not infer source truth, normalize text,
select events, certify edits, or assign causal states. Binding diagnostics need
their separately reviewed value-preserving contrasts.
"""
from visual_reasoning.stage6b.protocol import candidate_event


def compile_readout(tokens, claim, candidates, tokenizer):
    if (claim.get('demand') != 'singleton' or claim.get('readout_type', 'V') != 'V' or
        type(claim.get('locally_correct')) is not bool or claim.get('ground_truth') is None or
        not claim.get('source_id') or any(claim.get(k) is not False
            for k in ('question_provided', 'conditional', 'arithmetic_result'))):
        raise ValueError('Primary readout requires an independently adjudicated actual singleton visual claim')
    allowed = {'correct', 'foil', 'target_semantic', 'alternative_original', 'alternative_semantic'}
    if (not {'correct', 'foil'} <= set(candidates) or set(candidates) - allowed or
        any(not isinstance(v, str) or not v for v in candidates.values())):
        raise ValueError('Explicit literal candidates required; native tokens cannot be overridden')
    raw = ''.join(t['decoded_token'] for t in tokens)
    start, end = claim['readout_char_start'], claim['readout_char_end']
    if not 0 <= start < end <= len(raw) or raw[start:end] != claim['readout']:
        raise ValueError('Readout span differs from native token text')
    # Literal surface forms are reviewed explicitly. In particular, strip-to-
    # ASCII normalization would collapse distinct Greek labels such as α/β.
    if claim['locally_correct'] != (candidates['correct'] == claim['readout']):
        raise ValueError('Reviewed correctness must match the literal correct candidate surface')
    event = candidate_event(tokens, start, end, candidates['correct'], candidates['foil'], tokenizer)
    left = len(event['history_before_ed_text'])
    right = left + len(event['native_claim_suffix_text'])
    named = dict(correct=event['original_divergent_suffix_ids'],
                 foil=event['counterfactual_divergent_suffix_ids'], native=event['native_claim_suffix_ids'])
    for name, value in candidates.items():
        if name in named:
            continue
        text = raw[left:start] + value + raw[end:right]
        # Retain original generated token IDs whenever the candidate is native.
        ids = (event['native_claim_suffix_ids'] if text == event['native_claim_suffix_text']
               else tokenizer.encode(text, add_special_tokens=False))
        if not ids or tokenizer.decode(ids, skip_special_tokens=False, clean_up_tokenization_spaces=False) != text:
            raise ValueError('Named source-semantic candidate does not round-trip')
        named[name] = ids
    actual, correct = named['native'], named['correct']
    differing = next((i for i, (a, b) in enumerate(zip(actual, correct)) if a != b),
                     min(len(actual), len(correct)) if len(actual) != len(correct) else None)
    event.update(candidate_ids=named, semantic_alternatives=dict(candidates),
        readout_char_start=start, readout_char_end=end, readout_type='V',
        orientation_audit=dict(wrong_token_offset=differing,
            wrong_token_available=differing is not None and differing < len(actual),
            corresponding_correct_token_available=differing is not None and differing < len(correct),
            exact_native_token_history=True, source_truth_inferred=False,
            note='Error-oriented measurement uses the first differing native/correct token; unavailable corresponding tokens remain unavailable.'),
        causal_state=None, selection_used_causal_or_passive_scores=False)
    return event
