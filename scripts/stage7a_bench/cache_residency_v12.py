"""Exact inactive-cache CPU storage; only the current replay cache stays on GPU.

K/V transfers preserve dtype and layout. Logits, RoPE and compute metadata stay
on the compute device. No model operation, source intervention or score changes.
"""
import copy
import torch
from visual_reasoning.stage3b0.cache import _layer_tensors
from visual_reasoning.stage3c9.streaming import StreamingPrefixState


def offload_cache(state):
    _layer_tensors(state.cache)  # Validate before modifying any layer.
    had_cuda=False
    for layer in state.cache.layers:
        had_cuda |= layer.keys.device.type=='cuda'
        layer.keys=layer.keys.to('cpu')
        layer.values=layer.values.to('cpu')
    if had_cuda:
        torch.cuda.empty_cache()
    return state


def clone_streaming_state(state):
    """Leave the immutable source on CPU; clone directly to its compute device."""
    offload_cache(state)
    device=state.last_logits.device
    memo={id(t):t.to(device=device,copy=True) for pair in _layer_tensors(state.cache) for t in pair}
    cache=copy.deepcopy(state.cache,memo)
    return StreamingPrefixState(cache,state.rope_deltas.detach().clone(),
        int(state.prompt_length),int(state.generated_length),state.last_logits.detach().clone())


def cache_prefix_audit(before,after):
    n=before.prompt_length+before.generated_length
    if len(before.cache.layers)!=len(after.cache.layers):
        raise ValueError('Cache audit layer counts differ')
    rows=[]
    for i,(a,b) in enumerate(zip(before.cache.layers,after.cache.layers)):
        rows.append(dict(layer_index=i,
            past_key_exact=torch.equal(a.keys.cpu(),b.keys[:,:,:n].cpu()),
            past_value_exact=torch.equal(a.values.cpu(),b.values[:,:,:n].cpu())))
    return dict(past_length=n,layers=rows,passed=all(x['past_key_exact'] and x['past_value_exact'] for x in rows))
