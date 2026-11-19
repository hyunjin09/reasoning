"""One fixed full-document reference-memory/parity check, never native data."""
import gc
import os
from pathlib import Path
import platform
import sys

from scripts.stage7a.common import ROOT, read_json, read_jsonl, sha, write_json

OUT = ROOT / 'outputs/stage7a_bench_v2'
DEST = OUT / 'audit/document_reference_diagnostic_v8'
JOB = 'stage7a_bench_document_reference_diagnostic_v8'


def diagnostic():
    import torch
    from transformers import AutoProcessor
    from scripts.stage7a.common import configure_fresh_processor
    from scripts.stage7a_bench.document_inputs_v2 import prepare_document
    from scripts.stage7a_bench.document_reference_v8 import softmax_rows_, full_qk_reference_context
    from scripts.stage7a_bench.document_runtime_v2 import bounded_document_runtime
    from visual_reasoning.stage0.modeling import load_runtime, generate_once, runtime_environment
    from visual_reasoning.stage1.protocol import protocol_parameters, transformers_generation_kwargs

    assert os.environ['SLURM_JOB_ID'] == '113280' and platform.node().split('.')[0] == 'node02'
    assert torch.cuda.device_count() == 1 and 'A6000' in torch.cuda.get_device_name(0)
    manifest = OUT / 'cohort/benchmark_manifests/mmlongbench_doc_image_present_native.jsonl'
    assert sha(manifest) == '2422839cbc306ae68e05cee6f689ce56f131aa459a571e769c7a233632d623ce'
    row = min((r for r in read_jsonl(manifest) if r['preflight_status'] == 'ready'),
              key=lambda r: r['shape_estimate']['visual_tokens'])
    assert row['page_count'] == 9 and row['shape_estimate']['visual_tokens'] == 11160
    config = read_json(OUT / 'config/runtime_node02_v3.json')
    processor = AutoProcessor.from_pretrained(config['model_checkpoint'], local_files_only=True)
    configure_fresh_processor(processor)
    prepared, meta = prepare_document(processor, row, 'cuda:0')
    write_json(DEST / 'input.json', meta, freeze=True)
    length = prepared['input_ids'].shape[1]
    # Fixed small tensor distinguishes row packing before the large gate.
    from scripts.stage7a_bench.document_reference_v7 import softmax_rows_ as previous_rows
    torch.manual_seed(1234)
    with torch.inference_mode():
        small = torch.randn(1, 8, 133, length, device='cuda:0', dtype=torch.bfloat16)
        target = torch.nn.functional.softmax(small, dim=-1, dtype=torch.float32).to(small.dtype)
        previous = previous_rows(small.clone())
        repaired = softmax_rows_(small.clone())
        layout_check = dict(shape=list(small.shape), previous_exact=torch.equal(target, previous),
            repaired_exact=torch.equal(target, repaired),
            previous_differences=int((target != previous).sum()),
            repaired_differences=int((target != repaired).sum()), scientific_use=False)
        write_json(DEST / 'layout_check.json', layout_check, freeze=True)
        print('LAYOUT_CHECK', layout_check, flush=True)
        assert layout_check['repaired_exact']
        del small, target, previous, repaired
    gc.collect()
    torch.cuda.empty_cache()
    # The original full-shape softmax fits when model weights are not resident.
    # Validate its exact output before using the reduced-temporary reference.
    torch.manual_seed(1234)
    with torch.inference_mode():
        logits = torch.randn(1, 32, length, length, device='cuda:0', dtype=torch.bfloat16)
        expected = torch.nn.functional.softmax(logits, dim=-1, dtype=torch.float32).to(logits.dtype)
        actual = softmax_rows_(logits)
        exact = torch.equal(expected, actual)
        write_json(DEST / 'full_shape_softmax.json', dict(exact=exact,
            shape=list(logits.shape), dtype=str(logits.dtype), softmax_dtype='torch.float32',
            peak_allocated_bytes=torch.cuda.max_memory_allocated(), scientific_use=False), freeze=True)
        assert exact
        del logits, expected, actual
    gc.collect()
    torch.cuda.empty_cache()
    print('FULL_SHAPE_SOFTMAX_EXACT', length, flush=True)
    processor, model = load_runtime(Path(config['model_checkpoint']), device='cuda:0')
    configure_fresh_processor(processor)
    write_json(DEST / 'environment.json', dict(
        **runtime_environment(Path(config['model_checkpoint']), model, 128),
        sys_prefix=sys.prefix, slurm_job_id='113280', slurm_step_id=os.environ.get('SLURM_STEP_ID'),
        parameter_dtype=str(next(model.parameters()).dtype),
        gpu_uuid=str(torch.cuda.get_device_properties(0).uuid), scientific_use=False), freeze=True)
    parameters = protocol_parameters('official', 128, config['locked_generation_protocol']['seed'])
    kwargs = transformers_generation_kwargs(parameters)
    outputs = {}
    for name in ('reference_1', 'reference_2', 'bounded'):
        if name == 'bounded':
            prepared['pixel_values'] = prepared['pixel_values'].to(torch.bfloat16)
            context = bounded_document_runtime(prefill_chunk_size=2048, query_chunk_size=64)
        else:
            context = full_qk_reference_context()
        with context:
            value = generate_once(model, processor, prepared, 128, None,
                generation_kwargs=kwargs, seed=parameters['seed'], collect_predictive_metrics=False)
        value.pop('attention_arrays', None)
        value.pop('token_rows', None)
        value['scientific_use'] = False
        write_json(DEST / (name + '.json'), value, freeze=True)
        outputs[name] = value['generated_token_ids']
        print('DIAGNOSTIC_CALL_COMPLETE', name, len(outputs[name]), flush=True)
    compare = lambda ids: dict(exact=ids == outputs['reference_1'],
        first_divergence=next((i for i, (a, b) in enumerate(zip(outputs['reference_1'], ids)) if a != b), None),
        lengths=[len(outputs['reference_1']), len(ids)])
    comparisons = {name: compare(ids) for name, ids in outputs.items() if name != 'reference_1'}
    passed = all(v['exact'] for v in comparisons.values())
    write_json(DEST / 'result.json', dict(status='PASS' if passed else 'PARITY_FAILED',
        event_id=row['event_id'], cap=128, page_count=9, visual_tokens=11160,
        full_shape_softmax_exact=exact, comparisons=comparisons, layout_check=layout_check,
        reference='Full canonical QK/AV GEMM shapes and FP32 processor pixels; independent FP32 softmax rows streamed in place',
        scientific_use=False, scientific_runtime_changed=False,
        full_shape_softmax_artifact=dict(path=str((DEST/'full_shape_softmax.json').relative_to(ROOT)),
            sha256=sha(DEST/'full_shape_softmax.json')),
        output_artifacts={name: dict(path=str((DEST/(name+'.json')).relative_to(ROOT)),
            sha256=sha(DEST/(name+'.json'))) for name in outputs},
        source_sha256={str(p.relative_to(ROOT)):sha(p) for p in (
            Path(__file__), ROOT/'scripts/stage7a_bench/document_reference_v8.py',
            ROOT/'scripts/stage7a_bench/document_runtime_v2.py', manifest)}), freeze=True)
    print('DIAGNOSTIC_RESULT', passed, comparisons, flush=True)
    assert passed, 'Full-document token parity is required before science'


def main():
    sys.path.insert(0, str(ROOT / 'infra'))
    from harness_state import mutate_gpu_queue, now_iso
    assert os.environ['SLURM_JOB_ID'] == '113280' and not DEST.exists()
    def start(queue):
        job = next(j for j in queue['jobs'] if j['id'] == JOB)
        assert job['status'] == 'queued'
        job.update(status='running', launcher='existing_slurm_diagnostic_step',
            slurm_job_id='113280', slurm_step_id=os.environ.get('SLURM_STEP_ID'), started_at=now_iso())
    mutate_gpu_queue(ROOT, start)
    code = 1
    try:
        diagnostic()
        code = 0
    finally:
        record = dict(exit_code=code, completed=code == 0, finished_at=now_iso(),
            slurm_job_id='113280', slurm_step_id=os.environ.get('SLURM_STEP_ID'), scientific_use=False)
        write_json(DEST / 'wrapper.json', record, freeze=True)
        def finish(queue):
            job = next(j for j in queue['jobs'] if j['id'] == JOB)
            assert job['status'] == 'running'
            job.update(status='succeeded' if code == 0 else 'failed', **record)
        mutate_gpu_queue(ROOT, finish)


if __name__ == '__main__':
    main()
