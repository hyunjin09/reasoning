"""Aggregate reviewed native behavior, preserving missingness and paired scope.

This program never produces semantic judgments or causal grounding labels.
Without --require-complete it writes a clearly provisional progress snapshot.
"""
import argparse
from collections import Counter
from itertools import combinations
import time

from scripts.stage7a.common import ROOT, read_json, read_jsonl, sha, write_json, write_jsonl

OUT = ROOT / 'outputs/stage7a_bench_v2'


def indexed(rows, key='event_id'):
    result = {r[key]: r for r in rows}
    if len(result) != len(rows):
        raise ValueError('Duplicate ' + key)
    return result


def rate(values):
    if any(v is not None and type(v) is not bool for v in values):
        raise ValueError('Rate requires explicit bool or unknown, not truthiness')
    measured = [v for v in values if v is not None]
    positive = sum(measured)
    return dict(numerator=positive, denominator=len(measured), unknown=len(values)-len(measured),
                value=positive / len(measured) if measured else None)


def summarize_condition(manifest, results, reviews):
    cohort, outcomes, labels = indexed(manifest), indexed(results), indexed(reviews)
    phantom = manifest[0]['benchmark'] == 'phantom_0'
    if phantom and not all(x['benchmark'] == 'phantom_0' and x.get('no_image') is True for x in manifest):
        raise ValueError('Phantom structural exclusion requires an entirely no-image cohort')
    if not set(outcomes) <= set(cohort) or not set(labels) <= set(outcomes):
        raise ValueError('Result/review outside frozen or generated cohort')
    generated = [r for r in results if not r.get('unavailable')]
    unavailable = [r for r in results if r.get('unavailable')]
    if any(r['event_id'] in labels for r in unavailable):
        raise ValueError('Unavailable input cannot have native semantic judgment')
    if any(r['screen_label'] is not None and r['screen_label'] not in {'F'+str(i) for i in range(7)} for r in reviews):
        raise ValueError('Unknown semantic class')
    n, g, u, r = len(manifest), len(generated), len(unavailable), len(reviews)
    def metric(field):
        return rate([x.get(field) for x in reviews])
    def classes(choices):
        return rate([None if x['screen_label'] is None else x['screen_label'] in choices for x in reviews])
    return dict(benchmark=manifest[0]['benchmark'], condition=manifest[0]['condition'],
        frozen=n, generated=g, unavailable=u, pending_generation=n-g-u, reviewed=r,
        pending_review=g-r, screen_complete=n == g+u and g == r,
        unavailable_reasons=dict(Counter(x['unavailable_reason'] for x in unavailable)),
        screen_classes=dict(Counter(x['screen_label'] for x in reviews if x['screen_label'] is not None)),
        screen_class_unadjudicated=sum(x['screen_label'] is None for x in reviews),
        final_accuracy=metric('final_correctness'),
        local_visual_claim_rate=metric('local_visual_claim_present'),
        local_visual_error_rate=rate([None if x.get('local_visual_claim_correctness') is None
            else not x['local_visual_claim_correctness'] for x in reviews]),
        local_error_candidate_per_reviewed_example=classes({'F1', 'F2'}),
        binding_claim_rate=metric('binding_claim_present'),
        binding_error_candidate_rate=classes({'F2'}),
        unsupported_claim_rate=metric('unsupported_evidence_claim'),
        integration_error_candidate_rate=metric('correct_local_read_followed_by_later_error'),
        faithful_control_candidate_rate=classes({'F0'}),
        uncertainty_abstention_screen_rate=classes({'F5'}),
        abstention_or_caveat_rate=metric('abstention_or_caveat'),
        guessed_answer_rate=metric('guessed_answer'),
        expressed_confidence=dict(Counter(x.get('output_confidence', 'unrecorded') for x in reviews)),
        truncation_rate=rate([x.get('truncated') for x in generated]),
        eligible_causal_event_rate=rate([False] * r) if phantom else metric('eligible_causal_event'),
        causal_eligibility_basis=('No actual visual source in Phantom-0; behavioral screening only'
            if phantom else 'Requires separately reviewed source/readout and pilot eligibility; unknown until recorded'),
        native_elapsed_seconds=sum(x.get('elapsed_seconds', 0.) for x in generated),
        annotation_minutes=None,
        annotation_time_reason='No reliable per-example annotation-time measurements available',
        scope='Semantic rates use reviewed/adjudicated denominators; truncation uses all generated rows. '
              'Local error rate is conditional on adjudicated local-claim correctness. '
              'Unadjudicated screening classes remain unknown in class-derived rates. '
              'F0 is a screening candidate, never a causal certificate.')


def paired_comparison(left, right):
    a, b = indexed(left, 'base_id'), indexed(right, 'base_id')
    common = sorted(set(a) & set(b))
    def values(field, source):
        return [source[k].get(field) for k in common]
    def disagreement(field):
        return rate([None if a[k].get(field) is None or b[k].get(field) is None
                     else a[k][field] != b[k][field] for k in common])
    return dict(paired_reviewed=len(common), paired_base_ids=common,
        left_final_accuracy=rate(values('final_correctness', a)),
        right_final_accuracy=rate(values('final_correctness', b)),
        final_correctness_disagreement=disagreement('final_correctness'),
        visual_claim_disagreement=disagreement('local_visual_claim_present'),
        caveat_disagreement=disagreement('abstention_or_caveat'),
        unsupported_claim_disagreement=disagreement('unsupported_evidence_claim'),
        guess_disagreement=disagreement('guessed_answer'),
        left_visual_claim_rate=rate(values('local_visual_claim_present', a)),
        right_visual_claim_rate=rate(values('local_visual_claim_present', b)),
        left_caveat_rate=rate(values('abstention_or_caveat', a)),
        right_caveat_rate=rate(values('abstention_or_caveat', b)),
        left_unsupported_claim_rate=rate(values('unsupported_evidence_claim', a)),
        right_unsupported_claim_rate=rate(values('unsupported_evidence_claim', b)),
        paired_evidence=[dict(base_id=k, left_claims=a[k].get('claims', []),
            right_claims=b[k].get('claims', []),
            left_output_confidence=a[k].get('output_confidence', 'unrecorded'),
            right_output_confidence=b[k].get('output_confidence', 'unrecorded')) for k in common],
        evidence_comparison_scope='Preserved semantic claim identities/quotes; no automatic equivalence or causal assignment. Confidence is expressed text, not a calibrated probability.',
        causal_label=None, scope='Common reviewed base IDs only; behavioral comparison')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--require-complete', action='store_true')
    args = parser.parse_args()
    freeze = read_json(OUT / 'cohort/sample_freeze.json')['native_screen']
    manifests = {}
    for name, record in freeze.items():
        path = ROOT / record['manifest']
        assert sha(path) == record['sha256']
        manifests[name] = read_jsonl(path)
        assert len(manifests[name]) == record['count']
    results = []
    for path in sorted((OUT / 'native_screen/generations').glob('*/examples/*/result.json')):
        result = read_json(path)
        if not result.get('unavailable'):
            assert sha(path.with_name('generation.json')) == result['generation_sha256']
        results.append(result)
    outcomes = indexed(results)
    reviews = []
    for path in sorted((OUT / 'native_screen/manual_reviews').glob('*.jsonl')):
        reviews.extend(read_jsonl(path))
    labels = indexed(reviews)
    all_ids = {r['event_id'] for rows in manifests.values() for r in rows}
    assert set(outcomes) <= all_ids and set(labels) <= set(outcomes)
    for name, rows in manifests.items():
        for row in rows:
            if row['event_id'] in labels:
                label = labels[row['event_id']]
                assert label['manifest_sha256'] == freeze[name]['sha256']
                assert label['generation_sha256'] == outcomes[row['event_id']]['generation_sha256']
                assert all(label[k] == row[k] for k in ('benchmark', 'base_id', 'condition'))
    summaries, review_groups = {}, {}
    for name, rows in manifests.items():
        ids = [r['event_id'] for r in rows]
        review_groups[name] = [labels[k] for k in ids if k in labels]
        summaries[name] = summarize_condition(rows, [outcomes[k] for k in ids if k in outcomes], review_groups[name])
    complete = all(s['screen_complete'] for s in summaries.values())
    if args.require_complete and not complete:
        raise RuntimeError('Native generation/semantic review is incomplete; cannot publish final yield')
    pairs = {}
    for a, b in combinations(summaries, 2):
        if summaries[a]['benchmark'] == summaries[b]['benchmark']:
            pairs[a+'__'+b] = paired_comparison(review_groups[a], review_groups[b])
    payload = dict(status='NATIVE_SEMANTICS_COMPLETE' if complete else 'PROVISIONAL_INCOMPLETE',
        snapshot_unix=time.time(), conditions=summaries, paired_conditions=pairs,
        causal_states_assigned=False, native_screen_freeze=freeze)
    if args.require_complete:
        write_json(OUT / 'native_screen/native_yield.json', payload)
        write_jsonl(OUT / 'native_screen/native_labels.jsonl', reviews)
    else:
        write_json(OUT / 'native_screen/review_progress.json', payload)
    print(payload['status'], 'generated', sum(s['generated'] for s in summaries.values()),
          'reviewed', len(reviews), 'frozen', sum(s['frozen'] for s in summaries.values()))


if __name__ == '__main__':
    main()
