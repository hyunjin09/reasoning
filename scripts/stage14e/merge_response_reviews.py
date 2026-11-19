"""Seal the complete gold-blind review before any final-answer scoring."""
from scripts.stage14e.common import P, load, save, sha, now


def main():
    extraction = load(P / 'analysis/response_extraction_v1.json')
    expected = {r['generation_path']: r for r in extraction['records']}
    assert len(expected) == 77
    assert not (P / 'analysis/final_scored_rows_v1.json').exists()
    sources, records = {}, []
    for path in sorted((P / 'annotations').glob('response_review_*_v1.json')):
        batch = load(path)
        assert batch['gold_hidden'] and batch['aggregate_correctness_not_opened']
        sources[str(path)] = sha(path)
        records.extend(batch['records'])
    by = {r['generation_path']: r for r in records}
    assert len(by) == len(records) == 77 and set(by) == set(expected)
    for path, row in by.items():
        assert row['generation_sha256'] == expected[path]['generation_sha256'] == sha(path)
        assert expected[path]['final_body'] is not None or row['reviewed_answer'] is None
    save(P / 'annotations/response_review_v1.json', dict(at=now(),
        gold_hidden=True, aggregate_correctness_not_opened=True,
        source_batches=sources, extraction_sha256=sha(P / 'analysis/response_extraction_v1.json'),
        records=records))
    print('Sealed all77 physical response reviews before scoring')


if __name__ == '__main__':
    main()
