import pytest
import torch

from visual_reasoning.stage8a.measurement import projected_transport, zero_mass_convention, feature_vector


def test_projected_cancellation_uses_raw_residual_and_preserves_denominators():
    # Two logical heads project in opposite directions into the same residual.
    visual = torch.tensor([[[[2.], [1.]]]])
    total = torch.tensor([[[[3.], [1.]]]])
    weight = torch.tensor([[1., -1.], [0., 0.]])
    residual = torch.tensor([[[3., 4.]]])
    r = projected_transport(visual, total, weight, residual)
    assert r["postWO_ratio"] == pytest.approx([.5])
    assert r["residual_ratio"] == pytest.approx([.2])
    assert r["head_cancellation_ratio"] == pytest.approx([1/3])
    assert r["head_cosine_disagreement"] == pytest.approx([2.])
    assert r["residual_norm"] == [5.]


def test_zero_visual_mass_does_not_imply_one_effective_visual_token():
    original = dict(visual_mass=[0., .5], visual_entropy=[0., .8], visual_effective_count=[1., 5.])
    r = zero_mass_convention(original)
    assert r["visual_effective_count"] == [0., 5.]
    assert original["visual_effective_count"] == [1., 5.]


def record(x):
    return {str(l): {"passive":[dict(visual_mass=[x, x+2], qk_visual_nonvisual=[x+4,x+6],
            qk_visual_reasoning=[x+8,x+10], visual_top4_mass=[x,x], visual_max=[x,x],
            visual_entropy=[x,x], visual_effective_count=[x,x],sink_mass=[x,x])]}
            for l in (19,20)}


def test_temporal_features_use_only_strict_past_and_no_value_or_roi():
    r = feature_vector(record(10), [record(0), record(2), record(4)], aggregation="median", window=2)
    assert r["visual_mass"] == 11.
    assert r["delta_visual_mass"] == 7.
    assert r["delta_sink_mass"] == 7.
    assert not any("roi" in k.lower() or "transport" in k.lower() or "value" in k.lower() for k in r)
    with pytest.raises(ValueError, match="past"):
        feature_vector(record(10), [], aggregation="median", window=2)


def test_measurement_hooks_read_pre_normalization_residual_without_changing_forward():
    from types import SimpleNamespace
    from transformers.models.qwen3_vl.configuration_qwen3_vl import Qwen3VLTextConfig
    from transformers.models.qwen3_vl.modeling_qwen3_vl import Qwen3VLTextAttention
    from visual_reasoning.stage8a.measurement import MeasurementAssay

    class Layer(torch.nn.Module):
        def __init__(self):
            super().__init__()
            cfg = Qwen3VLTextConfig(hidden_size=16, num_attention_heads=4, num_key_value_heads=2,
                                   head_dim=4, num_hidden_layers=1, intermediate_size=32)
            cfg._attn_implementation = "eager"
            self.self_attn = Qwen3VLTextAttention(cfg,0)
            self.norm = torch.nn.LayerNorm(16)

        def forward(self, hidden_states, **kwargs):
            return hidden_states + self.self_attn(hidden_states=self.norm(hidden_states), **kwargs)[0]

    torch.manual_seed(7)
    layer = Layer().eval()
    model = SimpleNamespace(model=SimpleNamespace(language_model=SimpleNamespace(layers=[layer])))
    x = 3*torch.randn(1,6,16)
    kwargs = dict(position_embeddings=(torch.ones(1,6,4), torch.zeros(1,6,4)),
                  attention_mask=torch.full((1,1,6,6), -torch.inf).triu(1))
    with torch.no_grad():
        reference = layer(x, **kwargs)
        with MeasurementAssay(model, layers=[0], visual=[1,2], prompt_length=4) as assay:
            observed = layer(x, **kwargs)
        assert torch.equal(reference, observed)
        assert assay.records[0]["transport"]["residual_norm"] == pytest.approx(x.norm(dim=-1)[0].tolist())
        assert not layer._forward_pre_hooks
