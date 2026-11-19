"""One fixed-item runtime diagnostic; outputs are never native research data."""
from contextlib import nullcontext
import os
from pathlib import Path
import platform
import sys

from scripts.stage7a.common import ROOT, read_json, read_jsonl, sha, write_json

OUT = ROOT / 'outputs/stage7a_bench_v2'
JOB = 'stage7a_bench_mmmu_attention_parity_diagnostic_v1'
DEST = OUT / 'audit/mmmu_attention_parity_diagnostic_v1'


def compare(left, right):
    a, b = left['generated_token_ids'], right['generated_token_ids']
    first = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), None)
    if first is None and len(a) != len(b):
        first = min(len(a), len(b))
    return dict(exact=a == b, first_divergent_token=first,
                lengths=[len(a), len(b)])


def diagnostic():
    import torch
    from scripts.stage7a.common import configure_fresh_processor
    from scripts.stage7a_bench.image_inputs_v2 import prepare_condition
    from scripts.stage7a_bench.bounded_attention_v2 import bounded_native_attention
    from visual_reasoning.stage0.modeling import load_runtime, generate_once, runtime_environment
    from visual_reasoning.stage1.protocol import protocol_parameters, transformers_generation_kwargs

    assert os.environ.get('SLURM_JOB_ID') == '113280'
    assert platform.node().split('.')[0] == 'node02'
    assert torch.cuda.device_count() == 1 and 'A6000' in torch.cuda.get_device_name(0)
    config_path = OUT / 'config/runtime_node02_v3.json'
    config = read_json(config_path)
    manifest = OUT / 'cohort/benchmark_manifests/mmmu_pro_image_present_native.jsonl'
    assert sha(manifest) == 'e611262b18fc792b2b53e2b555fe4445d6c9885030e2c4406faedb62ebeaf208'
    row = read_jsonl(manifest)[0]
    prior_path = OUT / 'native_screen/generations/mmmu_pro_image_present_00_v6/mechanics.json'
    prior = read_json(prior_path)['checks'][0]
    assert prior['event_id'] == row['event_id'] and prior['repeat_token_ids_exact'] is False
    processor, model = load_runtime(Path(config['model_checkpoint']), device='cuda:0')
    configure_fresh_processor(processor)
    assert next(model.parameters()).dtype == torch.bfloat16
    prepared, meta = prepare_condition(processor, row, 'cuda:0')
    assert meta == prior['input']
    parameters = protocol_parameters('official', 128, config['locked_generation_protocol']['seed'])
    kwargs = transformers_generation_kwargs(parameters)
    write_json(DEST / 'input.json', meta, freeze=True)
    write_json(DEST / 'environment.json', dict(
        **runtime_environment(Path(config['model_checkpoint']), model, 128),
        slurm_job_id=os.environ['SLURM_JOB_ID'], slurm_step_id=os.environ.get('SLURM_STEP_ID'),
        gpu_uuid=str(torch.cuda.get_device_properties(0).uuid),
        node=platform.node(), scientific_use=False), freeze=True)
    outputs = {}
    prompt_length = int(prepared['input_ids'].shape[1])
    fixed_calls = [('canonical_1', None), ('canonical_2', None),
                   ('bounded128_1', 128), ('bounded128_2', 128),
                   ('untiled_prefill', prompt_length)]
    for name, chunk in fixed_calls:
        context = nullcontext() if chunk is None else bounded_native_attention(query_chunk_size=chunk)
        with context:
            result = generate_once(model, processor, prepared, 128, None,
                generation_kwargs=kwargs, seed=parameters['seed'], collect_predictive_metrics=False)
        result.pop('attention_arrays', None)
        result.pop('token_rows', None)
        result.update(scientific_use=False, diagnostic_call=name, query_chunk_size=chunk)
        write_json(DEST / (name + '.json'), result, freeze=True)
        outputs[name] = result
        print('DIAGNOSTIC_CALL_COMPLETE', name, len(result['generated_token_ids']), flush=True)
    comparisons = {name: compare(outputs['canonical_1'], outputs[name]) for name, _ in fixed_calls[1:]}
    comparisons['bounded_repeat'] = compare(outputs['bounded128_1'], outputs['bounded128_2'])
    comparisons['historical_canonical'] = compare(outputs['canonical_1'], prior)
    dependencies = [Path(__file__), config_path, manifest, prior_path,
        ROOT / 'scripts/stage7a_bench/bounded_attention_v2.py',
        ROOT / 'scripts/stage7a_bench/image_inputs_v2.py',
        ROOT / 'code/visual_reasoning/stage0/modeling.py']
    write_json(DEST / 'result.json', dict(status='FIXED_PREFLIGHT_DIAGNOSTIC_COMPLETE',
        event_id=row['event_id'], prompt_length=prompt_length, cap=128,
        comparisons=comparisons, generation_parameters=kwargs,
        scientific_use=False, scientific_thresholds_changed=False,
        source_sha256={str(p.relative_to(ROOT)): sha(p) for p in dependencies},
        generated_outputs={name: dict(path=str((DEST / (name+'.json')).relative_to(ROOT)),
            sha256=sha(DEST / (name+'.json'))) for name, _ in fixed_calls}), freeze=True)
    print('DIAGNOSTIC_COMPLETE', comparisons, flush=True)


def main():
    sys.path.insert(0, str(ROOT / 'infra'))
    from harness_state import mutate_gpu_queue, now_iso
    assert os.environ.get('SLURM_JOB_ID') == '113280'
    if DEST.exists():
        raise FileExistsError('Preserve the original diagnostic')
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
            assert job['status'] == 'running' and job['slurm_job_id'] == '113280'
            job.update(status='succeeded' if code == 0 else 'failed', **record)
        mutate_gpu_queue(ROOT, finish)


if __name__ == '__main__':
    main()
