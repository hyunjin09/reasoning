"""Same eager attention algebra with bounded query rows for native inference.

Only unpadded, batch-one, contiguous causal text sequences are supported.
The mask is materialized per query tile, never as a full square. This module
does not change the vision backend or collect/approximate attention weights.
Installed reference: transformers.models.qwen3_vl.modeling_qwen3_vl.
"""
from contextlib import contextmanager
from dataclasses import dataclass

import torch


@dataclass(frozen=True)
class CausalShape:
    queries: int
    past: int


def causal_shape(*, config, inputs_embeds, attention_mask=None,
                 past_key_values=None, position_ids=None, **kwargs):
    if config.model_type != 'qwen3_vl_text' or inputs_embeds.shape[0] != 1:
        raise ValueError('Bounded native path requires Qwen3-VL batch one')
    if kwargs:
        raise ValueError('Unexpected causal mask arguments: ' + str(sorted(kwargs)))
    queries = inputs_embeds.shape[1]
    past = int(past_key_values.get_seq_length()) if past_key_values is not None else 0
    if attention_mask is not None:
        if attention_mask.ndim != 2 or tuple(attention_mask.shape) != (1, past + queries):
            raise ValueError('Only a complete 2D padding mask is supported')
        if not bool((attention_mask == 1).all()):
            raise ValueError('Padding or masked input is unsupported')
    expected = torch.arange(past, past + queries, device=inputs_embeds.device).unsqueeze(0)
    if position_ids is not None and not torch.equal(position_ids, expected):
        raise ValueError('Noncontiguous text positions are unsupported')
    return CausalShape(queries, past)


def bounded_eager(module, query, key, value, attention_mask, scaling,
                  dropout=0.0, *, query_chunk_size=128, **kwargs):
    from transformers.models.qwen3_vl.modeling_qwen3_vl import repeat_kv
    if module.training or dropout != 0.0:
        raise ValueError('Bounded native attention is inference-only')
    if kwargs.get('output_attentions'):
        raise ValueError('Full attention weights are unavailable on the bounded path')
    if query_chunk_size < 1 or query.shape[0] != 1:
        raise ValueError('Invalid query chunk or batch size')
    if not isinstance(attention_mask, CausalShape):
        raise ValueError('Expected validated lazy causal shape')
    shape = attention_mask
    if query.shape[-2] != shape.queries or key.shape[-2] != shape.past + shape.queries:
        raise ValueError('Cache/query lengths do not match causal mask')
    keys = repeat_kv(key, module.num_key_value_groups)
    values = repeat_kv(value, module.num_key_value_groups)
    output = torch.empty_like(query)
    key_positions = torch.arange(key.shape[-2], device=query.device)
    for start in range(0, shape.queries, query_chunk_size):
        end = min(start + query_chunk_size, shape.queries)
        q = query[:, :, start:end, :]
        weights = torch.matmul(q, keys.transpose(2, 3)) * scaling
        query_positions = torch.arange(shape.past + start, shape.past + end, device=query.device)
        allowed = key_positions[None, :] <= query_positions[:, None]
        # Match the reference additive finite-min mask, including its dtype.
        mask = torch.zeros_like(allowed, dtype=query.dtype).masked_fill_(~allowed, torch.finfo(query.dtype).min)
        weights = weights + mask[None, None, :, :]
        weights = torch.nn.functional.softmax(weights, dim=-1, dtype=torch.float32).to(query.dtype)
        output[:, :, start:end, :] = torch.matmul(weights, values)
        del weights, mask, allowed
    return output.transpose(1, 2).contiguous(), None


@contextmanager
def bounded_native_attention(query_chunk_size=128):
    """Process-local patch; never alter the running Phantom process/modules."""
    from transformers.models.qwen3_vl import modeling_qwen3_vl as module
    original_mask, original_eager = module.create_causal_mask, module.eager_attention_forward
    def attention(*args, **kwargs):
        return bounded_eager(*args, query_chunk_size=query_chunk_size, **kwargs)
    module.create_causal_mask = causal_shape
    module.eager_attention_forward = attention
    try:
        yield
    finally:
        module.create_causal_mask = original_mask
        module.eager_attention_forward = original_eager
