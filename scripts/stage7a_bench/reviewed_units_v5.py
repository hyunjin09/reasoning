"""Verify native units across preserved runs and bounded worker shards.

This module reads no model features or effects. The caller verifies artifact
hashes, the frozen selection and run completion separately. A verified unit is
full semantic coverage, never causal pilot admission.
"""
from scripts.stage7a_bench.image_semantic_reviews_v2 import validate_judgment


def ordered_owners(expected_ids, run_ids):
    owners = {}
    for run, ids in run_ids.items():
        for event_id in ids:
            if event_id in owners:
                raise ValueError('A native event has multiple owners or repeats')
            owners[event_id] = run
    if len(set(expected_ids)) != len(expected_ids) or set(owners) != set(expected_ids):
        raise ValueError('Native union differs from the exact frozen gate IDs')
    return [(key, owners[key]) for key in expected_ids]


def verify_unit(*, row, index, manifest_sha256, result, review, meta, generation,
                tokens, generation_sha256, tokens_sha256):
    if result.get('unavailable'):
        raise ValueError('Unavailable input cannot supply a reviewed native response')
    if any(result.get(k) != row[k] or review.get(k) != row[k]
           for k in ('event_id', 'base_id', 'benchmark', 'condition')):
        raise ValueError('Native result/review identity mismatch')
    if (review.get('native_index') != index or
            review.get('manifest_sha256') != manifest_sha256 or
            review.get('truncation') != result.get('truncated')):
        raise ValueError('Review index, manifest or truncation mismatch')
    if (review.get('causal_state') is not None or
            review.get('eligible_causal_event') is not None or
            review.get('causal_or_passive_scores_used') is not False):
        raise ValueError('Native semantic gate cannot use causal interpretations')
    for name, digest in (('generation', generation_sha256), ('tokens', tokens_sha256)):
        if result.get(name+'_sha256') != digest or review.get(name+'_sha256') != digest:
            raise ValueError('Native artifact/review hash mismatch')
    length = len(meta['prompt_token_ids'])
    if (meta.get('prompt_token_count') != length or
            any(meta.get(k) != row[k] for k in ('event_id', 'condition', 'prompt', 'no_image')) or
            ''.join(t['decoded_token'] for t in tokens) != generation['raw_decoded_response'] or
            [t['token_id'] for t in tokens] != generation['generated_token_ids'] or
            generation.get('generated_token_count') != len(tokens) or
            result.get('token_count') != len(tokens) or
            any(t['token_index'] != i or t['generation_position'] != length+i
                for i, t in enumerate(tokens))):
        raise ValueError('Native input, response or token alignment mismatch')
    judgment = {k: v for k, v in review.items() if k not in
                ('causal_state', 'eligible_causal_event', 'manifest_sha256', 'generation_sha256')}
    if validate_judgment(judgment, generation['raw_decoded_response'])['claims'] != review['claims']:
        raise ValueError('Reviewed claim spans differ from the actual full native response')
