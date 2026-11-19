"""Download the approved pinned files, one benchmark at a time, without HF caches."""
import concurrent.futures
import datetime
import hashlib
import json
from pathlib import Path
import time
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'outputs/stage7a_bench'
DEST = Path('/data/dataset/reasoning_steps_stage7a_bench')


def now():
    return datetime.datetime.now().astimezone().isoformat()


def safe_target(destination, relative):
    base = Path(destination).resolve()
    path = (base / relative).resolve()
    if not path.is_relative_to(base) or path == base:
        raise ValueError('Manifest path would escape dataset directory')
    return path


def verify_content_hashes(payload, spec):
    digest = hashlib.sha256(payload).hexdigest()
    if spec.get('sha256'):
        if digest != spec['sha256']:
            raise ValueError('Release SHA256 mismatch')
    elif spec.get('git_blob_oid'):
        header = f'blob {len(payload)}\0'.encode()
        git_hash = hashlib.sha1(header + payload).hexdigest()
        if git_hash != spec['git_blob_oid']:
            raise ValueError('Release Git blob hash mismatch')
    return digest


def transfer(destination, spec):
    start = time.perf_counter()
    record = dict(relative_path=spec['relative_path'], started_at=now(), url=spec['url'])
    try:
        target = safe_target(destination, spec['relative_path'])
        if not target.is_relative_to(DEST.resolve()):
            raise ValueError('Destination is outside approved stage directory')
        target.parent.mkdir(parents=True, exist_ok=True)
        reused = target.exists()
        partial = target.with_name(target.name + '.stage7a_bench.part')
        if not reused:
            if partial.exists():
                raise ValueError('Preserved partial download requires explicit diagnosis')
            request = urllib.request.Request(urllib.parse.quote(spec['url'], safe=':/%'),
                headers={'User-Agent': 'stage7a-benchmark-research'})
            with urllib.request.urlopen(request, timeout=45) as response, partial.open('xb') as f:
                for block in iter(lambda: response.read(1024 * 1024), b''):
                    f.write(block)
            payload = partial.read_bytes()
        else:
            payload = target.read_bytes()
        if spec.get('bytes') is not None and len(payload) != spec['bytes']:
            raise ValueError('Release byte count mismatch')
        digest = verify_content_hashes(payload, spec)
        if not reused:
            partial.rename(target)
        record.update(status='VERIFIED', bytes=len(payload), sha256=digest,
                      destination=str(target), reused_verified_existing=reused)
    except Exception as exc:
        record.update(status='FAILED', error_type=type(exc).__name__, error=str(exc))
    record.update(finished_at=now(), elapsed_seconds=time.perf_counter() - start)
    return record


def main():
    path = OUT / 'cohort/download_manifest.json'
    manifest = json.loads(path.read_text())
    if manifest['policy_approval_required'] or 'authorization' not in manifest:
        raise RuntimeError('External destination has not been authorized')
    if not (OUT / 'cohort/dataset_inventory.json').exists():
        raise RuntimeError('Inventory must precede downloads')
    for dataset in manifest['entries']:
        print('START', dataset['candidate_id'], len(dataset['files']), 'files', flush=True)
        results = []
        journal = OUT / 'cohort/provenance' / (dataset['candidate_id'] + '_downloads.jsonl')
        with journal.open('a') as log, concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            futures = [pool.submit(transfer, dataset['proposed_destination'], spec)
                       for spec in dataset['files']]
            for future in concurrent.futures.as_completed(futures):
                record = future.result()
                log.write(json.dumps(record) + '\n')
                log.flush()
                results.append(record)
                if len(results) % 25 == 0 or record['status'] != 'VERIFIED':
                    print(dataset['candidate_id'], len(results), '/', len(futures),
                          record['status'], record['relative_path'], flush=True)
        dataset.update(status='VERIFIED' if all(r['status'] == 'VERIFIED' for r in results)
                       else 'PARTIAL_WITH_ERRORS', downloads_performed=sum(
                           r['status'] == 'VERIFIED' and not r['reused_verified_existing'] for r in results),
                       verified_files=sum(r['status'] == 'VERIFIED' for r in results),
                       errors=[r for r in results if r['status'] != 'VERIFIED'],
                       receipt_path=str(journal.relative_to(ROOT)), finished_at=now())
        manifest['status'] = 'DOWNLOAD_IN_PROGRESS'
        path.write_text(json.dumps(manifest, indent=2) + '\n')
        print('END', dataset['candidate_id'], dataset['status'], flush=True)
    manifest['status'] = ('ALL_DOWNLOADED_VERIFIED' if all(
        d['status'] == 'VERIFIED' for d in manifest['entries']) else 'COMPLETE_WITH_DATASET_BLOCKERS')
    manifest['finished_at'] = now()
    path.write_text(json.dumps(manifest, indent=2) + '\n')
    print(manifest['status'], flush=True)


if __name__ == '__main__':
    main()
