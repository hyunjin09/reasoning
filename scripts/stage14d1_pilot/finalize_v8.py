"""Apply sealed response-only transcription, preserving the original scoring pass."""
import csv
import numpy as np
from scripts.stage14d1_pilot.common import P, load, rows, save, sha, now
from scripts.stage14d1.contracts import ARMS
from scripts.stage14b.protocol import grade
from scripts.stage14d1_pilot.statistics import bootstrap_indices, paired_summary, interval


def summarize(records):
    families = sorted({r['family_id'] for r in records})
    by = {(r['family_id'], r['arm']): r for r in records}
    assert len(by) == len(records) == len(families)*6
    ix = bootstrap_indices([by[f, 'N']['source_stratum'] for f in families])
    matrix = np.array([[np.nan if by[f, a]['correct'] is None else float(by[f, a]['correct'])
                        for a in ARMS] for f in families])
    arms = {}
    for j, arm in enumerate(ARMS):
        x = matrix[:, j]; valid = np.isfinite(x); sample = x[ix]
        counts = np.isfinite(sample).sum(axis=1)
        means = np.divide(np.nansum(sample, axis=1), counts,
                          out=np.full(len(ix), np.nan), where=counts > 0)
        correct = int((x == 1).sum()); unknown = int((~valid).sum())
        arms[arm] = dict(correct=correct, wrong=int((x == 0).sum()),
            unscorable=unknown, missing=0, assigned=len(families),
            scorable_accuracy=float(np.nanmean(x)) if valid.any() else None,
            scorable_bootstrap_95ci=interval(means), known_correct_fraction=correct/len(families),
            accuracy_missingness_bounds=[correct/len(families), (correct+unknown)/len(families)],
            cap_hits=sum(by[f, arm]['cap_hit'] for f in families))
    contrasts = [('N', a) for a in ARMS[1:]] + [('G', 'QI'), ('Q', 'QI'), ('QI', 'QGL'), ('QIA', 'QGL')]
    pairs = {}
    for base, treatment in contrasts:
        b = matrix[:, ARMS.index(base)]; t = matrix[:, ARMS.index(treatment)]
        result = paired_summary(b, t, ix)
        result['rescue_items'] = [by[f, base]['item_id'] for i, f in enumerate(families) if b[i] == 0 and t[i] == 1]
        result['regression_items'] = [by[f, base]['item_id'] for i, f in enumerate(families) if b[i] == 1 and t[i] == 0]
        assert result['rescue'] == len(result['rescue_items'])
        assert result['regression'] == len(result['regression_items'])
        assert result['rescue']-result['regression'] == result['treatment_correct_paired']-result['baseline_correct_paired']
        pairs[treatment+'-'+base] = result
    return dict(families=len(families), arms=arms, pairs=pairs)


def main():
    initial = load(P/'analysis/scored_logical_rows_v8.json')['rows']
    review_path = P/'annotations/response_review_v8.json'
    review = load(review_path)
    assert review['gold_hidden_to_reviewer'] and review['aggregate_correctness_not_opened']
    edits = {r['generation_path']: r for r in review['records']}
    assert set(edits) == {r['generation_path'] for r in initial if r['correct'] is None}
    original = {r['item_id']: r for r in rows(
        'outputs/stage14b/manifests/mathvision_3040_eval_manifest.jsonl')}
    final = []
    for r in initial:
        s = dict(r, original_parser_answer=r['answer'], original_correct=r['correct'], response_reviewed=False)
        if r['generation_path'] in edits:
            e = edits[r['generation_path']]
            assert sha(e['generation_path']) == e['generation_sha256']
            assert sha(e['packet']) == e['packet_sha256']
            assert r['correct'] is None
            s.update(answer=e['reviewed_answer'], response_reviewed=True,
                response_review=str(review_path), extraction_status=e['status'], extraction_method='sealed_response_only_review')
            if e['reviewed_answer'] is not None:
                g = grade(e['reviewed_answer'], original[r['item_id']])
                assert g['correct'] is not None, (e['id'], g)
                s.update(correct=g['correct'], final_status=g['status'])
            else:
                s.update(correct=None, final_status='UNSCORABLE_NO_THINK_CLOSE')
        final.append(s)
    assert len(final) == 432 and len({r['generation_path'] for r in final}) == 345
    out = summarize(final)
    out.update(at=now(), primary_contrast='QI-N',
        secondary_contrasts=['QI-G', 'QI-Q', 'QGL-QI', 'QGL-QIA'],
        bootstrap=dict(draws=4000, seed=20261019, unit='independent conservative family',
                       strata='answerformat x structured', equal_family_weight=True),
        physical_solver_calls=345, logical_slots=432,
        response_review_sha256=sha(review_path),
        execution_blocks={v: summarize([r for r in final if r['execution_block'] == v])
                          for v in sorted({r['execution_block'] for r in final})},
        context_subgroups={v: summarize([r for r in final if r['context_stratum'] == v])
                           for v in sorted({r['context_stratum'] for r in final})})
    save(P/'analysis/scored_logical_rows_final_v8.json', dict(at=now(), rows=final,
        original_scoring_sha256=sha(P/'analysis/scored_logical_rows_v8.json'),
        review_sha256=sha(review_path), scorer_sha256=sha('scripts/stage14b/protocol.py')))
    with (P/'analysis/scored_logical_rows_final_v8_clean.csv').open('x', newline='') as f:
        writer=csv.DictWriter(f, fieldnames=list(dict.fromkeys(k for r in final for k in r)))
        writer.writeheader();writer.writerows(final)
    save(P/'analysis/accuracy_and_pairs_final_v8.json', out)
    print('Final scores saved; remaining unscorable:', sum(r['correct'] is None for r in final))


if __name__ == '__main__':
    main()
