"""Block3A native-only replay; unchanged Block2 capture, node02 Slurm workers."""
import argparse
import gc
import json
import os
import socket
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch

from visual_reasoning.stage0.modeling import load_runtime, runtime_environment
from visual_reasoning.stage3c9.streaming import advance_streaming_state, clone_streaming_state, prefill_streaming_state
from visual_reasoning.stage8b.block1_data import digest, save
from visual_reasoning.stage8b.block2_capture import SourceObserver
from visual_reasoning.stage8b.v2_protocol import prepared_input


@torch.inference_mode()
def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--manifest', default='outputs/stage8b_block3a/v1/audit/native_replay_manifest.json')
    args = parser.parse_args(); path = Path(args.manifest); frozen = json.loads(path.read_text())
    assert os.environ.get('SLURM_JOB_ID') and socket.gethostname().split('.')[0] == 'node02'
    assert int(os.environ['SLURM_NTASKS']) == 2 and torch.cuda.device_count() == 1
    rank = int(os.environ['SLURM_PROCID']); assert rank in [0, 1]
    torch.cuda.set_device(0)
    assert digest(frozen['annotation_seal_path']) == frozen['annotation_seal_sha256']
    for source, expected in frozen['source_sha256'].items():
        assert digest(source) == expected, source
    destination = Path(frozen['destination'])/f'worker{rank}'
    assert not destination.exists(), 'Use an explicit immutable continuation for any repair'
    processor, model = load_runtime(Path(frozen['model_checkpoint']), device='cuda:0')
    environment = runtime_environment(Path(frozen['model_checkpoint']), model, 40960)
    assert str(next(model.parameters()).dtype) == 'torch.bfloat16'
    assert (environment['language_layers'], environment['attention_heads'], environment['kv_heads']) == (28, 16, 8)
    environment.update(rank=rank, slurm_job_id=os.environ['SLURM_JOB_ID'], slurm_step_id=os.environ.get('SLURM_STEP_ID'),
                       node=socket.gethostname(), gpu_uuid=str(torch.cuda.get_device_properties(0).uuid),
                       manifest_sha256=digest(path), native_sampling=False)
    save(destination/'environment.json', environment)
    grouped = defaultdict(list)
    for request in frozen['requests']:
        if request['rank'] == rank:
            grouped[request['item_id']].append(request)
    completed = []
    for item, requests in grouped.items():
        assert len({r['query'] for r in requests}) == len(requests), 'Duplicate query requires grouped capture'
        start = time.monotonic(); torch.cuda.reset_peak_memory_stats()
        native = Path(requests[0]['native_dir'])
        for source, expected in requests[0]['native_sha256'].items():
            assert digest(source) == expected, source
        tokens = json.loads((native/'generation.json').read_text())['generated_token_ids']
        prepared, metadata = prepared_input(processor, requests[0]['row'])
        native_metadata = json.loads((native/'input.json').read_text())
        for key in ['prompt_ids_sha256', 'pixel_values_sha256', 'visual_token_indices', 'prompt_token_count', 'image_grid_thw', 'preprocessing']:
            assert metadata[key] == native_metadata[key], key
        state, prefill = prefill_streaming_state(model=model, prepared=prepared, seed=frozen['seed'])
        del prepared
        native_features = np.load(native/'passive.npz')['features']
        print(json.dumps(dict(event='item_start', item_id=item, rank=rank, max_query=max(r['query'] for r in requests))), flush=True)
        cursor = 0
        for request in sorted(requests, key=lambda r: (r['query'], r['event_id'])):
            query = request['query']; assert query >= cursor
            while cursor < query:
                end = min(query, cursor+256)
                advance_streaming_state(model=model, state=state, token_ids=tokens[cursor:end], seed=frozen['seed'], chunk_size=1)
                cursor = end
                if cursor % 1024 == 0:
                    print(json.dumps(dict(event='prefix_progress', item_id=item, rank=rank, cursor=cursor, seconds=time.monotonic()-start)), flush=True)
            reference = clone_streaming_state(state)
            advance_streaming_state(model=model, state=reference, token_ids=[tokens[query]], seed=frozen['seed'], chunk_size=1)
            observer = SourceObserver(model, metadata, request['source_positions'])
            with observer:
                advance_streaming_state(model=model, state=state, token_ids=[tokens[query]], seed=frozen['seed'], chunk_size=1)
            cursor = query+1
            result = observer.result()
            logits_equal = bool(torch.equal(state.last_logits, reference.last_logits))
            expected = native_features[request['claim_start']]
            observed = np.asarray(result['native_global_features'])
            feature_equal = bool(np.allclose(observed, expected, rtol=frozen['global_feature_parity']['rtol'], atol=frozen['global_feature_parity']['atol'], equal_nan=True))
            result.update(event_id=request['event_id'], item_id=item, family_id=request['family_id'], local=request['local'],
                          query=query, predicting_token=request['claim_start'], source_positions=request['source_positions'],
                          manifest_sha256=digest(path), capture_logits_exact=logits_equal, native_features_match=feature_equal,
                          native_features=expected.tolist(), feature_max_abs_delta=float(np.nanmax(np.abs(observed-expected))),
                          logits_max_abs_delta=float((state.last_logits.float()-reference.last_logits.float()).abs().max()),
                          elapsed_item_seconds=time.monotonic()-start, slurm_job_id=os.environ['SLURM_JOB_ID'])
            save(destination/'events'/f'{request["event_id"]}.json', result)
            assert logits_equal and feature_equal, 'Replay validity failure: preserve row and stop'
            completed.append(request['event_id'])
            print(json.dumps(dict(event='event_complete', event_id=request['event_id'], rank=rank, query=query,
                                  capture_logits_exact=logits_equal, feature_max_abs_delta=result['feature_max_abs_delta'],
                                  elapsed_item_seconds=result['elapsed_item_seconds'])), flush=True)
            del reference, observer, result
        save(destination/'items'/f'{item}.json', dict(item_id=item, completed=True, events=[r['event_id'] for r in requests],
             seconds=time.monotonic()-start, last_query=cursor-1, peak_allocated_bytes=torch.cuda.max_memory_allocated(),
             peak_reserved_bytes=torch.cuda.max_memory_reserved(), prefill=prefill))
        del state, native_features
        gc.collect(); torch.cuda.empty_cache()
    save(destination/'completed.json', dict(completed=True, rank=rank, events=completed, slurm_job_id=os.environ['SLURM_JOB_ID']))


if __name__ == '__main__':
    main()
