"""Acquire the manifest's missing v2 releases sequentially using tested guards."""
import concurrent.futures
import json
from pathlib import Path

from scripts.stage7a_bench.download_datasets import transfer, now

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'outputs/stage7a_bench_v2'


def main():
    path = OUT / 'cohort/download_manifest.json'
    manifest = json.loads(path.read_text())
    assert not manifest['policy_approval_required'] and manifest['authorization']
    assert (OUT / 'cohort/dataset_inventory.json').is_file()
    for dataset in manifest['entries']:
        if dataset['status'] != 'FROZEN_PENDING':
            raise RuntimeError('A completed or failed entry needs explicit reconciliation, not automatic retry')
        print('START', dataset['candidate_id'], len(dataset['files']), flush=True)
        results = []
        journal = OUT / 'cohort/provenance' / (dataset['candidate_id'] + '_downloads.jsonl')
        with journal.open('x') as log, concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            futures = [pool.submit(transfer, dataset['proposed_destination'], spec) for spec in dataset['files']]
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                results.append(result)
                log.write(json.dumps(result) + '\n')
                log.flush()
                if len(results) % 25 == 0 or result['status'] != 'VERIFIED':
                    print(dataset['candidate_id'], len(results), '/', len(futures),
                          result['status'], result['relative_path'], flush=True)
        dataset.update(status='VERIFIED' if all(r['status'] == 'VERIFIED' for r in results)
                       else 'PARTIAL_WITH_ERRORS', verified_files=sum(r['status'] == 'VERIFIED' for r in results),
                       errors=[r for r in results if r['status'] != 'VERIFIED'], finished_at=now(),
                       receipt_path=str(journal.relative_to(ROOT)))
        manifest['status'] = 'DOWNLOAD_IN_PROGRESS'
        path.write_text(json.dumps(manifest, indent=2) + '\n')
        print('END', dataset['candidate_id'], dataset['status'], flush=True)
    manifest.update(status='PUBLIC_DOWNLOADS_COMPLETE' if all(r['status'] == 'VERIFIED' for r in manifest['entries'])
                    else 'PUBLIC_DOWNLOADS_COMPLETE_WITH_ERRORS', finished_at=now())
    path.write_text(json.dumps(manifest, indent=2) + '\n')
    print(manifest['status'], flush=True)


if __name__ == '__main__':
    main()
