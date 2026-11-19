"""Execute one frozen Stage4A scoring phase inside the existing allocation."""
import argparse
import gc
import os
import platform
import re
import sys
import time
from pathlib import Path
import torch
from scripts.stage4a.prepare_config import ROOT, OUT, read_json, read_jsonl, write_json, sha
from visual_reasoning.stage0.data import load_mathverse_rows
from visual_reasoning.stage0.modeling import load_runtime, runtime_environment
from visual_reasoning.stage3a.runtime import prepare_custom_image
from visual_reasoning.stage3c8.protocol import distributed_process_info
from visual_reasoning.stage3c9.streaming import prefill_streaming_state
from visual_reasoning.stage4a.runtime import make_event_root, score_event_arm


def score_equal(a, b):
    return all(a[k] == b[k] for k in ('D', 'L_o', 'L_c', 'current_logits_sha256', 'original_candidate', 'counterfactual_candidate'))


def verify_freeze():
    freeze = read_json(OUT/'cohort/cohort_freeze_complete.json')
    for path, digest in {**freeze['sha256'], **freeze['asset_metadata_sha256']}.items():
        if sha(ROOT/path) != digest:
            raise RuntimeError(f'Frozen input changed: {path}')
    return freeze


def atomic_json(path, result):
    part = path.with_suffix('.part')
    write_json(part, result)
    part.replace(path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--phase', required=True, choices=['validation', 'primary', 'trigger', 'semantic'])
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    if not re.fullmatch(args.phase+r'_\d{2}', args.run_id):
        raise ValueError('Run ID must be phase_NN')
    config = read_json(OUT/'config/stage4a_config.json')
    freeze = verify_freeze()
    if os.environ.get('SLURM_JOB_ID') != config['runtime']['slurm_allocation']:
        raise RuntimeError('Existing user allocation108548 required')
    world, rank, device = distributed_process_info(os.environ, visible_device_count=torch.cuda.device_count())
    if world != 4 or torch.cuda.device_count() != 4:
        raise RuntimeError('Exactly four assigned GPUs and ranks required')
    torch.cuda.set_device(device)
    if 'A6000' not in torch.cuda.get_device_name(device):
        raise RuntimeError('A6000 required')
    if args.phase != 'validation' and not read_json(OUT/'audit/mechanical_validation.json')['passed']:
        raise RuntimeError('Mechanical gate closed')
    primary_freeze = None
    if args.phase in ('trigger', 'semantic'):
        primary_freeze = read_json(OUT/'phase_b_source_switch/primary_freeze.json')
        if args.phase == 'trigger' and not primary_freeze['phase_c_gate_open']:
            raise RuntimeError('Confirmatory trigger gate closed')
        for path, digest in primary_freeze['raw_sha256'].items():
            if sha(ROOT/path) != digest:
                raise RuntimeError('Frozen primary result changed')
    manifest = ('cohort/validation_manifest.jsonl' if args.phase == 'validation' else
                'phase_d_counterfactual_refresh/subset_manifest.jsonl' if args.phase == 'semantic' else
                'cohort/primary_manifest.jsonl')
    items = read_jsonl(OUT/manifest)[rank::world]
    shard = OUT/'raw'/args.run_id/f'shard_{rank:02d}'
    code_paths = ['code/visual_reasoning/stage4a/runtime.py', 'scripts/stage4a/run_scores.py',
                  'code/visual_reasoning/stage3c10/runtime.py', 'code/visual_reasoning/stage3c9/streaming.py',
                  'code/visual_reasoning/stage3c4/runtime.py', 'code/visual_reasoning/stage3c3/runtime.py',
                  'code/visual_reasoning/stage3c3/metrics.py', 'code/visual_reasoning/stage0/modeling.py']
    signature = {'phase': args.phase, 'run_id': args.run_id, 'rank': rank, 'world_size': world,
                 'slurm_job_id': os.environ['SLURM_JOB_ID'], 'node': platform.node(), 'command': sys.argv,
                 'code_sha256': {p: sha(ROOT/p) for p in code_paths},
                 'cohort_freeze_sha256': sha(OUT/'cohort/cohort_freeze_complete.json'),
                 'manifest_sha256': sha(OUT/manifest)}
    if (shard/'run_config.json').exists():
        old = read_json(shard/'run_config.json')
        for key in ('code_sha256', 'cohort_freeze_sha256', 'manifest_sha256'):
            if old[key] != signature[key]:
                raise RuntimeError('Resume signature mismatch; preserve failed attempt and use a new run ID')
        if not args.resume:
            raise FileExistsError(shard)
    write_json(shard/'run_config.json', signature)
    dataset = {str(r['sample_index']): r for r in load_mathverse_rows(Path(config['dataset_root']))}
    processor, model = load_runtime(Path(config['model_checkpoint']), device='cuda')
    if next(model.parameters()).dtype != torch.bfloat16:
        raise RuntimeError('BF16 model required')
    if model.config.text_config.num_hidden_layers != 36 or model.config.text_config.num_attention_heads != 32:
        raise RuntimeError('Frozen model architecture mismatch')
    write_json(shard/'environment.json', {**runtime_environment(Path(config['model_checkpoint']), model, 40960),
               **signature, 'local_device': device, 'slurm_visible_devices': os.environ.get('CUDA_VISIBLE_DEVICES')})
    started = time.perf_counter()
    completed = 0
    for item in items:
        base = item['base_problem_id']
        meta = read_json(ROOT/item['asset_metadata'])
        conditions = ['OO', 'AO', 'OB', 'AB', 'A_sham', 'B_sham'] if args.phase in ('validation', 'semantic') else ['OO']
        for condition in conditions:
            pending = [e for e in ('A1', 'B', 'A2') if not (shard/base/condition/f'{e}.json').exists()]
            if not pending:
                continue
            prepared, observed = prepare_custom_image(processor, dataset[item['example_id']], ROOT/meta['paths'][condition], device='cuda')
            for key in ('prompt_token_ids', 'visual_token_indices', 'image_grid_thw'):
                if observed[key] != meta['prompt_metadata'][key]:
                    raise RuntimeError(f'Frozen image/prompt layout changed: {base}/{condition}/{key}')
            if processor.tokenizer.decode([observed['prompt_token_ids'][0]]) != '<|im_start|>':
                raise RuntimeError('Frozen passive sink token is not im_start')
            prefill, prefill_audit = prefill_streaming_state(model=model, prepared=prepared, seed=1234)
            del prepared
            for name in pending:
                t0 = time.perf_counter()
                event = meta['events'][name]
                root = make_event_root(model, prefill, event)
                arms = {}
                validation = args.phase == 'validation'
                def run(arm, **kwargs):
                    arms[arm] = score_event_arm(model, root, meta, event, validate=validation, **kwargs)
                run('N', telemetry=(condition == 'OO' and args.phase != 'semantic'))
                checks = {}
                if condition == 'OO' and args.phase in ('validation', 'primary'):
                    for window in (2, 8):
                        for roi in ('A', 'B'):
                            run(f'{roi}_W{window}', roi=roi, window=window)
                    run('AB_W2', roi='AB')
                    if meta.get('irrelevant_controls_validated'):
                        run('I_W2', roi='I_'+event['fact'])
                if condition == 'OO' and args.phase in ('validation', 'trigger'):
                    run('R16', trigger=True)
                    run('R16_A_W2', trigger=True, roi='A')
                    run('R16_B_W2', trigger=True, roi='B')
                if condition == 'OO' and validation:
                    run('noop_AB_W8', roi='AB', window=8, gain=1.)
                    run('noop_R16_AB_W2', roi='AB', trigger=True, gain=1.)
                    run('unhooked', hooked=False)
                    run('replay_A_W2', roi='A')
                    checks = {'noop_AB_exact': score_equal(arms['N'], arms['noop_AB_W8']),
                              'noop_trigger_exact': score_equal(arms['N'], arms['noop_R16_AB_W2']),
                              'unhooked_exact': score_equal(arms['N'], arms['unhooked']),
                              'replay_exact': arms['A_W2'] == arms['replay_A_W2']}
                if args.phase in ('trigger', 'semantic') and condition == 'OO':
                    original = list((OUT/'raw'/primary_freeze['run_id']).glob(f'shard_*/{base}/OO/{name}.json'))
                    if len(original) != 1:
                        raise RuntimeError('Missing unique primary denominator')
                    old = read_json(original[0])
                    checks['primary_native_exact'] = score_equal(arms['N'], old['arms']['N'])
                    if not checks['primary_native_exact']:
                        raise RuntimeError('Same-path primary native denominator replay failed')
                result = {'base_problem_id': base, 'example_id': item['example_id'], 'event': name,
                          'condition': condition, 'phase': args.phase, 'run_id': args.run_id,
                          'cohort_split': item['split'], 'asset_metadata_sha256': item['asset_metadata_sha256'],
                          'event_history_sha256': event['history_before_ed_sha256'], 'arms': arms,
                          'validation_checks': checks, 'prefill_audit': prefill_audit,
                          'image_layout_exact': True, 'final_correct': item['final_correct'],
                          'local_fact_reference_correct': True, 'runtime_seconds': time.perf_counter()-t0,
                          'peak_gpu_allocated_bytes': torch.cuda.max_memory_allocated(),
                          'peak_gpu_reserved_bytes': torch.cuda.max_memory_reserved()}
                path = shard/base/condition/f'{name}.json'
                atomic_json(path, result)
                completed += 1
                print(f'rank={rank} phase={args.phase} base={base} image={condition} event={name} arms={len(arms)} seconds={result["runtime_seconds"]:.1f}', flush=True)
                del arms, root
            del prefill
            gc.collect(); torch.cuda.empty_cache()
    write_json(shard/'run_summary.json', {'phase': args.phase, 'run_id': args.run_id, 'rank': rank,
               'new_event_files': completed, 'runtime_seconds': time.perf_counter()-started, 'completed': True})
    print(f'rank={rank} COMPLETE {args.run_id} new={completed}', flush=True)


if __name__ == '__main__':
    main()
