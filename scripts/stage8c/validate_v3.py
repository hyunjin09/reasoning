"""V1–V6 on scheduled GPUs. Fail closed before scientific generation."""
import argparse
import ast
import hashlib
import json
import os
import socket
import traceback
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import torch

from visual_reasoning.stage0.modeling import generate_once, load_runtime, runtime_environment, _reset_generation_state
from visual_reasoning.stage3b0.cache import clone_cache
from visual_reasoning.stage3b0.runtime import suffix_position_ids
from visual_reasoning.stage8b.v2_protocol import prepared_input, generation_parameters
from visual_reasoning.stage8b.passive import PassiveRecorder
from visual_reasoning.stage8b.block0 import episodes
from visual_reasoning.stage8c.gain import VisualGain
from scripts.stage8c.prepare import save, sha


def cache_equal(left, right):
    return all(torch.equal(a.keys, b.keys) and torch.equal(a.values, b.values)
               for a, b in zip(left.layers, right.layers))


@torch.inference_mode()
def validate_cache(model, prepared, metadata, detector):
    _reset_generation_state(model, seed=11)
    ctx = VisualGain(model, visual=metadata['visual_token_indices'],
        prompt_length=metadata['prompt_token_count'], detector=detector, gain=1.5,
        policy='schedule', schedule=[1], audit=True)
    with ctx:
        first = model(**prepared, use_cache=True, return_dict=True)
        cache = first.past_key_values
        prefix = clone_cache(cache)
        length = cache.get_seq_length()
        token = first.logits[:, -1].argmax(-1, keepdim=True)
        kwargs = dict(input_ids=token, past_key_values=cache,
                      attention_mask=torch.ones((1, length+1), dtype=torch.long, device=token.device),
                      cache_position=torch.tensor([length], device=token.device),
                      position_ids=suffix_position_ids(prompt_length=length,suffix_length=1,rope_deltas=model.model.rope_deltas,device=token.device),
                      use_cache=True, return_dict=True)
        committed = model(**kwargs)
        assert len(ctx.events) == 1 and ctx.events[0]['rerun']
        assert cache.get_seq_length() == length+1
        assert all(torch.equal(a.keys, b.keys[:, :, :length]) and torch.equal(a.values, b.values[:, :, :length])
                   for a, b in zip(prefix.layers, cache.layers)), 'Earlier prefix altered'
        ctx.mode = 'gain'
        reference = ctx.original_forward(**dict(kwargs, past_key_values=clone_cache(prefix)))
        assert torch.equal(committed.logits, reference.logits), 'Independent replay logits differ'
        assert cache_equal(committed.past_key_values, reference.past_key_values), 'Independent replay cache differs'
        ctx.mode = 'native'
        native = ctx.original_forward(**dict(kwargs, past_key_values=clone_cache(prefix)))
        changed = [i for i, (a,b) in enumerate(zip(native.past_key_values.layers, cache.layers))
                   if not torch.equal(a.keys, b.keys) or not torch.equal(a.values, b.values)]
        assert changed and min(changed) >= 20, 'Intervention did not propagate to later-layer cache'
        next_token = committed.logits[:, -1].argmax(-1, keepdim=True)
        continuation = dict(input_ids=next_token, attention_mask=torch.ones((1,length+2), dtype=torch.long, device=token.device),
            cache_position=torch.tensor([length+1], device=token.device),
            position_ids=suffix_position_ids(prompt_length=length+1,suffix_length=1,rope_deltas=model.model.rope_deltas,device=token.device), use_cache=True, return_dict=True)
        a = ctx.original_forward(**continuation, past_key_values=committed.past_key_values)
        b = ctx.original_forward(**continuation, past_key_values=reference.past_key_values)
        assert torch.equal(a.logits, b.logits) and cache_equal(a.past_key_values, b.past_key_values)
    return dict(pass_check=True, independent_replay_exact=True, continuation_exact=True,
                prefix_unchanged=True, changed_cache_layers=changed, decompositions=ctx.decompositions)


def validate_item(model, processor, row, detector, cap):
    # Empty answer is a required legacy-preprocessor field; it never enters text.
    safe = {k:row[k] for k in ('item_id','image','image_sha256','question','generation_query')}
    prepared, metadata = prepared_input(processor, dict(safe, answer=''))
    hashes = []
    def capture(_module, _args, out):
        hashes.append(hashlib.sha256(out[0,-1].float().cpu().numpy().tobytes()).hexdigest())
    handle = model.lm_head.register_forward_hook(capture)
    try:
        with PassiveRecorder(visual=metadata['visual_token_indices'], prompt_length=metadata['prompt_token_count'],
                             model=detector, reference_check=True) as passive:
            native = generate_once(model, processor, prepared, cap, None,
                       generation_kwargs=generation_parameters(), seed=1234, collect_predictive_metrics=False)
    finally:
        handle.remove()
    native_rng = torch.cuda.get_rng_state().clone()
    checks = {}
    decompositions = []
    for name, gain, policy, replay in [('V1',1.,'retrieval',True),('V2',2.,'never',False)]:
        with VisualGain(model, visual=metadata['visual_token_indices'], prompt_length=metadata['prompt_token_count'],
                        detector=detector, gain=gain, policy=policy, replay_noop=replay, audit=True) as observer:
            result = generate_once(model, processor, prepared, cap, None,
                       generation_kwargs=generation_parameters(), seed=1234, collect_predictive_metrics=False)
        assert result['generated_token_ids'] == native['generated_token_ids'], name+' token mismatch'
        assert observer.committed_logit_hashes == hashes, name+' raw-logit mismatch'
        assert torch.equal(native_rng, torch.cuda.get_rng_state()), name+' RNG consumed more than once'
        assert np.array_equal(observer.arrays()['features'], passive.arrays()['features'], equal_nan=True), 'Detector feature mismatch'
        assert np.array_equal(observer.arrays()['retrieval_score'], passive.arrays()['retrieval_score'], equal_nan=True)
        onsets = [r['start_token'] for r in episodes(observer.scores,4)]
        if name == 'V1':
            assert onsets == [e['token_index'] for e in observer.events], 'Online/offline onset disagreement'
        checks[name] = dict(pass_check=True, tokens=len(hashes), raw_logits_exact=True, tokens_exact=True,
            sampling_rng_exact=True, replays=sum(e['rerun'] for e in observer.events), runtime=result['runtime'])
        decompositions.extend(observer.decompositions)
    cache = validate_cache(model, prepared, metadata, detector)
    decompositions.extend(cache.pop('decompositions'))
    assert decompositions
    max_rel = max(x['relative_l2'] for x in decompositions)
    max_abs = max(x['max_abs'] for x in decompositions)
    assert max_rel <= .02 and max_abs <= .125, 'V3 decomposition outside frozen BF16 tolerance'
    checks['V3'] = dict(pass_check=True, rows=len(decompositions), max_relative_l2=max_rel,
                         max_abs=max_abs, max_fp32_relative_l2=max(x['fp32_relative_l2'] for x in decompositions))
    checks['V4'] = cache
    checks['V5'] = dict(pass_check=True, passive_features_and_scores_exact=True,
                       reference_per_head_rows=passive.reference_rows, gap4_onsets=onsets)
    source = ast.parse(Path('code/visual_reasoning/stage8c/gain.py').read_text())
    identifiers = {n.id for n in ast.walk(source) if isinstance(n, ast.Name)}
    identifiers.update(n.attr for n in ast.walk(source) if isinstance(n, ast.Attribute))
    assert not identifiers.intersection({'ground_truth','answer','roi','future_tokens','read_text','open','load','loads'})
    checks['V6'] = dict(pass_check=True, inference_fields=sorted(safe), tensor_fields=sorted(prepared),
                        metadata_answer_empty=True, module_sha256=sha('code/visual_reasoning/stage8c/gain.py'),
                        assertion='Online interface has model, image-token positions, prompt length, frozen detector and dose/timing only; module has no data/file loading or oracle fields')
    return dict(item_id=row['item_id'], checks=checks, native_runtime=native['runtime'],
                raw_native_logit_sha256=hashes, native_token_ids=native['generated_token_ids'], pass_checks=True)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--config',required=True);args=ap.parse_args()
    cfg=json.loads(Path(args.config).read_text());rank=int(os.environ['SLURM_PROCID'])
    assert os.environ['SLURM_NTASKS']=='2' and socket.gethostname().split('.')[0]=='node02'
    assert torch.cuda.device_count()==1
    torch.cuda.set_device(0)
    dest=Path(cfg['output_dir'])/'technical_v3'/f'worker{rank}'
    for path, expected in cfg['source_sha256'].items():assert sha(path)==expected,path
    freeze=json.loads(Path(cfg['detector_freeze']).read_text());assert sha(cfg['detector_freeze'])==cfg['detector_freeze_sha256']
    assert sha(freeze['retrieval']['models'])==freeze['retrieval']['models_sha256']
    detector=joblib.load(freeze['retrieval']['models'])['joint']['model']
    processor,model=load_runtime(Path(cfg['model_checkpoint']),'cuda:0')
    env=runtime_environment(Path(cfg['model_checkpoint']),model,cfg['max_new_tokens'])
    env.update(slurm_job_id=os.environ['SLURM_JOB_ID'],hostname=socket.gethostname(),rank=rank,config_sha256=sha(args.config))
    save(dest/'environment.json',env)
    results=[]
    try:
        for row in cfg['technical_items'][rank::2]:
            print(json.dumps(dict(event='validation_start',rank=rank,item_id=row['item_id'])),flush=True)
            result=validate_item(model,processor,row,detector,cfg['technical_tokens'])
            save(dest/f'{row["item_id"]}.json',result);results.append(result)
            print(json.dumps(dict(event='validation_pass',rank=rank,item_id=row['item_id'])),flush=True)
        assert sum(r['checks']['V1']['replays'] for r in results)>0, 'Worker lacks triggered no-op coverage'
        save(dest/'result.json',dict(pass_checks=True,results=results,at=datetime.now(timezone.utc).isoformat()))
    except Exception:
        save(dest/'failure.json',dict(pass_checks=False,traceback=traceback.format_exc(),at=datetime.now(timezone.utc).isoformat()))
        raise


if __name__=='__main__':main()
