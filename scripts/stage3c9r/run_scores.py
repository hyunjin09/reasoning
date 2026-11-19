#!/usr/bin/env python3
"""Score every frozen event; no source-sensitive computational pre-gate."""

import argparse
import gc
import json
import os
import platform
import time
from pathlib import Path

import torch

from visual_reasoning.stage0.data import load_mathverse_rows
from visual_reasoning.stage0.modeling import load_runtime, runtime_environment
from visual_reasoning.stage3a.runtime import prepare_custom_image
from visual_reasoning.stage3c8.protocol import distributed_process_info
from visual_reasoning.stage3c9.assay import CONDITIONS, exact_readout_sequences
from visual_reasoning.stage3c9.streaming import prefill_streaming_state
from visual_reasoning.stage3c9r.runtime import score_family
from scripts.stage3c9r.freeze_inputs import ROOT, OUT, read_json, read_jsonl, sha, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--role', choices=['validation', 'primary', 'lifetime', 'necessity'], required=True)
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    config = read_json(OUT / 'config/stage3c9r_config.json')
    if os.environ.get('SLURM_JOB_ID') != config['runtime']['slurm_allocation']:
        raise RuntimeError('Must run inside the user-provided frozen allocation')
    world, rank, device = distributed_process_info(os.environ, visible_device_count=torch.cuda.device_count())
    if world != 4 or torch.cuda.device_count() != 4:
        raise RuntimeError('Exactly four Slurm-visible GPUs and four ranks are required')
    torch.cuda.set_device(device)
    if 'A6000' not in torch.cuda.get_device_name(device):
        raise RuntimeError('A6000 required')
    if args.role == 'primary' and not read_json(OUT / 'audit/mechanical_validation.json')['passed']:
        raise RuntimeError('Mechanical validation must pass before primary')
    code_hashes = {str(p.relative_to(ROOT)): sha(p) for p in [
        ROOT / 'code/visual_reasoning/stage3c9r/runtime.py',
        ROOT / 'code/visual_reasoning/stage3c9r/protocol.py',
        ROOT / 'code/visual_reasoning/stage3c9/streaming.py',
        ROOT / 'code/visual_reasoning/stage3c4/runtime.py',
    ]}
    manifest_role = 'validation' if args.role == 'validation' else 'primary'
    manifest = read_jsonl(OUT / f'cohort/{manifest_role}_manifest.jsonl')[rank::world]
    root = OUT / ('audit/raw' if args.role == 'validation' else
                  'same_path_scores/raw' if args.role == 'primary' else f'{args.role}_raw')
    shard = root / f'shard_{rank}'
    previous = read_json(shard / 'run_config.json') if (shard / 'run_config.json').exists() else None
    if previous and previous['scoring_code_sha256'] != code_hashes:
        raise RuntimeError('Scoring implementation changed since this shard started')
    run_config = {'role': args.role, 'rank': rank, 'world_size': world,
                  'slurm_job_id': os.environ['SLURM_JOB_ID'], 'node': platform.node(),
                  'command': list(__import__('sys').argv), 'config_sha256': sha(OUT / 'config/stage3c9r_config.json'),
                  'scoring_code_sha256': code_hashes,
                  'base_problem_ids': [str(r['base_problem_id']) for r in manifest],
                  'all_frozen_events_scored_without_pre_gate': args.role in ('validation', 'primary')}
    write_json(shard / 'run_config.json', run_config)
    tasks = None
    if args.role in ('lifetime', 'necessity'):
        tasks = read_json(OUT / f'analysis/{args.role}_tasks.json')['tasks']
    dataset = {str(r['sample_index']): r for r in load_mathverse_rows(Path(config['dataset_root']))}
    processor, model = load_runtime(Path(config['model_checkpoint']), device='cuda')
    environment = runtime_environment(Path(config['model_checkpoint']), model, 40960)
    if next(model.parameters()).dtype != torch.bfloat16:
        raise RuntimeError('Frozen BF16 model dtype violated')
    write_json(shard / 'environment.json', {**environment, **run_config,
        'CUDA_VISIBLE_DEVICES': os.environ.get('CUDA_VISIBLE_DEVICES'),
        'local_device': device, 'torch': torch.__version__})
    layers = list(range(model.config.text_config.num_hidden_layers))
    heads = list(range(model.config.text_config.num_attention_heads))
    assert len(layers) == 36 and len(heads) == 32
    torch.cuda.reset_peak_memory_stats()
    started = time.perf_counter()
    completed, resumed = 0, 0
    for item in manifest:
        base = str(item['base_problem_id'])
        tokens = read_jsonl(ROOT / item['tokens_path'])
        final = exact_readout_sequences(tokens, item['final_use_readout'])
        edit = read_json(ROOT / item['edit_metadata'])
        visual = item['roi_mapping']['absolute_source_groups']['V_all']
        target = item['roi_mapping']['absolute_source_groups']['V_target']
        active_events = item['events']
        if tasks is not None:
            active_events = [e for e in active_events if any(t['base_problem_id'] == base and t['event_id'] == e['event_id'] for t in tasks)]
        expected_layout = None
        for condition in (CONDITIONS if args.role in ('validation', 'primary') else ('O', 'C')):
            pending = []
            for event in active_events:
                event_tasks = ([{'readout': event['local_use_readout'], 'readout_name': 'local', 'windows': ['W8', 'W16']}]
                               if tasks is None else [t for t in tasks if t['base_problem_id'] == base and t['event_id'] == event['event_id']])
                for task in event_tasks:
                    path = shard / base / str(event['event_id']) / f"{condition}_{task['readout_name']}.json"
                    if path.exists():
                        if not args.resume:
                            raise FileExistsError(path)
                        existing = read_json(path)
                        if existing['config_sha256'] != run_config['config_sha256']:
                            raise RuntimeError('Resume config mismatch')
                        resumed += 1
                    else:
                        pending.append((event, task, path))
            if not pending:
                continue
            prepared, metadata = prepare_custom_image(processor, dataset[str(item['example_id'])],
                                                       ROOT / edit['paths'][condition], device='cuda')
            layout = (metadata['prompt_token_ids'], metadata['image_grid_thw'])
            if expected_layout is not None and layout != expected_layout:
                raise RuntimeError('Quartet prompt/grid mismatch')
            expected_layout = layout
            if metadata['visual_token_indices'] != visual:
                raise RuntimeError('Frozen ROI layout mismatch')
            prefill, prefill_audit = prefill_streaming_state(model=model, prepared=prepared, seed=1234)
            del prepared
            for event, task, path in pending:
                t0 = time.perf_counter()
                sequences = exact_readout_sequences(tokens, task['readout'])
                event_id = int(event['event_id'])
                execution_prefix = f"3c9r/{base}/{event_id}/{condition}/{task['readout_name']}"
                scores = score_family(model=model, prefill=prefill, sequences=sequences, event=event,
                    layers=layers, heads=heads, target_positions=target, visual_positions=visual,
                    seed=1234, execution_prefix=execution_prefix,
                    validate=args.role == 'validation', windows=task['windows'],
                    compare_inherited=args.role == 'validation' and condition == 'O' and event is item['events'][0],
                    necessity=args.role == 'necessity')
                result = {'base_problem_id': base, 'event_id': event_id, 'condition': condition,
                    'role': args.role, 'readout_name': task['readout_name'],
                    'readout': task['readout'], 'event': event, 'windows': scores,
                    'target_positions': target, 'visual_positions': visual,
                    'prompt_length': prefill.prompt_length, 'prefill_audit': prefill_audit,
                    'final_readout_index': final['readout_generated_index'],
                    'final_prefix_hash_exact': final['prefix_hash_exact'],
                    'config_sha256': run_config['config_sha256'],
                    'runtime_seconds': time.perf_counter() - t0,
                    'peak_gpu_allocated_bytes': int(torch.cuda.max_memory_allocated()),
                    'peak_gpu_reserved_bytes': int(torch.cuda.max_memory_reserved())}
                partial = path.with_suffix('.part')
                write_json(partial, result)
                partial.replace(path)
                completed += 1
                print(f"rank={rank} base={base} event={event_id} condition={condition} readout={task['readout_name']} windows={len(scores)} seconds={result['runtime_seconds']:.1f}", flush=True)
            del prefill
            gc.collect()
            torch.cuda.empty_cache()
    torch.cuda.synchronize()
    write_json(shard / 'run_summary.json', {'role': args.role, 'rank': rank, 'completed': completed,
        'resumed': resumed, 'runtime_seconds': time.perf_counter() - started,
        'peak_gpu_allocated_bytes': int(torch.cuda.max_memory_allocated()),
        'peak_gpu_reserved_bytes': int(torch.cuda.max_memory_reserved())})
    print(f'rank={rank} COMPLETE role={args.role} new={completed} resumed={resumed}', flush=True)


if __name__ == '__main__':
    main()
