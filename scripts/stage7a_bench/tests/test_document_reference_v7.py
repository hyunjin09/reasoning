from types import SimpleNamespace

import pytest
import torch
from transformers.models.qwen3_vl import modeling_qwen3_vl as qwen

from scripts.stage7a_bench.document_reference_v7 import (
    full_qk_reference_attention, full_qk_reference_context, softmax_rows_)


@pytest.mark.parametrize('queries,keys', [(1, 37), (19, 257), (130, 193), (2, 11197)])
def test_softmax_retains_exact_bf16_values_with_bounded_float_temporaries(queries, keys, monkeypatch):
    torch.manual_seed(31)
    weights = torch.randn(1, 8, queries, keys, dtype=torch.bfloat16)
    weights[..., -3:] = torch.finfo(weights.dtype).min
    expected = torch.nn.functional.softmax(weights, dim=-1, dtype=torch.float32).to(weights.dtype)
    original = torch.nn.functional.softmax
    observed = []
    def bounded_call(x, *args, **kwargs):
        observed.append(x.numel())
        return original(x, *args, **kwargs)
    monkeypatch.setattr(torch.nn.functional, 'softmax', bounded_call)
    with torch.inference_mode():
        actual = softmax_rows_(weights, rows=7)
    assert torch.equal(actual, expected)
    assert actual.data_ptr() == weights.data_ptr()
    assert max(observed) <= 8 * min(7, queries) * keys


@pytest.mark.parametrize('mask_dtype', [torch.bfloat16, torch.float32])
def test_full_qk_reference_preserves_masked_attention_and_scope(mask_dtype):
    torch.manual_seed(32)
    module = SimpleNamespace(num_key_value_groups=4, training=False)
    q = torch.randn(1, 8, 130, 16, dtype=torch.bfloat16)
    k = torch.randn(1, 2, 137, 16, dtype=torch.bfloat16)
    v = torch.randn_like(k)
    allowed = torch.arange(137)[None] <= torch.arange(7, 137)[:, None]
    mask = torch.zeros_like(allowed, dtype=mask_dtype).masked_fill(~allowed, torch.finfo(q.dtype).min)[None, None]
    original = qwen.eager_attention_forward
    with torch.inference_mode():
        expected = original(module, q, k, v, mask, .25)
        with full_qk_reference_context():
            actual = qwen.eager_attention_forward(module, q, k, v, mask, .25)
    assert qwen.eager_attention_forward is original
    for left, right in zip(actual, expected):
        assert torch.equal(left, right)
    with pytest.raises(ValueError, match='inference'):
        full_qk_reference_attention(module, q, k, v, mask, .25)
