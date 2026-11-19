from types import SimpleNamespace

import pytest
import torch
from transformers.models.qwen3_vl.modeling_qwen3_vl import eager_attention_forward
from scripts.stage7a_bench.bounded_attention_v2 import CausalShape, bounded_eager, causal_shape


@pytest.mark.parametrize('queries,past,chunk', [(17, 0, 3), (5, 13, 2), (1, 18, 4)])
@pytest.mark.parametrize('dtype', [torch.float32, torch.bfloat16])
def test_prefill_cached_continuation_and_decode_match_reference(queries, past, chunk, dtype):
    torch.manual_seed(714)
    q = torch.randn(1, 8, queries, 16, dtype=dtype)
    k = torch.randn(1, 2, queries + past, 16, dtype=dtype)
    v = torch.randn_like(k)
    module = SimpleNamespace(num_key_value_groups=4, training=False)
    allowed = torch.arange(queries + past)[None, :] <= torch.arange(past, past + queries)[:, None]
    mask = torch.zeros_like(allowed, dtype=dtype).masked_fill(~allowed, torch.finfo(dtype).min)[None, None]
    expected, _ = eager_attention_forward(module, q, k, v, mask, .25)
    actual, weights = bounded_eager(module, q, k, v, CausalShape(queries, past), .25, query_chunk_size=chunk)
    # CPU FP32 GEMM changes accumulation order with the query dimension.
    # BF16 (the scientific dtype) must remain exact in this kernel check.
    torch.testing.assert_close(actual, expected, rtol=0, atol=0 if dtype == torch.bfloat16 else 1e-6)
    assert weights is None


def test_rejects_padding_and_noncontiguous_positions():
    args = dict(config=SimpleNamespace(model_type='qwen3_vl_text'), inputs_embeds=torch.zeros(1, 3, 4))
    assert causal_shape(**args, attention_mask=torch.ones(1, 3), position_ids=torch.arange(3)[None]) == CausalShape(3, 0)
    with pytest.raises(ValueError, match='Padding'):
        causal_shape(**args, attention_mask=torch.tensor([[1, 0, 1]]))
    with pytest.raises(ValueError, match='Noncontiguous'):
        causal_shape(**args, position_ids=torch.tensor([[0, 2, 3]]))
