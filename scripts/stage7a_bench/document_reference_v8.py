"""Reference-only eager attention with bounded FP32 softmax temporaries.

Keep full QK and AV matrix shapes, scaling, mask, dtype and full key support.
Only independent softmax rows are scheduled separately. This reference does
not change the bounded-document scientific path or select document pages.
"""
from contextlib import contextmanager

import torch
from transformers.models.qwen3_vl import modeling_qwen3_vl as qwen


def softmax_rows_(weights, rows=64):
    if torch.is_grad_enabled() or weights.ndim != 4 or type(rows) is not int or rows < 1:
        raise ValueError('Positive row bound and inference-only four-dimensional weights required')
    if not weights.is_contiguous():
        raise ValueError("Reference logits must retain contiguous canonical row order")
    flat = weights.view(-1, weights.shape[-1])
    block = rows * weights.shape[1]
    for start in range(0, flat.shape[0], block):
        part = flat[start:start + block]
        part.copy_(torch.nn.functional.softmax(part, dim=-1, dtype=torch.float32).to(weights.dtype))
    return weights


def full_qk_reference_attention(module, query, key, value, attention_mask, scaling,
                                dropout=0.0, **kwargs):
    if torch.is_grad_enabled() or module.training or dropout != 0.0:
        raise ValueError('Reference is inference-only without dropout')
    key_states = qwen.repeat_kv(key, module.num_key_value_groups)
    value_states = qwen.repeat_kv(value, module.num_key_value_groups)
    weights = torch.matmul(query, key_states.transpose(2, 3)) * scaling
    if attention_mask is not None:
        weights = weights + attention_mask
    weights = softmax_rows_(weights).to(query.dtype)
    output = torch.matmul(weights, value_states)
    return output.transpose(1, 2).contiguous(), weights


@contextmanager
def full_qk_reference_context():
    original = qwen.eager_attention_forward
    qwen.eager_attention_forward = full_qk_reference_attention
    try:
        yield
    finally:
        qwen.eager_attention_forward = original
