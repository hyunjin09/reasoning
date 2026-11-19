"""Native text-only interface for a model whose forward leaves RoPE delta unset.

Qwen3-VL's installed TextModel uses arange(past_length, past_length+length)
when multimodal position IDs are absent. Generation also explicitly uses a zero
delta for text-only input. We encode that identity in the existing state type;
mechanics independently compares every cached K/V and logit to implicit positions.
"""
import time
import torch
from visual_reasoning.stage0.modeling import _reset_generation_state
from visual_reasoning.stage3c9.streaming import (StreamingPrefixState,prefill_streaming_state,
    clone_streaming_state,advance_streaming_state,fixed_chunk_ranges)


@torch.inference_mode()
def prefill_condition(model,prepared,no_image):
    if not no_image:
        return prefill_streaming_state(model=model,prepared=prepared,seed=1234)
    assert prepared['input_ids'].shape[0]==1
    assert not any(k in prepared for k in ('pixel_values','image_grid_thw','pixel_values_videos','video_grid_thw'))
    assert bool(prepared['attention_mask'].all())
    _reset_generation_state(model,seed=1234);started=time.perf_counter()
    output=model(**prepared,use_cache=True,return_dict=True,logits_to_keep=1)
    length=int(prepared['input_ids'].shape[1])
    assert output.past_key_values is not None and output.past_key_values.get_seq_length()==length
    if output.rope_deltas is not None:assert not bool(output.rope_deltas.any())
    delta=torch.zeros((1,1),dtype=torch.long,device=prepared['input_ids'].device)
    state=StreamingPrefixState(output.past_key_values,delta,length,0,output.logits[0,-1].detach().clone())
    return state,{'prompt_length':length,'cache_sequence_length':length,'rope_deltas':[[0]],
        'native_returned_rope_deltas':None if output.rope_deltas is None else output.rope_deltas.tolist(),
        'prefix_execution':'native_text_only_prefill; explicit identity offset for cached continuation',
        'runtime_seconds':time.perf_counter()-started,'visual_tokens':0}


@torch.inference_mode()
def validate_text_replay(model,prefill,event):
    ids=event['history_before_ed_token_ids'];end=len(ids);boundary=end-8
    ranges=fixed_chunk_ranges(start=0,end=boundary,chunk_size=2048) if boundary else []
    ranges += [(i,i+1) for i in range(boundary,end)]
    explicit=clone_streaming_state(prefill);implicit=clone_streaming_state(prefill)
    checks=[];device=explicit.last_logits.device
    for start,stop in ranges:
        advance_streaming_state(model=model,state=explicit,token_ids=ids[start:stop],seed=1234,
            chunk_size=stop-start,release_allocator_cache=True)
        model.model.rope_deltas=None
        output=model(input_ids=torch.tensor([ids[start:stop]],device=device),
            attention_mask=torch.ones((1,prefill.prompt_length+stop),dtype=torch.long,device=device),
            past_key_values=implicit.cache,use_cache=True,return_dict=True,logits_to_keep=1)
        implicit.cache=output.past_key_values;implicit.generated_length=stop
        implicit.last_logits=output.logits[0,-1].detach().clone()
        exact=torch.equal(explicit.last_logits,implicit.last_logits)
        caches=all(torch.equal(a.keys,b.keys) and torch.equal(a.values,b.values)
                   for a,b in zip(explicit.cache.layers,implicit.cache.layers))
        checks.append({'range':[start,stop],'logits_exact':exact,'all_layer_kv_exact':caches})
        del output;torch.cuda.empty_cache()
    assert all(c['logits_exact'] and c['all_layer_kv_exact'] for c in checks)
    return {'passed':True,'partition_checks':checks,'reference':'Native implicit text positions and fresh text-only cache; no image cache reuse'}
