"""Bounded native screening for a verified retained benchmark release.

Embedded and multiple-image inputs extend the canonical single-image path.
The Phantom runner and its running dependencies remain unchanged.
"""
import argparse
import gc
import os
import platform
import resource
import sys
import time
from contextlib import nullcontext
from pathlib import Path

from scripts.stage7a.common import ROOT, read_json, read_jsonl, sha, write_json, write_jsonl

OUT = ROOT / 'outputs/stage7a_bench_v2'


def validate_rows(rows):
    if not rows or len({r['event_id'] for r in rows}) != len(rows):
        raise ValueError('Empty manifest or duplicate event IDs')
    for row in rows:
        if Path(row['event_id']).name != row['event_id'] or row['event_id'] in {'.', '..'}:
            raise ValueError('Unsafe event ID')
        if not row.get('no_image') and not (row.get('image_path') or row.get('image_assets') or row.get('document_path')):
            raise ValueError('This runner requires frozen image/document inputs or no_image')
        if row.get('no_image') and (row.get('image_path') or row.get('image_assets') or row.get('document_path')):
            raise ValueError('No-image row must not supply an image')
        if not row['prompt'].strip():
            raise ValueError('Empty prompt')


def check_manifest(path, freeze, audit):
    rows = read_jsonl(path)
    validate_rows(rows)
    matches = [x for x in freeze['native_screen'].values() if x['sha256'] == sha(path)]
    if len(matches) != 1 or matches[0]['count'] != len(rows):
        raise ValueError('Native manifest is not uniquely frozen with its exact count')
    for benchmark in {r['benchmark'] for r in rows}:
        record = audit.get(benchmark, {})
        if record.get('count') != 64 or not (record.get('eligible_track_a') or record.get('eligible_track_b')):
            raise ValueError('Benchmark has no completed eligible structural audit: ' + benchmark)
    return rows


def main():
    import torch
    from scripts.stage7a.common import configure_fresh_processor
    from visual_reasoning.stage0.modeling import load_runtime, runtime_environment, generate_once
    from visual_reasoning.stage1.protocol import protocol_parameters, transformers_generation_kwargs
    from scripts.stage7a_bench.image_inputs_v2 import prepare_condition as prepare_image
    from scripts.stage7a_bench.document_inputs_v2 import prepare_document
    def prepare_condition(processor, row, device):
        return prepare_document(processor, row, device) if row.get('document_path') else prepare_image(processor, row, device)

    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--manifest', action='append', required=True)
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--selection', required=True)
    parser.add_argument('--execution-plan', required=True)
    parser.add_argument('--bounded-attention', action='store_true')
    args = parser.parse_args()
    import re
    from scripts.stage7a_bench.native_migration_v3 import validate_runtime_move
    from scripts.stage7a_bench.reduced_native_selection_v6 import select_retained_rows
    if not re.fullmatch(r'[a-z0-9_]+', args.run_id):
        raise ValueError('Unsafe run identity')
    config_path = OUT / 'config/runtime_node02_v3.json'
    config = read_json(config_path)
    original = config['original_runtime']
    original_path = ROOT / original['path']
    if sha(original_path) != original['sha256']:
        raise ValueError('Original runtime provenance changed')
    validate_runtime_move(read_json(original_path), config)
    allocation = config['runtime']
    assert os.environ.get('SLURM_JOB_ID') == allocation['slurm_allocation']
    assert platform.node().split('.')[0] == allocation['node']
    assert torch.cuda.device_count() == 1 and 'A6000' in torch.cuda.get_device_name(0)
    freeze = read_json(OUT / 'cohort/sample_freeze.json')
    audit = read_json(OUT / 'structural_audit/benchmark_structural_summary.json')
    paths = [ROOT / name for name in args.manifest]
    manifests = [check_manifest(path, freeze, audit) for path in paths]
    rows = [row for manifest in manifests for row in manifest]
    validate_rows(rows)
    selection_path = (ROOT / args.selection).resolve()
    if not selection_path.is_relative_to(OUT / 'config'):
        raise ValueError('Selection outside active config directory')
    rows = select_retained_rows(rows, read_json(selection_path), args.run_id)
    if {row['benchmark'] for row in rows} != {'mmlongbench_doc'}:
        raise ValueError('This repaired reference runner is only for the retained document screen')
    reference_certificate_path = OUT / 'audit/document_reference_diagnostic_v8/result.json'
    reference_certificate = read_json(reference_certificate_path)
    if (reference_certificate['status'] != 'PASS' or
            reference_certificate['full_shape_softmax_exact'] is not True or
            not all(x['exact'] for x in reference_certificate['comparisons'].values())):
        raise ValueError('Exact GPU reference/128-token document certificate required')
    for source, digest in reference_certificate['source_sha256'].items():
        if sha(ROOT / source) != digest:
            raise ValueError('Validated reference source changed')

    execution_plan_path = (ROOT / args.execution_plan).resolve()
    if not execution_plan_path.is_relative_to(OUT / 'config'):
        raise ValueError('Execution plan outside active config directory')
    execution = read_json(execution_plan_path)
    matching = [batch for batch in execution['batches'] if batch['run_id'] == args.run_id]
    if (execution['allocation'] != allocation or len(matching) != 1 or
            execution['selection'] != dict(path=str(selection_path.relative_to(ROOT)), sha256=sha(selection_path)) or
            matching[0]['selection'] != str(selection_path.relative_to(ROOT)) or
            matching[0]['manifest_hashes'] != {str(path.relative_to(ROOT)): sha(path) for path in paths} or
            matching[0]['expected_event_count'] != len(rows)):
        raise ValueError('Native child differs from its frozen registered execution batch')
    dest = OUT / 'native_screen/generations' / args.run_id
    if (dest / 'signature.json').exists() and not args.resume:
        raise RuntimeError('Existing run requires explicit resume')
    dependencies = ['scripts/stage7a_bench/native_images_v8.py', 'scripts/stage7a_bench/run_native_parallel_v8_tmux.sh',
        'scripts/stage7a_bench/native_migration_v3.py',
        'scripts/stage7a_bench/mathwild_gate_v5.py',
        'scripts/stage7a_bench/parallel_native_v8.py',
        'scripts/stage7a_bench/image_inputs_v2.py',
        'scripts/stage7a_bench/bounded_attention_v2.py',
        'scripts/stage7a_bench/bounded_attention_v3.py',
        'scripts/stage7a_bench/document_inputs_v2.py',
        'scripts/stage7a_bench/document_runtime_v2.py',
        'outputs/stage7a_bench_v2/config/document_input_rules.json',
        'outputs/stage7a_bench_v2/config/document_execution_memory_rules_v2.json',
        'outputs/stage7a_bench_v2/config/image_pairing_sample_rules.json',
        'scripts/stage7a/common.py', 'code/visual_reasoning/stage0/modeling.py',
        'code/visual_reasoning/stage1/protocol.py', 'code/visual_reasoning/stage6a/runtime.py',
        'outputs/stage7a/config/image_preprocessing.json',
        'outputs/stage7a_bench_v2/config/runtime.json',
        'outputs/stage7a_bench_v2/config/runtime_node02_v3.json',
        str(execution_plan_path.relative_to(ROOT)),
        'outputs/stage7a_bench_v2/config/native_screen_rules.json',
        'outputs/stage7a_bench_v2/config/paired_condition_rules.json']
    dependencies += [
        'scripts/stage7a_bench/reduced_native_selection_v6.py',
        'scripts/stage7a_bench/mathwild_gate_checkpoint_v6.py',
        'scripts/stage7a_bench/mathwild_gate_coverage_v5.py',
        'scripts/stage7a_bench/mathwild_semantic_ledger_v5.py',
        'scripts/stage7a_bench/mathwild_feasibility_v5.py',
        'scripts/stage7a_bench/completed_screen_v7.py',
        'scripts/stage7a_bench/reviewed_units_v5.py',
        'scripts/stage7a_bench/causal_provenance_v2.py',
        'scripts/stage7a_bench/native_yield_v2.py']
    dependencies.append(str(selection_path.relative_to(ROOT)))
    dependencies += ['scripts/stage7a_bench/document_reference_v8.py',
                     str(reference_certificate_path.relative_to(ROOT))]
    signature = dict(runtime_config=str(config_path.relative_to(ROOT)),
        selection=str(selection_path.relative_to(ROOT)),
        manifests={str(p.relative_to(ROOT)): sha(p) for p in paths},
        event_ids=[r['event_id'] for r in rows], slurm_job_id=allocation['slurm_allocation'],
        bounded_attention=args.bounded_attention, query_chunk_size=128 if args.bounded_attention else None,
        non_document_short_cache_free_prefill_untiled_limit=1024 if args.bounded_attention else None,
        dependencies={p: sha(ROOT / p) for p in dependencies})
    write_json(dest / 'signature.json', signature, freeze=True)
    for source in dependencies:
        target = dest / 'source_snapshot' / source
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = (ROOT / source).read_bytes()
        if target.exists():
            assert target.read_bytes() == payload
        else:
            target.write_bytes(payload)
    # Structural state can grow for other benchmarks; preserve this run's gate.
    if not (dest / 'structural_gate_snapshot.json').exists():
        write_json(dest / 'structural_gate_snapshot.json',
                   {name: audit[name] for name in {r['benchmark'] for r in rows}}, freeze=True)
    cap = config['locked_generation_protocol']['max_new_tokens']
    parameters = protocol_parameters('official', cap, config['locked_generation_protocol']['seed'])
    kwargs = transformers_generation_kwargs(parameters)
    processor, model = load_runtime(Path(config['model_checkpoint']), device='cuda:0')
    configure_fresh_processor(processor)
    from scripts.stage7a_bench.bounded_attention_v3 import bounded_native_attention
    from scripts.stage7a_bench.document_runtime_v2 import bounded_document_runtime
    def attention_context(row):
        if args.bounded_attention and row.get('document_path'):
            return bounded_document_runtime(prefill_chunk_size=2048, query_chunk_size=64)
        return bounded_native_attention() if args.bounded_attention else nullcontext()
    def compact_document_pixels(prepared, row):
        if row.get('document_path'):
            # Canonical get_image_features performs this exact cast before the
            # vision encoder. Move it before generation to bound retained input.
            prepared['pixel_values'] = prepared['pixel_values'].to(torch.bfloat16)
    assert next(model.parameters()).dtype == torch.bfloat16
    write_json(dest / 'environment.json', dict(
        **runtime_environment(Path(config['model_checkpoint']), model, cap),
        sys_prefix=sys.prefix, parameter_dtype=str(next(model.parameters()).dtype),
        slurm_job_id=allocation['slurm_allocation'], node=platform.node(), world_size=1,
        slurm_step_id=os.environ.get('SLURM_STEP_ID'),
        slurm_task_rank=os.environ.get('SLURM_PROCID'),
        gpu_uuid=str(torch.cuda.get_device_properties(0).uuid)))
    # Determinism and fresh input-state checks precede this run's scientific data.
    mechanics = []
    for manifest in manifests:
        row = manifest[0]
        if row.get('document_path'):
            if not args.bounded_attention:
                raise ValueError('Full documents require the validated bounded eager path')
            # Output-blind mechanics input: smallest full document in this
            # frozen cohort, without removing pages from the native task.
            row = min((r for r in manifest if r['preflight_status'] == 'ready'),
                      key=lambda r: r['shape_estimate']['visual_tokens'])
        prepared, meta = prepare_condition(processor, row, 'cuda:0')
        from scripts.stage7a_bench.document_reference_v8 import full_qk_reference_context
        with full_qk_reference_context():
            first = generate_once(model, processor, prepared, 128, None,
                generation_kwargs=kwargs, seed=parameters['seed'], collect_predictive_metrics=False)
        compact_document_pixels(prepared, row)
        with attention_context(row):
            second = generate_once(model, processor, prepared, 128, None,
                generation_kwargs=kwargs, seed=parameters['seed'], collect_predictive_metrics=False)
        check = dict(event_id=row['event_id'],
            repeat_token_ids_exact=first['generated_token_ids'] == second['generated_token_ids'],
            no_image_state=(not meta['visual_token_indices'] and meta['image_grid_thw'] is None)
                           if row.get('no_image') else None,
            generated_token_ids=first['generated_token_ids'], input=meta, scientific_use=False)
        check['comparison'] = 'canonical versus bounded eager' if args.bounded_attention else 'canonical repeat'
        if row.get('document_path'):
            check['comparison'] = 'full canonical QK/AV and FP32 processor pixels with exact contiguous-row FP32 softmax versus BF16 vision-input pixels/bounded full-document prefill'
            check['reference_certificate_sha256'] = sha(reference_certificate_path)
        mechanics.append(check)
        write_json(dest / 'mechanics.json', dict(checks=mechanics, cap=128))
        assert check['repeat_token_ids_exact'] and check['no_image_state'] is not False
        del prepared, first, second
    print('MECHANICS_PASSED', len(mechanics), flush=True)
    if read_json(OUT / 'cohort/sample_freeze.json').get('model_generation_started') is not True:
        raise ValueError('This continuation requires an already-started frozen screen')
    eos = model.generation_config.eos_token_id
    eos = [eos] if isinstance(eos, int) else eos
    results = []
    def progress(row):
        write_json(dest / 'progress.json', dict(completed=len(results), total=len(rows),
            generated=sum(not r.get('unavailable') for r in results),
            unavailable=sum(bool(r.get('unavailable')) for r in results),
            last_event=row['event_id'], updated_unix=time.time(),
            elapsed_generation_seconds=sum(r['elapsed_seconds'] for r in results)))
    for index, row in enumerate(rows):
        example = dest / 'examples' / row['event_id']
        if (example / 'result.json').exists():
            result = read_json(example / 'result.json')
            assert read_json(example / 'manifest_row.json') == row
            if not result.get('unavailable'):
                assert result['generation_sha256'] == sha(example / 'generation.json')
                assert result['tokens_sha256'] == sha(example / 'tokens.jsonl')
            results.append(result)
            continue
        start = time.perf_counter()
        if row.get('preflight_status', 'ready') != 'ready':
            write_json(example / 'manifest_row.json', row, freeze=True)
            result = dict(event_id=row['event_id'], base_id=row['base_id'], benchmark=row['benchmark'],
                condition=row['condition'], family_id=row['family_id'], complete=False,
                unavailable=True, unavailable_reason=row['preflight_status'],
                artifact_dir=str(example.relative_to(ROOT)), elapsed_seconds=0.0,
                generation_sha256=None, tokens_sha256=None, token_count=0, truncated=None,
                interpretation='Missing input or fixed context budget; not a model error or scientific zero')
            write_json(example / 'result.json', result, freeze=True)
            results.append(result)
            progress(row)
            print(f"{index + 1}/{len(rows)} {row['event_id']} unavailable={row['preflight_status']}", flush=True)
            continue
        if row.get('image_path'):
            assert sha(row['image_path']) == row['image_sha256']
        prepared, meta = prepare_condition(processor, row, 'cuda:0')
        compact_document_pixels(prepared, row)
        if row.get('document_path'):
            meta['execution_pixel_values_dtype'] = str(prepared['pixel_values'].dtype)
            meta['execution_prefill_chunk_size'] = 2048
            meta['execution_query_chunk_size'] = 64
            meta['execution_pixel_cast'] = 'Exact canonical vision-input cast moved before generation; image content and preprocessing unchanged'
        write_json(example / 'input.json', meta, freeze=True)
        write_json(example / 'manifest_row.json', row, freeze=True)
        with attention_context(row):
            generation = generate_once(model, processor, prepared, cap, None,
                generation_kwargs=kwargs, seed=parameters['seed'], collect_predictive_metrics=False)
        tokens = generation.pop('token_rows')
        generation.pop('attention_arrays', None)
        write_json(example / 'generation.json', generation)
        write_jsonl(example / 'tokens.jsonl', tokens)
        ids = generation['generated_token_ids']
        ended = bool(ids and ids[-1] in eos)
        result = dict(event_id=row['event_id'], base_id=row['base_id'], benchmark=row['benchmark'],
            condition=row['condition'], family_id=row['family_id'],
            complete=ended and '</think>' in generation['raw_decoded_response'],
            ended_with_eos=ended, truncated=len(ids) >= cap and not ended, token_count=len(ids),
            runtime=generation['runtime'], elapsed_seconds=time.perf_counter() - start,
            peak_host_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            artifact_dir=str(example.relative_to(ROOT)),
            generation_sha256=sha(example / 'generation.json'), tokens_sha256=sha(example / 'tokens.jsonl'))
        write_json(example / 'result.json', result)
        results.append(result)
        progress(row)
        print(f"{index + 1}/{len(rows)} {row['event_id']} tokens={len(ids)} eos={ended} seconds={result['elapsed_seconds']:.1f}", flush=True)
        del prepared, generation, tokens
        gc.collect()
        torch.cuda.empty_cache()
    write_json(dest / 'run_summary.json', dict(completed=True, results=results,
        generated=sum(not r.get('unavailable') for r in results),
        unavailable=sum(bool(r.get('unavailable')) for r in results)))


if __name__ == '__main__':
    main()
