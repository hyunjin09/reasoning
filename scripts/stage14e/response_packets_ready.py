"""Gold-blind response review of immutable completed receipts while queues finish."""
import argparse
from pathlib import Path
from scripts.stage14e.common import P, load, rows, save, sha, now
from scripts.stage14b.protocol import extract


def main(batch):
    source = P / 'annotations/evaluation_source_review_v1.json'
    assert len(load(source)['records']) == 96
    reviewed = set()
    for p in (P / 'annotations').glob('response_review_*_v1.json'):
        r = load(p)
        assert r['gold_hidden'] and r['aggregate_correctness_not_opened']
        reviewed.update(v['generation_path'] for v in r['records'])
    options = {r['item_id']: r['options'] for r in rows('outputs/stage14b/manifests/mathvision_3040_eval_manifest.jsonl')}
    ready = {}
    for root in load(P / 'manifests/final_execution_registry_v1.json')['solver_roots']:
        for r in load(Path(root) / 'solver_execution_manifest.json')['rows']:
            path = Path(r['generation_path'])
            if str(path) in reviewed or str(path) in ready or not path.with_name('result.json').exists():
                continue
            g = load(path)
            assert sha(path) == load(path.with_name('result.json'))['generation_sha256']
            ready[str(path)] = dict(item_id=r['item_id'], generation_path=str(path), generation_sha256=sha(path),
                parser=extract(g['raw_decoded_response'], options[r['item_id']], 'T', g['finish_reason']),
                final_body=g['raw_decoded_response'].rsplit('</think>', 1)[-1] if '</think>' in g['raw_decoded_response'] else None,
                cap_hit=g['cap_hit'], finish_reason=g['finish_reason'], tokens=g['tokens'], options=options[r['item_id']])
    assert ready, 'No new completed physical receipts'
    save(P / f'analysis/response_packet_ready{batch:02d}_v1.json', dict(at=now(), records=list(ready.values()),
        acquisition_review_sha256=sha(source), gold_used=False, incomplete_queue_allowed_but_only_completed_receipts=True))
    for path, r in ready.items():
        print('\nID', Path(path).parent.name, 'PARSER', r['parser'], 'OPTIONS', r['options'],
            'CAP', r['cap_hit'], '\nFINAL TAIL\n', r['final_body'][-1400:] if r['final_body'] is not None else 'NO COMMITTED FINAL')
    print('Ready physical records', len(ready))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('batch', type=int)
    main(parser.parse_args().batch)
