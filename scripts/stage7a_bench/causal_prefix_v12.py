"""Prepare bounded native prefixes, then restore the unchanged causal assay.

The source-suppression path needs full eager weights for one query at a time.
Bounded native attention is therefore scoped to prefill and pre-W8 replay only.
"""
import torch
from transformers.models.qwen3_vl import modeling_qwen3_vl as qwen

from scripts.stage7a_bench.bounded_attention_v3 import bounded_native_attention
from scripts.stage7a_bench.document_runtime_v2 import bounded_document_runtime
from visual_reasoning.stage6b.text_interface import prefill_condition
from visual_reasoning.stage4a.runtime import event_coordinates
from visual_reasoning.stage3c9.streaming import advance_streaming_state

_EAGER = qwen.eager_attention_forward
_MASK = qwen.create_causal_mask


def require_canonical_assay_attention():
    if qwen.eager_attention_forward is not _EAGER or qwen.create_causal_mask is not _MASK:
        raise RuntimeError('Source suppression must use canonical eager attention outside bounded scopes')


@torch.inference_mode()
def make_benchmark_root(model, prepared, row, event):
    require_canonical_assay_attention()
    document = bool(row.get('document_path'))
    scope = bounded_document_runtime() if document else bounded_native_attention()
    with scope:
        prefill, audit = prefill_condition(model, prepared, row['no_image'])
        root = make_event_root(model, prefill, event)
        del prefill
    require_canonical_assay_attention()
    audit.update(prefix_backend='bounded_document' if document else 'bounded_native',
        replay_partition='Unchanged Stage4A event_coordinates;2048-token prefix chunks before W8',
        canonical_assay_attention_restored=True,
        scope='Prefix preparation only; no causal score or GPU mechanics certificate')
    return root, audit


@torch.inference_mode()
def make_event_root(model, prefill, event):
    """Consume the exclusively owned prefill instead of retaining a GPU clone."""
    coords = event_coordinates(event, prefill.prompt_length)
    root = prefill
    context = event['history_before_ed_token_ids']
    for left, right in coords['partition']:
        if right > coords['window_start']:
            break
        if root.generated_length != left:
            raise RuntimeError('Prefix left the canonical event partition')
        advance_streaming_state(model=model, state=root, token_ids=context[left:right], seed=1234,
                                chunk_size=2048, release_allocator_cache=True)
    return root
