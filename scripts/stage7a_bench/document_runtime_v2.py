"""Bounded full-document execution, without page selection or decoding changes.

Preserve eager attention, all KV history and multimodal/deepstack positions.
Native token parity is required separately on the actual model/GPU.
"""
from contextlib import contextmanager

import torch

from scripts.stage7a_bench.bounded_attention_v2 import CausalShape, causal_shape


def grouped_eager(module, query, key, value, attention_mask, scaling, dropout=0.,
                  *, query_chunk_size=128, **kwargs):
    if module.training or dropout != 0.:
        raise ValueError('Document attention requires inference')
    if kwargs.get('output_attentions') or not isinstance(attention_mask, CausalShape):
        raise ValueError('Document attention requires a validated lazy mask and no weight collection')
    shape = attention_mask
    if (query.shape[0] != 1 or query.shape[-2] != shape.queries or
            key.shape[-2] != shape.past + shape.queries or query_chunk_size < 1):
        raise ValueError('Invalid document attention shape')
    groups = module.num_key_value_groups
    if query.shape[1] != key.shape[1] * groups:
        raise ValueError('Query/KV head mapping mismatch')
    output = torch.empty_like(query)
    key_positions = torch.arange(key.shape[-2], device=query.device)
    for start in range(0, shape.queries, query_chunk_size):
        end = min(start + query_chunk_size, shape.queries)
        query_positions = torch.arange(shape.past+start, shape.past+end, device=query.device)
        allowed = key_positions[None, :] <= query_positions[:, None]
        mask = torch.zeros_like(allowed, dtype=query.dtype).masked_fill_(~allowed, torch.finfo(query.dtype).min)
        # repeat_kv orders heads as kv0/group0..groupG, kv1/group0..groupG.
        # Strided query-head selection reuses each physical KV tensor directly.
        for group in range(groups):
            q = query[:, group::groups, start:end, :]
            weights = torch.matmul(q, key.transpose(2, 3)) * scaling
            weights = weights + mask[None, None]
            weights = torch.nn.functional.softmax(weights, dim=-1, dtype=torch.float32).to(query.dtype)
            output[:, group::groups, start:end, :] = torch.matmul(weights, value)
            del weights
    return output.transpose(1, 2).contiguous(), None


def chunked_text_forward(module, original, *, prefill_chunk_size=2048, **inputs):
    from transformers.modeling_outputs import BaseModelOutputWithPast
    x = inputs.get('inputs_embeds')
    if x is None or x.shape[1] <= prefill_chunk_size:
        return original(module, **inputs)
    if module.training or torch.is_grad_enabled() or x.shape[0] != 1:
        raise ValueError('Document prefill requires batch-one inference')
    if inputs.get('input_ids') is not None or inputs.get('use_cache') is not True:
        raise ValueError('Document prefill requires embedded inputs and a cache')
    if inputs.get('output_attentions') or inputs.get('output_hidden_states'):
        raise ValueError('Document prefill does not collect layer outputs')
    cache = inputs.get('past_key_values')
    if cache is not None and cache.get_seq_length() != 0:
        raise ValueError('Long document prefill must begin with a fresh cache')
    position = inputs.get('position_ids')
    mask = inputs.get('attention_mask')
    visual = inputs.get('visual_pos_masks')
    features = inputs.get('deepstack_visual_embeds')
    if position is None or position.shape[-1] != x.shape[1]:
        raise ValueError('Preserve full native multimodal positions before chunking')
    if mask is not None and (mask.ndim != 2 or not bool((mask == 1).all())):
        raise ValueError('Only unpadded documents are supported')
    if features is not None and (visual is None or any(f.shape[0] != int(visual.sum()) for f in features)):
        raise ValueError('Deepstack feature/visual-position mismatch')
    hidden = torch.empty_like(x)
    visual_start = 0
    for start in range(0, x.shape[1], prefill_chunk_size):
        end = min(start+prefill_chunk_size, x.shape[1])
        part = dict(inputs, inputs_embeds=x[:, start:end], position_ids=position[..., start:end],
                    past_key_values=cache, attention_mask=mask[:, :end] if mask is not None else None)
        if visual is not None:
            selected = visual[:, start:end]
            visual_end = visual_start + int(selected.sum())
            part['visual_pos_masks'] = selected
            part['deepstack_visual_embeds'] = ([f[visual_start:visual_end] for f in features]
                                                if features is not None else None)
            visual_start = visual_end
        result = original(module, **part)
        hidden[:, start:end] = result.last_hidden_state
        cache = result.past_key_values
        if cache.get_seq_length() != end:
            raise ValueError('Chunked prefill cache did not advance exactly')
        del result, part
    return BaseModelOutputWithPast(last_hidden_state=hidden, past_key_values=cache)


def compact_image_forward(module, original, **inputs):
    """Canonical image-only embedding/position path with shorter tensor lifetimes.

    The installed forward retains raw vision states and duplicate pooled image
    tensors until after language decoding. Neither is read after masked_scatter.
    Release them before the long language prefill, preserving all DeepStack data.
    """
    from transformers.models.qwen3_vl.modeling_qwen3_vl import Qwen3VLModelOutputWithPast
    if inputs.get('pixel_values') is None:
        return original(module, **inputs)
    if module.training or torch.is_grad_enabled():
        raise ValueError('Compact image path requires inference')
    if inputs.get('pixel_values_videos') is not None or inputs.get('video_grid_thw') is not None:
        raise ValueError('Document path supports image pages only')
    named = {'input_ids', 'inputs_embeds', 'attention_mask', 'position_ids', 'past_key_values',
             'pixel_values', 'pixel_values_videos', 'image_grid_thw', 'video_grid_thw', 'mm_token_type_ids'}
    kwargs = {k: v for k, v in inputs.items() if k not in named}
    if kwargs.pop('return_dict', True) is False or kwargs.get('output_hidden_states') or kwargs.get('output_attentions'):
        raise ValueError('Document path returns final states/cache only')
    ids, embedded = inputs.get('input_ids'), inputs.get('inputs_embeds')
    if (ids is None) == (embedded is None):
        raise ValueError('Exactly one of token IDs or embeddings is required')
    if embedded is None:
        embedded = module.get_input_embeddings()(ids)
    features = module.get_image_features(inputs['pixel_values'], inputs['image_grid_thw'],
                                         return_dict=True, **kwargs)
    deepstack = features.deepstack_features
    image_embeds = torch.cat(features.pooler_output, dim=0).to(embedded.device, embedded.dtype)
    mask, _ = module.get_placeholder_mask(ids, inputs_embeds=embedded, image_features=image_embeds)
    embedded = embedded.masked_scatter(mask, image_embeds)
    visual = mask[..., 0]
    del features, image_embeds, mask
    positions = inputs.get('position_ids')
    if positions is None:
        positions = module.compute_3d_position_ids(input_ids=ids,
            image_grid_thw=inputs.get('image_grid_thw'), video_grid_thw=None,
            inputs_embeds=embedded, attention_mask=inputs.get('attention_mask'),
            past_key_values=inputs.get('past_key_values'), mm_token_type_ids=inputs.get('mm_token_type_ids'))
    outputs = module.language_model(input_ids=None, inputs_embeds=embedded, position_ids=positions,
        attention_mask=inputs.get('attention_mask'), past_key_values=inputs.get('past_key_values'),
        visual_pos_masks=visual, deepstack_visual_embeds=deepstack, **kwargs)
    return Qwen3VLModelOutputWithPast(**outputs, rope_deltas=module.rope_deltas)


@contextmanager
def bounded_document_runtime(prefill_chunk_size=2048, query_chunk_size=64):
    from transformers.models.qwen3_vl import modeling_qwen3_vl as module
    from visual_reasoning.stage0 import modeling
    original_mask, original_eager = module.create_causal_mask, module.eager_attention_forward
    original_forward, original_clone = module.Qwen3VLTextModel.forward, modeling._clone_inputs
    original_multimodal = module.Qwen3VLModel.forward
    def attention(*args, **kwargs):
        return grouped_eager(*args, query_chunk_size=query_chunk_size, **kwargs)
    def forward(self, *args, **kwargs):
        if args:
            raise ValueError('Document text forward requires explicit keyword inputs')
        return chunked_text_forward(self, original_forward, prefill_chunk_size=prefill_chunk_size, **kwargs)
    def multimodal(self, *args, **kwargs):
        if args:
            raise ValueError('Document multimodal forward requires explicit keyword inputs')
        return compact_image_forward(self, original_multimodal, **kwargs)
    def clone(inputs):
        # Canonical get_image_features only casts/reads pixel_values. Retain a
        # fresh processor result per example while avoiding a second large copy.
        result = original_clone({k: v for k, v in inputs.items() if k != 'pixel_values'})
        if 'pixel_values' in inputs:
            if inputs['pixel_values'].dtype != torch.bfloat16:
                raise ValueError('Compact document pixels must match the vision BF16 input dtype')
            result['pixel_values'] = inputs['pixel_values'].detach()
        return result
    module.create_causal_mask, module.eager_attention_forward = causal_shape, attention
    module.Qwen3VLTextModel.forward, modeling._clone_inputs = forward, clone
    module.Qwen3VLModel.forward = multimodal
    try:
        yield
    finally:
        module.create_causal_mask, module.eager_attention_forward = original_mask, original_eager
        module.Qwen3VLTextModel.forward, modeling._clone_inputs = original_forward, original_clone
        module.Qwen3VLModel.forward = original_multimodal
