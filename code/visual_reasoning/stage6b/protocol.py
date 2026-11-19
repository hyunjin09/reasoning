"""Source identities, candidate orientation and bounded allocation contracts."""
from visual_reasoning.stage5a.annotation import exact_semantic_candidate


def c2_roles(row):
    cell = row['condition']
    if cell not in ('AR', 'A_only', 'R_only', 'Neither'):
        raise ValueError('Unknown factorial cell')
    demand = cell in ('AR', 'R_only')
    demanded = 'T' if demand else 'X'
    if row['demanded_sources'] != [demanded]:
        raise ValueError('Frozen focal demand mapping is inconsistent')
    alignment = cell in ('AR', 'A_only')
    return {'focal': 'T', 'aligned': 'T' if alignment else None,
            'demanded': demanded, 'alternative': 'X' if demand else 'T',
            'alignment': alignment, 'focal_demand': demand}


def candidate_event(tokens, start, end, correct, foil, tokenizer):
    """Same native prefix, truth-oriented pair, and separate observed claim."""
    raw = ''.join(t['decoded_token'] for t in tokens)
    actual = raw[start:end]
    # Obtain native boundaries using whichever replacement differs from actual.
    replacement = foil if actual != foil else correct
    anchor = exact_semantic_candidate(tokens=tokens, match_start=start,
        match_end=end, counterfactual_value=replacement, tokenizer=tokenizer)
    first = anchor['ed_generated_index']
    if first < 8:
        raise ValueError('Readout has fewer than eight preceding generated queries')
    left = len(anchor['history_before_ed_text'])
    native_text = anchor['original_divergent_suffix_text']
    right = left + len(native_text)

    def candidate(value):
        text = raw[left:start] + value + raw[end:right]
        ids = (anchor['original_divergent_suffix_ids'] if text == native_text
               else tokenizer.encode(text, add_special_tokens=False))
        if not ids or tokenizer.decode(ids, skip_special_tokens=False,
                clean_up_tokenization_spaces=False) != text:
            raise ValueError('Semantic candidate does not round-trip')
        return ids, text

    correct_ids, correct_text = candidate(correct)
    foil_ids, foil_text = candidate(foil)
    if correct_ids == foil_ids:
        raise ValueError('Correct and foil candidates are identical')
    return {**anchor, 'candidate_start_token': first,
        'current_query_zero_based': first-1,
        'native_claim_suffix_ids': anchor['original_divergent_suffix_ids'],
        'native_claim_suffix_text': native_text,
        'original_divergent_suffix_ids': correct_ids,
        'counterfactual_divergent_suffix_ids': foil_ids,
        'original_divergent_suffix_text': correct_text,
        'counterfactual_divergent_suffix_text': foil_text,
        'correct_semantic_value': correct, 'foil_semantic_value': foil,
        'native_claim_semantic_value': actual,
        'candidate_orientation': 'D=mean_logP(correct)-mean_logP(foil)',
        'original_candidate_exact_generated_tokens': correct_ids == anchor['original_divergent_suffix_ids']}


def assigned_rank(env, visible_devices, allocation):
    rank = int(env.get('LOCAL_RANK', '-1'))
    if (env.get('SLURM_JOB_ID') != allocation or env.get('WORLD_SIZE') != '2'
            or visible_devices != 2 or rank not in (0, 1)):
        raise ValueError('Exactly two assigned GPUs in the authorized allocation required')
    return rank
