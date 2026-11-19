"""Finite, versioned attempts for original tasks still relevant to discovery GO."""
import argparse
import os
import socket
import time
import traceback
from pathlib import Path
import torch
from scripts.stage11b.common import ROOT, load, save, sha, now
from scripts.stage11b.generation import runtime, prepare, generate
from visual_reasoning.stage0.modeling import runtime_environment


def main(shard_id, max_seconds):
    started = time.monotonic()
    job = os.environ['SLURM_JOB_ID']
    queue = ROOT/'source_feasible'
    cfg = load(ROOT/'config.json')
    execution = load(ROOT/'source_feasible_execution.json')
    manifest = load(ROOT/'source_feasible_tasks.json')
    assert sha(ROOT/'source_feasible_tasks.json') == execution['manifest_sha256']
    assert sha(__file__) == execution['worker_sha256']
    assert sha(ROOT/'config.json') == manifest['config_sha256']
    for p, h in cfg['source_sha256'].items():
        assert sha(p) == h, p
    shard = next(s for s in manifest['shards'] if s['id'] == shard_id)
    originals = {r['task_id']: r for r in load(ROOT/'discovery_tasks.json')['rows']}
    assert len(shard['rows']) % cfg['batch_size'] == 0
    for row in shard['rows']:
        assert {k: v for k, v in row.items() if k != 'required_for_remaining_gate'} == originals[row['task_id']]
        assert not (ROOT/'discovery/results'/row['task_id']/'result.json').exists(), 'Never rerun a completed result'
    assert torch.cuda.device_count() == 1
    assert socket.gethostname().split('.')[0] in ['node02', 'node03', 'node06', 'node07']
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    info = cfg['models'][shard['model_key']]
    for name, h in info['files_sha256'].items():
        assert sha(Path(info['checkpoint'])/name) == h, name
    proc, model = runtime(info)
    save(queue/'workers'/job/'environment.json', dict(at=now(), slurm_job_id=job,
        node=socket.gethostname(), shard_id=shard_id, tf32=False,
        config_sha256=sha(ROOT/'config.json'), execution_sha256=sha(ROOT/'source_feasible_execution.json'),
        **runtime_environment(Path(info['checkpoint']), model, cfg['max_new_tokens'])))
    complete = 0
    for start in range(0, len(shard['rows']), cfg['batch_size']):
        if (queue/'STOP').exists() or time.monotonic()-started > max_seconds-600:
            print('SAFE_STOP_BETWEEN_BATCHES', flush=True)
            break
        rows = shard['rows'][start:start+cfg['batch_size']]
        try:
            for row in rows:
                dest = queue/'results'/row['task_id']
                assert not dest.exists()
                assert sha(row['image']) == row['image_sha256']
                lock = queue/'claims'/row['task_id']
                lock.mkdir(parents=False, exist_ok=False)
                save(lock/'owner.json', dict(at=now(), slurm_job_id=job, shard_id=shard_id))
            batch, metas = prepare(proc, rows)
            for row, meta in zip(rows, metas):
                save(queue/'results'/row['task_id']/'input.json', meta)
            outputs = generate(proc, model, batch, cfg['max_new_tokens'],
                max_time=max(1, max_seconds-(time.monotonic()-started)-45))
            for row, out in zip(rows, outputs):
                dest = queue/'results'/row['task_id']
                save(dest/'generation.json', out)
                receipt = {k: v for k, v in out.items() if k not in ['raw_decoded_response', 'generated_token_ids']}
                save(dest/'result.json', dict(receipt, at=now(), task_id=row['task_id'], item_id=row['item_id'],
                    family_id=row['family_id'], arm=row['arm'], condition=row['condition'], slurm_job_id=job,
                    required_for_remaining_gate=row['required_for_remaining_gate'],
                    generation_sha256=sha(dest/'generation.json'), input_sha256=sha(dest/'input.json'),
                    config_sha256=sha(ROOT/'config.json')))
                complete += 1
                print('COMPLETE', row['task_id'], 'tokens', out['tokens'], 'batch_seconds', round(out['batch_seconds'], 2), flush=True)
            del batch, outputs
        except Exception as exc:
            save(queue/'workers'/job/'failure.json', dict(at=now(), error=repr(exc), traceback=traceback.format_exc(),
                task_ids=[r['task_id'] for r in rows]))
            raise
    save(queue/'workers'/job/'exit.json', dict(at=now(), elapsed_seconds=time.monotonic()-started,
        finite_queue=True, completed=complete, shard_total=len(shard['rows']), complete=complete==len(shard['rows'])))
    print('WORKER_EXIT', complete, '/', len(shard['rows']), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--shard', required=True)
    p.add_argument('--max-seconds', type=int, default=5300)
    a = p.parse_args()
    main(a.shard, a.max_seconds)
