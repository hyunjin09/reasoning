"""Frozen solver-only recovery; full-cap cache reservation and per-call receipts."""
import argparse
import hashlib
import importlib.metadata
import os
import socket
import sys
import time
import traceback
from pathlib import Path

from scripts.stage14d1_pilot.common import P, load, now, rows, save, sha
from scripts.stage14d1_pilot.resume_v7 import admission_fits, completed_receipt


def run(manifest_path):
    assert os.environ.get('SLURM_JOB_ID')
    assert os.environ.get('VLLM_ENABLE_V1_MULTIPROCESSING') == '0'
    manifest = load(manifest_path)
    root = P / 'raw' / manifest['id']
    assert not root.exists(), 'New immutable attempt required'
    for path, digest in load(manifest['seal'])['files'].items():
        assert sha(path) == digest, path
    cfg = load(P / 'protocol/runtime_v6.json')
    originals = {r['item_id']: r for r in rows(P / 'inference/families.jsonl')}
    import torch
    from transformers import AutoProcessor
    from vllm import LLM, SamplingParams
    sys.path.insert(0, str(Path('outputs/qwen3vl_official_eval/v1/sources/qwen/evaluation/MathVision').resolve()))
    from run_mathv import prepare_inputs_for_vllm
    versions = {k: importlib.metadata.version(k) for k in cfg['environment']}
    assert versions == cfg['environment']
    assert torch.cuda.device_count() == 1
    node = socket.gethostname().split('.')[0]
    assert node in {'node02', 'node03', 'node06', 'node07'}
    job = os.environ['SLURM_JOB_ID']
    started = time.monotonic()
    processor = AutoProcessor.from_pretrained(cfg['model']['model']['checkpoint'])
    llm = LLM(model=cfg['model']['model']['checkpoint'], dtype='bfloat16',
              tensor_parallel_size=1, seed=42, gpu_memory_utilization=.85,
              max_model_len=128000, max_num_seqs=8, limit_mm_per_prompt={'image': 3},
              enable_prefix_caching=False, trust_remote_code=True, disable_log_stats=False)
    engine = llm.llm_engine
    block_size = engine.vllm_config.cache_config.block_size
    blocks = engine.vllm_config.cache_config.num_gpu_blocks
    capacity = blocks * block_size - 4096
    assert capacity > 128000
    save(root / 'environment.json', dict(at=now(), job=job, node=node,
        gpu=torch.cuda.get_device_name(0), versions=versions,
        engine_config=str(engine.vllm_config), manifest=manifest,
        runtime_sha256=sha(P / 'protocol/runtime_v6.json'), ready_seconds=time.monotonic()-started,
        block_size=block_size, num_gpu_blocks=blocks, usable_token_capacity=capacity,
        admission='full output cap + conservative prompt bound; block rounded'))
    completed = 0

    def calls(tasks):
        nonlocal completed
        active, answers = {}, {}
        cursor, pending = 0, None
        last_heartbeat = 0
        while cursor < len(tasks) or active:
            while cursor < len(tasks):
                t = tasks[cursor]
                row = originals[t['item_id']]
                rid = t['id']
                if pending is None:
                    prep_start = time.monotonic()
                    assert sha(row['image']) == row['image_sha256']
                    assert hashlib.sha256(row['prefix'].encode()).hexdigest() == row['prefix_sha256']
                    inp = prepare_inputs_for_vllm(row['original_messages'], processor)
                    assert inp['prompt'] == row['original_chat_prompt']
                    inp['prompt'] += row['prefix'] + t['suffix']
                    images = inp.get('multi_modal_data', {}).get('image', [])
                    pixels = [hashlib.sha256(im.tobytes()).hexdigest() for im in images]
                    sizes = [list(im.size) for im in images]
                    assert pixels == row['original_image_pixels'] and sizes == row['original_image_sizes']
                    # Text tokenizer counts each image placeholder once. Add the full
                    # Qwen3 16px-patch/2x-merge visual expansion, plus a margin.
                    prompt_bound = len(processor.tokenizer.encode(inp['prompt'])) + sum(w*h//1024 for w,h in sizes) + 256
                    reservation = ((prompt_bound + 81920 + block_size-1)//block_size)*block_size
                    if reservation > capacity:
                        raise RuntimeError('Single full-cap request exceeds measured cache capacity')
                    pending = inp, pixels, sizes, reservation, prompt_bound, time.monotonic()-prep_start
                inp, pixels, sizes, reserve, prompt_bound, prep_seconds = pending
                if not admission_fits([x['reserve'] for x in active.values()], reserve, capacity):
                    break
                folder = root / rid
                assert not folder.exists()
                save(folder / 'input.json', dict(at=now(), id=rid, family_id=row['family_id'],
                    item_id=row['item_id'], kind='solver', prompt=inp['prompt'], pixels=pixels,
                    sizes=sizes, preprocessing_seconds=prep_seconds, images=[row['image']],
                    prefix_sha256=row['prefix_sha256'], sampling=cfg['helper_recipe'], cap=t['cap'],
                    seed=row['seed'], job=job, schema=None, full_cap_token_reservation=reserve,
                    prompt_token_upper_bound=prompt_bound))
                params = SamplingParams(**cfg['helper_recipe'], max_tokens=t['cap'], seed=row['seed'],
                                        stop_token_ids=[], ignore_eos=False)
                engine.add_request(rid, inp, params)
                active[rid] = dict(task=t, reserve=reserve, prompt_bound=prompt_bound,
                                   started=time.monotonic(), latest=None)
                cursor += 1
                pending = None
            if not active:
                raise RuntimeError('No live requests while work remains')
            try:
                updates = engine.step()
            except BaseException as exc:
                for rid, data in active.items():
                    g = data['latest'].outputs[0] if data['latest'] else None
                    save(root/rid/'interrupted.json', dict(at=now(), reason='ENGINE_ERROR',
                        error=repr(exc), raw=g.text if g else '', tokens=list(g.token_ids) if g else []))
                raise
            for output in updates:
                rid = output.request_id
                data = active[rid]
                data['latest'] = output
                assert len(output.prompt_token_ids) <= data['prompt_bound']
                if not output.finished:
                    continue
                g = output.outputs[0]
                folder = root/rid
                record = dict(at=now(), id=rid, tokens=len(g.token_ids), generated_token_ids=list(g.token_ids),
                    raw_decoded_response=g.text, prompt_token_ids=list(output.prompt_token_ids),
                    prompt_tokens=len(output.prompt_token_ids), visual_tokens=sum(x==151655 for x in output.prompt_token_ids),
                    finish_reason=g.finish_reason, stop_reason=g.stop_reason, cap_hit=g.finish_reason=='length',
                    latency_seconds=time.monotonic()-data['started'], job=job, node=node,
                    seed=originals[data['task']['item_id']]['seed'])
                save(folder/'generation.json', record)
                save(folder/'result.json', dict(input_sha256=sha(folder/'input.json'), generation_sha256=sha(folder/'generation.json')))
                answers[rid] = str(folder/'generation.json')
                del active[rid]
                completed += 1
                print('COMPLETE', manifest['id'], rid, record['tokens'], record['finish_reason'], flush=True)
            if time.monotonic()-last_heartbeat > 60:
                save(root/'heartbeats'/f'{time.time_ns()}.json', dict(at=now(), completed=completed,
                    elapsed_seconds=time.monotonic()-started, remaining=len(tasks)-cursor,
                    active={rid:len(x['latest'].outputs[0].token_ids) if x['latest'] else 0 for rid,x in active.items()},
                    reserved_tokens=sum(x['reserve'] for x in active.values()), usable_token_capacity=capacity))
                last_heartbeat = time.monotonic()
        return answers

    try:
        # Fresh repeated same-prefix continuations under the repaired admission.
        technical_ids = manifest['technical_item_ids']
        checks = []
        outputs = []
        for repeat in ('a','b'):
            outputs.append(calls([dict(id=f'{item}_check_{repeat}', item_id=item, suffix='', cap=64) for item in technical_ids]))
        for item in technical_ids:
            a = load(outputs[0][f'{item}_check_a'])
            b = load(outputs[1][f'{item}_check_b'])
            old = load(P/'raw/technical_v6'/f'{item}_replay_a/generation.json')
            checks.append(dict(item_id=item, repeated_equal=a['generated_token_ids']==b['generated_token_ids'],
                reference_equal=a['generated_token_ids']==old['generated_token_ids'],
                prompt_ids_equal=a['prompt_token_ids']==old['prompt_token_ids']))
        passed = all(all(c[k] for k in ('repeated_equal','reference_equal','prompt_ids_equal')) for c in checks)
        save(root/'technical_gate.json', dict(at=now(), checks=checks, passed=passed))
        assert passed, 'Scheduling validation failed; scientific requests not admitted'
        answers = calls(manifest['requests'])
        for t in manifest['requests']:
            assert completed_receipt(Path(answers[t['id']]).parent, originals[t['item_id']], t['suffix'])
        save(root/'resolved_requests.json', dict(at=now(), paths=answers))
        save(root/'exit.json', dict(at=now(), status='COMPLETE', physical_main=len(answers),
            completed=completed, seconds=time.monotonic()-started, peak_gpu_bytes=torch.cuda.max_memory_allocated()))
    except BaseException as exc:
        save(root/'error.json', dict(at=now(), error=repr(exc), traceback=traceback.format_exc(),
            completed=completed, seconds=time.monotonic()-started))
        raise


if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('manifest');run(parser.parse_args().manifest)
