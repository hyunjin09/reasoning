"""Verify a resumed125-item batch plus131 preserved cohort members."""
import argparse
import hashlib
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from harness_state import mutate_gpu_queue


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def verify(cfg):
    for name in ['manifest', 'cohort_artifact_index', 'bounded_cohort_manifest']:
        assert digest(cfg[name]) == cfg[name+'_sha256']
    root = Path(cfg['output_dir'])
    rows = [json.loads(x) for x in Path(cfg['manifest']).read_text().splitlines()]
    combined = [json.loads(x) for x in Path(cfg['bounded_cohort_manifest']).read_text().splitlines()]
    index = json.loads(Path(cfg['cohort_artifact_index']).read_text())['rows']
    assert len(rows) == 125 and len({r['item_id'] for r in rows}) == 125
    assert len(combined) == 256 and len({r['item_id'] for r in combined}) == 256
    assert [r['item_id'] for r in index] == [r['item_id'] for r in combined]
    by_id = {r['item_id']: r for r in combined}
    new_ids = {r['item_id'] for r in rows}
    assert [r for r in combined if r['item_id'] in new_ids] == rows
    paths = list(root.glob('examples/*/result.json'))
    assert len(paths) == 125 and {p.parent.name for p in paths} == new_ids
    for row in index:
        p = Path(row['receipt']); receipt = json.loads(p.read_text())
        assert receipt['item_id'] == row['item_id'] and receipt['family_id'] == row['family_id']
        assert json.loads((p.parent/'manifest_row.json').read_text()) == by_id[row['item_id']]
        if row['receipt_sha256'] is not None:
            assert row['item_id'] not in new_ids and digest(p) == row['receipt_sha256']
        else:
            assert row['item_id'] in new_ids and p == root/'examples'/row['item_id']/'result.json'
        for artifact, sha in receipt['provenance_sha256'].items():
            assert digest(artifact) == sha, artifact
    assert sum(r['receipt_sha256'] is not None for r in index) == 131
    layout = json.loads(Path(cfg['layout_decision']).read_text())
    count = layout['worker_count']; per_gpu = layout['workers_per_gpu']
    assert count == 2*per_gpu and per_gpu in (1, 2) and layout['exact_parity']
    env = [json.loads((root/'census'/f'worker{i}'/'environment.json').read_text()) for i in range(count)]
    assert sorted(Counter(e['gpu_uuid'] for e in env).values()) == [per_gpu, per_gpu]
    for i, e in enumerate(env):
        assert e['rank'] == i and e['slurm_parent_rank'] == i//per_gpu and e['workers_per_gpu'] == per_gpu
        assert e['hostname'].split('.')[0] == 'node06'
        state = json.loads((root/'census'/f'worker{i}'/'completed.json').read_text())
        assert state['completed'] and state['items'] == [r['item_id'] for r in rows[i::count]]
    return paths


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--config', required=True); ap.add_argument('--exit-code', type=int, required=True)
    args = ap.parse_args(); cfg = json.loads(Path(args.config).read_text()); root = Path(cfg['output_dir'])
    root.mkdir(parents=True, exist_ok=True)
    paths = list(root.glob('examples/*/result.json')); error = None
    if args.exit_code == 0:
        try:
            paths = verify(cfg)
        except Exception as exc:
            error = f'{type(exc).__name__}: {exc}'
    complete = args.exit_code == 0 and error is None
    result = dict(at=datetime.now(timezone.utc).isoformat(), completed=complete, exit_code=args.exit_code,
                  verification_error=error, new_examples=len(paths), preserved_examples=131, cohort_target=256,
                  slurm_job_id=os.environ['SLURM_JOB_ID'], config_sha256=digest(args.config),
                  result_sha256={str(p): digest(p) for p in paths}, stage_complete=False,
                  gpu_release='Batch exits now; verify release independently', next_step='Semantic/passive discovery analysis; no automatic follow-up GPU job')
    dest = root/'wrapper.json'
    with dest.open('x') as stream: json.dump(result, stream, indent=2)
    def update(queue):
        job = next(j for j in queue['jobs'] if j['id'] == cfg['scheduler_id'])
        job.update(status='succeeded' if complete else 'failed', finished_at=result['at'], result_path=str(dest))
    mutate_gpu_queue(Path.cwd(), update)
    print(json.dumps({k:v for k,v in result.items() if k != 'result_sha256'}), flush=True)
    if not complete: raise SystemExit(args.exit_code or 1)
