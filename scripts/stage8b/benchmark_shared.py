"""Compare fixed short native workloads, excluding model load and synchronization."""
import argparse
import gc
import hashlib
import json
import os
import socket
import time
from pathlib import Path

import joblib
import torch

from scripts.stage8b.run_native_v2_shared import digest, save, technical_check
from visual_reasoning.stage0.modeling import generate_once, load_runtime, runtime_environment
from visual_reasoning.stage8b.passive import PassiveRecorder
from visual_reasoning.stage8b.shared_execution import runtime_rank
from visual_reasoning.stage8b.single_execution import NativeProgress
from visual_reasoning.stage8b.v2_protocol import generation_parameters, prepared_input


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', required=True)
    ap.add_argument('--workers-per-gpu', type=int, choices=[1, 2], required=True)
    ap.add_argument('--lane', type=int, required=True)
    args = ap.parse_args()
    cfg = json.loads(Path(args.config).read_text())
    assert socket.gethostname().split('.')[0] == 'node06'
    rank = runtime_rank(os.environ, visible_devices=torch.cuda.device_count(), allocation=os.environ.get('SLURM_JOB_ID'),
                        lane=args.lane, workers_per_gpu=args.workers_per_gpu)
    torch.cuda.set_device(0)
    assert cfg['generation_parameters'] == generation_parameters() and cfg['presence_penalty'] == 0
    for p, sha in cfg['source_sha256'].items():
        assert digest(p) == sha, p
    assert digest(cfg['manifest']) == cfg['manifest_sha256']
    rows = [json.loads(x) for x in Path(cfg['manifest']).read_text().splitlines()]
    assert [r['item_id'] for r in rows[:4]] == cfg['performance_probe_ids']
    parent = int(os.environ['SLURM_PROCID'])
    indices = [2*parent, 2*parent+1] if args.workers_per_gpu == 1 else [2*parent+args.lane]
    phase = 'benchmark_single' if args.workers_per_gpu == 1 else 'benchmark_double'
    output = Path(cfg['output_dir'])/phase
    worker = output/f'worker{rank}'
    assert not worker.exists(), worker
    freeze = Path(cfg['detector_freeze'])
    assert digest(freeze) == cfg['detector_freeze_sha256']
    rule = json.loads(freeze.read_text())
    assert digest(rule['retrieval']['models']) == rule['retrieval']['models_sha256']
    fitted = joblib.load(rule['retrieval']['models'])['joint']
    assert fitted['spec'] == rule['retrieval']['spec'] and fitted['threshold'] == rule['retrieval']['tau_R']
    processor, model = load_runtime(Path(cfg['model_checkpoint']), device='cuda:0')
    assert str(next(model.parameters()).dtype) == 'torch.bfloat16'
    env = runtime_environment(Path(cfg['model_checkpoint']), model, cfg['performance_probe_tokens'])
    assert (env['language_layers'], env['attention_heads'], env['kv_heads']) == (28, 16, 8)
    env.update(rank=rank, gpu_uuid=str(torch.cuda.get_device_properties(0).uuid), hostname=socket.gethostname(),
               slurm_job_id=os.environ['SLURM_JOB_ID'], config_sha256=digest(args.config), workers_per_gpu=args.workers_per_gpu)
    save(worker/'environment.json', env)
    prepared, metadata = prepared_input(processor, rows[indices[0]])
    check = technical_check(model, processor, prepared, metadata, fitted['model'], cfg['seed'])
    save(worker/'checks.json', check)
    del prepared
    gc.collect()
    torch.cuda.empty_cache()
    save(output/'barrier'/f'{rank}.json', dict(ready=True))
    deadline = time.monotonic()+300
    while not all((output/'barrier'/f'{i}.json').exists() for i in range(2*args.workers_per_gpu)):
        if time.monotonic() > deadline:
            raise TimeoutError('Benchmark workers failed to synchronize')
        time.sleep(.1)
    results = []
    for index in indices:
        row = rows[index]
        prepared, metadata = prepared_input(processor, row)
        logits = []
        def capture(_module, _args, value):
            logits.append(hashlib.sha256(value[0, -1].detach().float().cpu().numpy().tobytes()).hexdigest())
        handle = model.lm_head.register_forward_hook(capture)
        started = time.time()
        try:
            with NativeProgress(model, row['item_id']), PassiveRecorder(visual=metadata['visual_token_indices'], prompt_length=metadata['prompt_token_count'], model=fitted['model']) as observer:
                generated = generate_once(model, processor, prepared, cfg['performance_probe_tokens'], recorder=None,
                                          generation_kwargs=generation_parameters(), seed=cfg['seed'], collect_predictive_metrics=False)
            arrays = observer.arrays()
            finished = time.time()
            result = dict(item_id=row['item_id'], tokens=len(generated['generated_token_ids']),
                          token_ids=generated['generated_token_ids'], raw_logit_sha256=logits,
                          passive_sha256={k: hashlib.sha256(v.tobytes()).hexdigest() for k, v in arrays.items()},
                          started=started, finished=finished, runtime=generated['runtime'])
        finally:
            handle.remove()
        save(worker/f"item_{row['item_id']}.json", result)
        results.append(dict(item_id=row['item_id'], tokens=result['tokens'], started=started, finished=finished,
                            peak_gpu_reserved_bytes=result['runtime']['peak_gpu_reserved_bytes']))
        del generated, observer, arrays, prepared
        gc.collect()
        torch.cuda.empty_cache()
    save(worker/'completed.json', dict(completed=True, items=results))
    print(json.dumps(dict(event='benchmark_complete', phase=phase, rank=rank, items=results)), flush=True)


if __name__ == '__main__':
    main()
