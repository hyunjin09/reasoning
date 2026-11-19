"""Finite batch-one Stage11C calls; no scoring or automatic next phase."""
import argparse
import os
import socket
import time
import traceback
from pathlib import Path
import torch
from scripts.stage11c.common import ROOT, load, save, sha, now
from scripts.stage11b.generation import runtime, prepare, generate
from visual_reasoning.stage0.modeling import runtime_environment


def main(manifest_path, manifest_sha256, shard_id, max_seconds):
    started = time.monotonic()
    job = os.environ['SLURM_JOB_ID']
    assert sha(manifest_path) == manifest_sha256
    manifest = load(manifest_path)
    cfg = load(ROOT/'config.json')
    assert manifest['frozen'] and sha(ROOT/'config.json') == manifest['config_sha256']
    for path, digest in cfg['source_sha256'].items():
        assert sha(path) == digest, path
    shard = next(s for s in manifest['shards'] if s['id'] == shard_id)
    queue = ROOT/manifest['queue']
    assert cfg['batch_size'] == 1 and torch.cuda.device_count() == 1
    assert socket.gethostname().split('.')[0] in cfg['allowed_nodes']
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    info = cfg['models'][shard['model_key']]
    for name, digest in info['files_sha256'].items():
        assert sha(Path(info['checkpoint'])/name) == digest, name
    proc, model = runtime(info)
    save(queue/'workers'/job/'environment.json', dict(at=now(), slurm_job_id=job,
        node=socket.gethostname(), shard_id=shard_id, batch_size=1, tf32=False,
        config_sha256=sha(ROOT/'config.json'), manifest_sha256=manifest_sha256,
        **runtime_environment(Path(info['checkpoint']), model, max(r['max_new_tokens'] for r in shard['rows']))))
    complete = 0
    for row in shard['rows']:
        if (queue/'STOP').exists() or time.monotonic()-started > max_seconds-180:
            print('SAFE_STOP_BETWEEN_EXAMPLES', flush=True)
            break
        dest = queue/'results'/row['task_id']
        try:
            assert not dest.exists(), 'Do not overwrite or regenerate existing attempts'
            assert row['max_new_tokens'] in cfg['candidate_caps']
            if row['condition'] == 'native':
                assert sha(row['image']) == row['image_sha256']
            claim = queue/'claims'/row['task_id']
            claim.mkdir(parents=False, exist_ok=False)
            save(claim/'owner.json', dict(at=now(), slurm_job_id=job, shard=shard_id))
            batch, metas = prepare(proc, [row])
            assert batch['input_ids'].shape[0] == 1 and metas[0]['batch_left_padding'] == 0
            if row['condition'] != 'native':
                assert not any(k in batch for k in ['pixel_values', 'image_grid_thw', 'past_key_values'])
                assert metas[0]['visual_token_count'] == 0
                if 'mm_token_type_ids' in batch:
                    assert torch.count_nonzero(batch['mm_token_type_ids']).item() == 0
            save(dest/'input.json', metas[0])
            out, = generate(proc, model, batch, row['max_new_tokens'],
                max_time=max(1, max_seconds-(time.monotonic()-started)-45))
            save(dest/'generation.json', out)
            receipt = {k: v for k, v in out.items() if k not in ['raw_decoded_response', 'generated_token_ids']}
            answer_region = out['raw_decoded_response'].split('</think>', 1)[-1]
            structural_complete = bool(answer_region.replace('<|im_end|>', '').strip())
            if row['arm'] == 'thinking':
                structural_complete = structural_complete and out['has_think_end']
            save(dest/'result.json', dict(receipt, at=now(), task_id=row['task_id'], item_id=row['item_id'],
                family_id=row['family_id'], arm=row['arm'], condition=row['condition'], slurm_job_id=job,
                cap=row['max_new_tokens'], structural_complete=structural_complete, batch_size=1,
                generation_sha256=sha(dest/'generation.json'), input_sha256=sha(dest/'input.json'),
                config_sha256=sha(ROOT/'config.json'), manifest_sha256=manifest_sha256))
            complete += not out['budget_interrupted']
            print('COMPLETE', row['task_id'], 'tokens', out['tokens'], 'capped', out['at_length_cap'],
                  'interrupted', out['budget_interrupted'], 'seconds', round(out['batch_seconds'], 2), flush=True)
            del batch, out
        except Exception as exc:
            save(queue/'workers'/job/'failure.json', dict(at=now(), error=repr(exc),
                traceback=traceback.format_exc(), task_id=row['task_id']))
            raise
    save(queue/'workers'/job/'exit.json', dict(at=now(), elapsed_seconds=time.monotonic()-started,
        finite_queue=True, completed=complete, shard_total=len(shard['rows']), complete=complete==len(shard['rows'])))
    print('WORKER_EXIT', complete, '/', len(shard['rows']), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--manifest-sha256', required=True)
    parser.add_argument('--shard', required=True)
    parser.add_argument('--max-seconds', type=int, required=True)
    args = parser.parse_args()
    main(args.manifest, args.manifest_sha256, args.shard, args.max_seconds)
