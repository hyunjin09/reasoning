import pytest
import torch
from transformers.models.qwen3_vl import modeling_qwen3_vl as qwen
from transformers.models.qwen3_vl.configuration_qwen3_vl import Qwen3VLConfig

from scripts.stage7a_bench.causal_prefix_v2 import make_benchmark_root, require_canonical_assay_attention
from scripts.stage7a_bench.bounded_attention_v2 import bounded_native_attention
from visual_reasoning.stage6b.text_interface import prefill_condition
from visual_reasoning.stage4a.runtime import make_event_root


def fixture():
    torch.manual_seed(72)
    config = Qwen3VLConfig(text_config=dict(vocab_size=64, hidden_size=32, intermediate_size=64,
        num_hidden_layers=2, num_attention_heads=4, num_key_value_heads=2, head_dim=16,
        rope_parameters=dict(rope_type='default', rope_theta=1000000., mrope_section=[2, 3, 3])),
        vision_config=dict(depth=2, hidden_size=32, intermediate_size=64, num_heads=4,
            patch_size=2, temporal_patch_size=1, spatial_merge_size=2, out_hidden_size=32,
            num_position_embeddings=64, deepstack_visual_indexes=[0, 1]),
        image_token_id=60, video_token_id=61, vision_start_token_id=62, vision_end_token_id=63)
    config.text_config._attn_implementation = 'eager'; config.vision_config._attn_implementation = 'sdpa'
    model = qwen.Qwen3VLForConditionalGeneration(config).to(torch.bfloat16).eval()
    ids = torch.tensor([[1, 62]+[60]*4+[63, 10]])
    prepared = dict(input_ids=ids, attention_mask=torch.ones_like(ids),
        mm_token_type_ids=(ids == 60).long(), image_grid_thw=torch.tensor([[1, 4, 4]]),
        pixel_values=torch.randn(16, 12))
    event = dict(candidate_start_token=12, current_query_zero_based=11,
                 history_before_ed_token_ids=[4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15])
    return model, prepared, event


@pytest.mark.parametrize('document', [False, True])
def test_prefix_preserves_native_logits_kv_then_returns_attention_weights(document):
    model, prepared, event = fixture()
    with torch.inference_mode():
        prefill, _ = prefill_condition(model, prepared, False)
        expected = make_event_root(model, prefill, event)
        actual, audit = make_benchmark_root(model, prepared, dict(no_image=False, document_path='test.pdf' if document else None), event)
        require_canonical_assay_attention()
        torch.testing.assert_close(actual.last_logits, expected.last_logits, rtol=0, atol=0)
        for a, b in zip(actual.cache.layers, expected.cache.layers):
            torch.testing.assert_close(a.keys, b.keys, rtol=0, atol=0)
            torch.testing.assert_close(a.values, b.values, rtol=0, atol=0)
        # Test the actual eager interface needed by inherited source suppression.
        module = model.model.language_model.layers[0].self_attn
        q = torch.randn(1, 4, 1, 16, dtype=torch.bfloat16)
        k = torch.randn(1, 2, 9, 16, dtype=torch.bfloat16);v = torch.randn_like(k)
        _, weights = qwen.eager_attention_forward(module, q, k, v, None, module.scaling)
        assert weights.shape == (1, 4, 1, 9)
        assert audit['canonical_assay_attention_restored'] is True
        assert actual.generated_length == 4


def test_assay_inside_bounded_context_is_rejected():
    with bounded_native_attention():
        with pytest.raises(RuntimeError, match='canonical eager'):
            require_canonical_assay_attention()
    require_canonical_assay_attention()


def test_failed_prefix_restores_canonical_attention():
    model, prepared, event = fixture()
    event['candidate_start_token'] = 1
    with pytest.raises(ValueError, match='coordinates'):
        make_benchmark_root(model, prepared, dict(no_image=False), event)
    require_canonical_assay_attention()
