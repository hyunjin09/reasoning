from types import SimpleNamespace

import pytest
import torch
from transformers.models.qwen3_vl.modeling_qwen3_vl import eager_attention_forward

from scripts.stage7a_bench import bounded_attention_v3 as current
from scripts.stage7a_bench.bounded_attention_v2 import CausalShape


@pytest.mark.parametrize('dtype', [torch.float32, torch.bfloat16])
@pytest.mark.parametrize('queries,past', [(129, 0), (1, 2048), (1033, 0)])
def test_preserves_reference_causal_attention(dtype, queries, past):
    torch.manual_seed(7)
    module = SimpleNamespace(training=False, num_key_value_groups=2)
    q = torch.randn(1, 4, queries, 8, dtype=dtype)
    k = torch.randn(1, 2, queries+past, 8, dtype=dtype)
    v = torch.randn_like(k)
    allowed = torch.arange(queries+past)[None, :] <= torch.arange(past, past+queries)[:, None]
    mask = torch.zeros(queries, queries+past, dtype=dtype).masked_fill(~allowed, torch.finfo(dtype).min)
    expected, _ = eager_attention_forward(module, q, k, v, mask[None, None], .25)
    actual, weights = current.short_prefill_eager(module, q, k, v, CausalShape(queries, past), .25)
    assert weights is None
    if queries <= 1024:
        assert torch.equal(actual, expected)
    else:
        torch.testing.assert_close(actual, expected, atol=1e-6 if dtype == torch.float32 else .01, rtol=.01)


def test_only_small_cache_free_prefills_change_query_tiling(monkeypatch):
    calls = []
    def capture(*args, **kwargs):
        calls.append(kwargs['query_chunk_size'])
        return None
    monkeypatch.setattr(current, 'bounded_eager', capture)
    for shape in (CausalShape(890, 0), CausalShape(1024, 0), CausalShape(1025, 0), CausalShape(890, 900)):
        current.short_prefill_eager(None, None, None, None, shape, 1.0)
    assert calls == [890, 1024, 128, 128]


def test_process_patch_restored_on_error():
    from transformers.models.qwen3_vl import modeling_qwen3_vl as module
    before = module.create_causal_mask, module.eager_attention_forward
    with pytest.raises(RuntimeError):
        with current.bounded_native_attention():
            assert module.create_causal_mask is current.causal_shape
            raise RuntimeError('diagnostic exception')
    assert (module.create_causal_mask, module.eager_attention_forward) == before
