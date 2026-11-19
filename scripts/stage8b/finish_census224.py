"""Verify the bounded native batch and release Slurm resources on wrapper exit."""
import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from harness_state import mutate_gpu_queue


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_batch(cfg):
    root = Path(cfg['output_dir'])
    assert digest(cfg['manifest']) == cfg['manifest_sha256']
    assert digest(cfg['cohort_artifact_index']) == cfg['cohort_artifact_index_sha256']
    assert digest(cfg['bounded_cohort_manifest']) == cfg['bounded_cohort_manifest_sha256']
    expected = [json.loads(x) for x in Path(cfg['manifest']).read_text().splitlines()]
    assert len(expected) == 224 and len({r['item_id'] for r in expected}) == 224
    paths = list(root.glob('examples/*/result.json'))
    assert len(paths) == 224
    by_id = {json.loads(p.read_text())['item_id']: p for p in paths}
    assert set(by_id) == {r['item_id'] for r in expected}
    for row in expected:
        path = by_id[row['item_id']]
        receipt = json.loads(path.read_text())
        assert receipt['family_id'] == row['family_id']
        assert json.loads((path.parent/'manifest_row.json').read_text()) == row
        for name, sha in receipt['provenance_sha256'].items():
            assert digest(name) == sha, name
    env = [json.loads((root/'census'/f'worker{i}'/'environment.json').read_text()) for i in range(4)]
    assert len({e['gpu_uuid'] for e in env}) == 4
    for i in range(4):
        state = json.loads((root/'census'/f'worker{i}'/'completed.json').read_text())
        assert state['completed'] and state['items'] == [r['item_id'] for r in expected[i::4]]
    index = json.loads(Path(cfg['cohort_artifact_index']).read_text())
    assert len(index['rows']) == 256 and len({r['item_id'] for r in index['rows']}) == 256
    combined = [json.loads(x) for x in Path(cfg['bounded_cohort_manifest']).read_text().splitlines()]
    assert len(combined) == 256 and combined[32:] == expected
    assert [r['item_id'] for r in index['rows']] == [r['item_id'] for r in combined]
    for row in index['rows'][:32]:
        assert digest(row['receipt']) == row['receipt_sha256'], row['item_id']
        receipt = json.loads(Path(row['receipt']).read_text())
        assert receipt['item_id'] == row['item_id']
        for name, sha in receipt['provenance_sha256'].items():
            assert digest(name) == sha, name
    return paths


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', type=Path, required=True)
    ap.add_argument('--exit-code', type=int, required=True)
    args = ap.parse_args()
    cfg = json.loads(args.config.read_text())
    root = Path(cfg['output_dir'])
    paths = list(root.glob('examples/*/result.json'))
    error = None
    if args.exit_code == 0:
        try:
            paths = verify_batch(cfg)
        except Exception as exc:
            error = f'{type(exc).__name__}: {exc}'
    complete = args.exit_code == 0 and error is None
    record = dict(completed=complete, exit_code=args.exit_code,
                  verification_error=error, examples=len(paths), cohort_total=256,
                  slurm_job_id=os.environ['SLURM_JOB_ID'],
                  at=datetime.now(timezone.utc).isoformat(), config_sha256=digest(args.config),
                  result_sha256={str(p): digest(p) for p in paths},
                  gpu_release='Wrapper exits now; verify release independently.',
                  next_step='256-item passive/semantic discovery analysis; no automatic new GPU job')
    root.mkdir(parents=True, exist_ok=True)
    dest = root/'wrapper.json'
    with dest.open('x') as stream:
        json.dump(record, stream, indent=2)
        stream.write('\n')
    def update(queue):
        job = next(j for j in queue['jobs'] if j['id'] == cfg['scheduler_id'])
        job.update(status='succeeded' if complete else 'failed',
                   finished_at=record['at'], result_path=str(dest))
    mutate_gpu_queue(Path.cwd(), update)
    print(json.dumps({k: v for k, v in record.items() if k != 'result_sha256'}), flush=True)
    if not complete:
        raise SystemExit(args.exit_code or 1)


if __name__ == '__main__':
    main()
