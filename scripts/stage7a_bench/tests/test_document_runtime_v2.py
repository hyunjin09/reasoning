from types import SimpleNamespace

import pytest
import torch
from transformers.models.qwen3_vl.configuration_qwen3_vl import Qwen3VLTextConfig
from transformers.models.qwen3_vl.modeling_qwen3_vl import Qwen3VLTextModel, eager_attention_forward

from scripts.stage7a_bench.bounded_attention_v2 import CausalShape
from scripts.stage7a_bench.document_runtime_v2 import grouped_eager, bounded_document_runtime


@pytest.mark.parametrize('queries,past', [(19, 0), (3, 17), (1, 22)])
def test_grouped_keys_do_not_change_attention(queries, past):
    torch.manual_seed(27)
    q = torch.randn(1, 8, queries, 16, dtype=torch.bfloat16)
    k = torch.randn(1, 2, queries+past, 16, dtype=torch.bfloat16)
    v = torch.randn_like(k)
    module = SimpleNamespace(num_key_value_groups=4, training=False)
    allowed = torch.arange(queries+past)[None] <= torch.arange(past, past+queries)[:, None]
    mask = torch.zeros_like(allowed, dtype=q.dtype).masked_fill(~allowed, torch.finfo(q.dtype).min)[None, None]
    expected, _ = eager_attention_forward(module, q, k, v, mask, .25)
    actual, weights = grouped_eager(module, q, k, v, CausalShape(queries, past), .25, query_chunk_size=5)
    torch.testing.assert_close(actual, expected, rtol=0, atol=0)
    assert weights is None


def test_chunked_prefill_preserves_multimodal_positions_deepstack_and_cache():
    torch.manual_seed(19)
    config = Qwen3VLTextConfig(vocab_size=64, hidden_size=32, intermediate_size=64,
        num_hidden_layers=2, num_attention_heads=4, num_key_value_heads=2, head_dim=16,
        rope_parameters=dict(rope_type='default', rope_theta=1000000., mrope_section=[2, 3, 3]))
    config._attn_implementation = 'eager'
    model = Qwen3VLTextModel(config).to(torch.bfloat16).eval()
    x = torch.randn(1, 29, 32, dtype=torch.bfloat16)
    visual = torch.zeros(1, 29, dtype=torch.bool)
    visual[:, 3:15] = True
    visual[:, 18:25] = True
    positions = torch.arange(29).view(1, 1, -1).expand(4, 1, -1).clone()
    positions[1:, :, 3:15] = torch.arange(12).view(1, 1, -1) // 3 + 3
    features = [torch.randn(19, 32, dtype=torch.bfloat16) for _ in range(2)]
    inputs = dict(inputs_embeds=x, position_ids=positions, attention_mask=torch.ones(1, 29),
                  visual_pos_masks=visual, deepstack_visual_embeds=features, use_cache=True)
    with torch.inference_mode():
        original = model(**inputs)
        with bounded_document_runtime(prefill_chunk_size=7, query_chunk_size=3):
            actual = model(**inputs)
    torch.testing.assert_close(actual.last_hidden_state, original.last_hidden_state, rtol=0, atol=0)
    for a, b in zip(actual.past_key_values.layers, original.past_key_values.layers):
        torch.testing.assert_close(a.keys, b.keys, rtol=0, atol=0)
        torch.testing.assert_close(a.values, b.values, rtol=0, atol=0)
    assert actual.past_key_values.get_seq_length() == 29


def test_document_scope_restores_clone_behavior_and_rejects_training():
    from visual_reasoning.stage0 import modeling
    original = modeling._clone_inputs
    pixels = torch.randn(3, 4, dtype=torch.bfloat16)
    ids = torch.tensor([[1, 2]])
    with bounded_document_runtime():
        result = modeling._clone_inputs(dict(pixel_values=pixels, input_ids=ids))
        assert result['pixel_values'].data_ptr() == pixels.data_ptr()
        assert result['input_ids'].data_ptr() != ids.data_ptr()
    assert modeling._clone_inputs is original
    with pytest.raises(ValueError, match='inference'):
        grouped_eager(SimpleNamespace(training=True), None, None, None, None, 1.)


def test_full_image_prefill_releases_unused_vision_outputs_and_preserves_logits():
    import weakref
    from transformers.models.qwen3_vl.configuration_qwen3_vl import Qwen3VLConfig
    from transformers.models.qwen3_vl.modeling_qwen3_vl import Qwen3VLForConditionalGeneration
    torch.manual_seed(57)
    config = Qwen3VLConfig(text_config=dict(vocab_size=64, hidden_size=32, intermediate_size=64,
        num_hidden_layers=2, num_attention_heads=4, num_key_value_heads=2, head_dim=16,
        rope_parameters=dict(rope_type='default', rope_theta=1000000., mrope_section=[2, 3, 3])),
        vision_config=dict(depth=2, hidden_size=32, intermediate_size=64, num_heads=4,
            patch_size=2, temporal_patch_size=1, spatial_merge_size=2, out_hidden_size=32,
            num_position_embeddings=64, deepstack_visual_indexes=[0, 1]),
        image_token_id=60, video_token_id=61, vision_start_token_id=62, vision_end_token_id=63)
    config.text_config._attn_implementation = 'eager'
    config.vision_config._attn_implementation = 'sdpa'
    model = Qwen3VLForConditionalGeneration(config).to(torch.bfloat16).eval()
    ids = torch.tensor([[1, 62]+[60]*4+[63, 10, 62]+[60]*6+[63, 11]])
    inputs = dict(input_ids=ids, attention_mask=torch.ones_like(ids),
        mm_token_type_ids=(ids == 60).long(), image_grid_thw=torch.tensor([[1, 4, 4], [1, 4, 6]]),
        pixel_values=torch.randn(40, 12), use_cache=True, logits_to_keep=1)
    retained, released = [], []
    get_features = model.model.get_image_features
    def capture(*args, **kwargs):
        result = get_features(*args, **kwargs)
        retained[:] = [weakref.ref(result.last_hidden_state), weakref.ref(result.pooler_output[0])]
        return result
    model.model.get_image_features = capture
    hook = model.model.language_model.register_forward_pre_hook(
        lambda *_: released.append(all(ref() is None for ref in retained)))
    with torch.inference_mode():
        expected = model(**inputs)
        model.model.rope_deltas = None
        compact = dict(inputs, pixel_values=inputs['pixel_values'].to(torch.bfloat16))
        with bounded_document_runtime(prefill_chunk_size=5, query_chunk_size=3):
            actual = model(**compact)
    hook.remove()
    assert released == [False, True]
    torch.testing.assert_close(actual.logits, expected.logits, rtol=0, atol=0)
    torch.testing.assert_close(actual.rope_deltas, expected.rope_deltas, rtol=0, atol=0)
    for a, b in zip(actual.past_key_values.layers, expected.past_key_values.layers):
        torch.testing.assert_close(a.keys, b.keys, rtol=0, atol=0)
        torch.testing.assert_close(a.values, b.values, rtol=0, atol=0)
