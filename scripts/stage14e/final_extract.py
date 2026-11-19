"""Gold-blind response extraction, only after the acquisition review is sealed."""
from scripts.stage14e.common import P, load, rows, save, sha, now
from scripts.stage14b.protocol import extract
from pathlib import Path


def main():
    review = P / 'annotations/evaluation_source_review_v1.json'
    assert review.exists(), 'Seal acquisition annotations before opening solver finals'
    assert len(load(review)['records']) == 96
    registry = load(P / 'manifests/final_execution_registry_v1.json')
    logical = []
    for root in registry['solver_roots']:
        root = Path(root)
        assert load(root / 'result.json')['status'] == 'COMPLETED'
        logical.extend(load(root / 'solver_execution_manifest.json')['rows'])
    assert len(logical) == 96
    assert len({(r['family_id'], r['arm']) for r in logical}) == 96
    selected = {r['item_id']: r for r in load(P / 'manifests/evaluation_family_selection_v1.json')['rows']}
    assert {r['item_id'] for r in logical} == set(selected)
    options = {r['item_id']: r['options'] for r in rows('outputs/stage14b/manifests/mathvision_3040_eval_manifest.jsonl')
               if r['item_id'] in selected}
    physical = {}
    for r in logical:
        path = r['generation_path']
        if path in physical:
            continue
        g = load(path)
        assert sha(path) == load(Path(path).with_name('result.json'))['generation_sha256']
        parsed = extract(g['raw_decoded_response'], options[r['item_id']], 'T', g['finish_reason'])
        physical[path] = dict(item_id=r['item_id'], generation_path=path, generation_sha256=sha(path),
            parser=parsed, finish_reason=g['finish_reason'], cap_hit=g['cap_hit'], tokens=g['tokens'],
            final_body=g['raw_decoded_response'].rsplit('</think>', 1)[-1]
                if '</think>' in g['raw_decoded_response'] else None,
            tail_if_no_final=g['raw_decoded_response'][-2500:] if '</think>' not in g['raw_decoded_response'] else None,
            options=options[r['item_id']])
    save(P / 'analysis/response_extraction_v1.json', dict(at=now(), records=list(physical.values()),
        logical_rows=logical, acquisition_review_sha256=sha(review), gold_used=False,
        scorer_sha256=sha('scripts/stage14b/protocol.py')))
    packet = P / 'analysis/response_only_review_v1.txt'
    with packet.open('x') as f:
        for path, r in physical.items():
            f.write('\n\n' + path + '\nPARSER ' + str(r['parser']) + '\nOPTIONS ' + str(r['options']) +
                    '\nFINAL\n' + (r['final_body'] if r['final_body'] is not None else
                                    'NO THINK CLOSE. TAIL:\n' + r['tail_if_no_final']))
    print('Physical response packets', len(physical))


if __name__ == '__main__':
    main()
