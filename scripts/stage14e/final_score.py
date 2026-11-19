"""Apply sealed response-only review, then inherited answer equivalence."""
from scripts.stage14e.common import P, load, rows, save, sha, now
from scripts.stage14e.analysis_metrics import accuracy
from scripts.stage14b.protocol import grade


def main():
    extracts = load(P / 'analysis/response_extraction_v1.json')
    review_path = P / 'annotations/response_review_v1.json'
    review = load(review_path)
    assert review['gold_hidden'] and review['aggregate_correctness_not_opened']
    by = {r['generation_path']: r for r in extracts['records']}
    judged = {r['generation_path']: r for r in review['records']}
    assert len(judged) == len(review['records']) and set(by) == set(judged)
    source = {r['item_id']: r for r in rows('outputs/stage14b/manifests/mathvision_3040_eval_manifest.jsonl')}
    selection = load(P / 'manifests/evaluation_family_selection_v1.json')['rows']
    meta = {r['item_id']: r for r in selection}
    result = []
    for logical in extracts['logical_rows']:
        path = logical['generation_path']
        original, manual = by[path], judged[path]
        assert sha(path) == original['generation_sha256'] == manual['generation_sha256']
        answer = manual['reviewed_answer']
        if original['final_body'] is None:
            assert answer is None, 'Never reinterpret uncommitted reasoning as a final'
        score = grade(answer, source[logical['item_id']])
        result.append(dict(logical, parser_answer=original['parser']['answer'], parser_status=original['parser']['status'],
            reviewed_answer=answer, response_review_note=manual['note'], correct=score['correct'], final_status=score['status'],
            grader=score['grader'], missing=False, cap_hit=original['cap_hit'], tokens=original['tokens'],
            stratum=meta[logical['item_id']]['stratum'], generation_sha256=sha(path),
            gold_answer=source[logical['item_id']]['gold_answer']))
    save(P / 'analysis/final_scored_rows_v1.json', dict(at=now(), records=result,
        response_review_sha256=sha(review_path), scorer_sha256=sha('scripts/stage14b/protocol.py')))
    summary = accuracy(result, [r['family_id'] for r in selection])
    save(P / 'analysis/final_accuracy_v1.json', dict(at=now(), **summary))
    print(summary)


if __name__ == '__main__':
    main()
