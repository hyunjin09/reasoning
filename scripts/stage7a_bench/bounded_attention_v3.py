"""Keep short prefills untiled; preserve the bounded path for long inputs.

The fixed MMMU mechanics diagnostic reproduces a sampled-token difference when
890 query rows are tiled by128, despite exact repeatability of both paths.
Untiled prefill restores the canonical128-token sequence. The fixed1024-row
limit bounds a cache-free BF16 QK matrix to64MiB at32 heads, before temporaries.
No mask, attention algebra, cache, generation setting or model weight changes.
Historical runs retain bounded_attention_v2 and their source snapshots.
"""
from contextlib import contextmanager

from scripts.stage7a_bench.bounded_attention_v2 import CausalShape, bounded_eager, causal_shape

UNTILED_PREFILL_LIMIT = 1024


def short_prefill_eager(module, query, key, value, attention_mask, scaling,
                        dropout=0.0, *, query_chunk_size=128, **kwargs):
    if query_chunk_size < 1:
        raise ValueError('Invalid query chunk')
    chunk = query_chunk_size
    if (isinstance(attention_mask, CausalShape) and attention_mask.past == 0 and
            0 < attention_mask.queries <= UNTILED_PREFILL_LIMIT):
        chunk = attention_mask.queries
    return bounded_eager(module, query, key, value, attention_mask, scaling,
        dropout, query_chunk_size=chunk, **kwargs)


@contextmanager
def bounded_native_attention(query_chunk_size=128):
    from transformers.models.qwen3_vl import modeling_qwen3_vl as module
    original_mask, original_eager = module.create_causal_mask, module.eager_attention_forward
    def attention(*args, **kwargs):
        return short_prefill_eager(*args, query_chunk_size=query_chunk_size, **kwargs)
    module.create_causal_mask = causal_shape
    module.eager_attention_forward = attention
    try:
        yield
    finally:
        module.create_causal_mask = original_mask
        module.eager_attention_forward = original_eager
