"""Record explicit full-response judgments; never infer semantics from accuracy.

Claims are actual local visual assertions, not question-provided facts,
hypothetical examples, or downstream arithmetic. Source coordinates and causal
readouts require a separate pilot review before any experiment.
"""
import argparse
from pathlib import Path

from scripts.stage7a.common import ROOT, read_json, read_jsonl, sha, write_jsonl
from scripts.stage7a.annotation_helpers import readout_offset

OUT = ROOT / 'outputs/stage7a_bench_v2'
BOOLEAN = ('final_correctness', 'local_visual_claim_present',
    'local_visual_claim_correctness', 'binding_claim_present',
    'binding_claim_correctness', 'unsupported_evidence_claim',
    'correct_local_read_followed_by_later_error', 'abstention_or_caveat', 'guessed_answer')
UNKNOWN_OK = {'final_correctness', 'local_visual_claim_correctness', 'binding_claim_correctness'}


def validate_judgment(judgment, raw):
    row = dict(judgment)
    if any(k in row for k in ('causal_state', 'eligible_causal_event', 'manifest_sha256', 'generation_sha256')):
        raise ValueError('Semantic judgment cannot set causal labels or generated provenance')
    for key in BOOLEAN:
        if key not in row or not (type(row[key]) is bool or key in UNKNOWN_OK and row[key] is None):
            raise ValueError('Explicit boolean/adjudicated unknown required: ' + key)
    for key in ('final_correctness_reason', 'review_note', 'source_review_note', 'task_quality', 'output_confidence'):
        if not isinstance(row.get(key), str) or not row[key].strip():
            raise ValueError('Explicit review evidence required: ' + key)
    claims = []
    for claim in row.get('claims', []):
        claim = dict(claim)
        quote, readout = claim.get('quote'), claim.get('readout')
        if not quote or not readout or raw.count(quote) != 1 or readout not in quote:
            raise ValueError('Claim quote/readout must have an unambiguous native location')
        if any(claim.get(k) is not False for k in ('question_provided', 'conditional', 'arithmetic_result')):
            raise ValueError('A local visual claim cannot be a question fact, conditional example or arithmetic result')
        if not claim.get('source_id') or claim.get('demand') not in ('singleton', 'multi', 'unclear', 'none'):
            raise ValueError('Explicit source/demand interpretation required')
        if 'locally_correct' not in claim or not (type(claim['locally_correct']) is bool or claim['locally_correct'] is None):
            raise ValueError('Explicit claim correctness or unknown required')
        if claim['locally_correct'] is not None and claim.get('ground_truth') is None:
            raise ValueError('Adjudicated local correctness requires independently reviewed truth')
        left = raw.index(quote)
        start = left + readout_offset(quote, readout, claim.get('readout_occurrence'))
        claim.update(char_start=left, char_end=left+len(quote),
                     readout_char_start=start, readout_char_end=start+len(readout))
        claims.append(claim)
    row['claims'] = claims
    present, correct = row['local_visual_claim_present'], row['local_visual_claim_correctness']
    if present != bool(claims) or not present and correct is not None:
        raise ValueError('Local-claim presence/correctness disagrees with explicit claims')
    if correct is True and any(c['locally_correct'] is not True for c in claims):
        raise ValueError('All local claims must be adjudicated correct for aggregate correct')
    if correct is False and not any(c['locally_correct'] is False for c in claims):
        raise ValueError('Aggregate local error requires an actual adjudicated wrong claim')
    valid = {
        'F0': present and correct is True,
        'F1': present and correct is False,
        'F2': present and row['binding_claim_present'] and row['binding_claim_correctness'] is False,
        'F3': present and row['unsupported_evidence_claim'],
        'F4': present and correct is True and row['correct_local_read_followed_by_later_error'],
        'F5': row['abstention_or_caveat'],
        'F6': not present,
    }
    if 'screen_label' in row and row['screen_label'] is None:
        # Missing adjudication is neither a new failure class nor a model
        # abstention. Preserve it explicitly rather than forcing F0/F1/F3.
        reason = row.get('screen_label_reason')
        if (not present or correct is not None or any(valid.values()) or
            not isinstance(reason, str) or not reason.strip()):
            raise ValueError('Unclassified claim requires unresolved correctness and an explicit reason')
    elif not valid.get(row.get('screen_label'), False):
        raise ValueError('Screening label conflicts with separately reviewed dimensions')
    return row


def record(run, manifest, index, judgment):
    if Path(run).name != run or run in ('.', '..'):
        raise ValueError('Unsafe run identity')
    manifest = (ROOT / manifest).resolve()
    if not manifest.is_relative_to(OUT / 'cohort/benchmark_manifests'):
        raise ValueError('Use a benchmark manifest inside the active cohort')
    rows = read_jsonl(manifest)
    freezes = read_json(OUT / 'cohort/sample_freeze.json')['native_screen'].values()
    matches = [f for f in freezes if f['sha256'] == sha(manifest) and f['count'] == len(rows)]
    if len(matches) != 1:
        raise ValueError('Manifest is not uniquely frozen with its exact count')
    if index < 0 or index >= len(rows):
        raise ValueError('Native index outside frozen manifest')
    row = rows[index]
    if row['benchmark'] == 'phantom_0':
        raise ValueError('Use the separate Phantom no-ground-truth recorder')
    path = OUT / 'native_screen/generations' / run / 'examples' / row['event_id']
    result = read_json(path / 'result.json')
    if result.get('unavailable'):
        raise ValueError('Unavailable input is not a generated response')
    if read_json(path / 'manifest_row.json') != row:
        raise ValueError('Generated row differs from selected frozen manifest')
    generation = read_json(path / 'generation.json')
    tokens = read_jsonl(path / 'tokens.jsonl')
    if (sha(path / 'generation.json') != result['generation_sha256'] or
        sha(path / 'tokens.jsonl') != result['tokens_sha256'] or
        ''.join(t['decoded_token'] for t in tokens) != generation['raw_decoded_response']):
        raise ValueError('Native response/token provenance mismatch')
    review = validate_judgment(judgment, generation['raw_decoded_response'])
    review.update(event_id=row['event_id'], base_id=row['base_id'], example_id=row['example_id'],
        family_id=row['family_id'], benchmark=row['benchmark'], condition=row['condition'], native_index=index,
        truncation=result['truncated'], manifest_sha256=sha(manifest),
        generation_sha256=result['generation_sha256'], tokens_sha256=result['tokens_sha256'],
        reviewer='primary agent manual semantic review',
        review_scope='Full raw generated response including reasoning and final answer',
        causal_state=None, eligible_causal_event=None, causal_or_passive_scores_used=False,
        structural_selection_precedes_model_outputs=True)
    dest = OUT / 'native_screen/manual_reviews' / (run + '__' + row['condition'] + '.jsonl')
    records = read_jsonl(dest) if dest.exists() else []
    previous = [r for r in records if r['event_id'] == row['event_id']]
    if previous and previous != [review]:
        raise ValueError('Existing semantic judgment differs; explicit amendment required')
    if not previous:
        records.append(review)
    write_jsonl(dest, sorted(records, key=lambda r: r['native_index']))
    return review


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', required=True)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--index', type=int, required=True)
    parser.add_argument('--judgment', required=True)
    args = parser.parse_args()
    draft = (ROOT / args.judgment).resolve()
    if not draft.is_relative_to(OUT):
        raise ValueError('Judgment draft must be inside the active stage outputs')
    saved = record(args.run, args.manifest, args.index, read_json(draft))
    print('MANUAL_REVIEWED', saved['event_id'], saved['screen_label'])
