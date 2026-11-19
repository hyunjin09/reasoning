import math

import pytest
import torch

from visual_reasoning.stage8a.instrumentation import (
    AttentionAssay, js_divergence, passive_statistics, value_delta,
)


def test_uniform_attention_retains_source_size_and_concentration():
    weights = torch.full((2, 6), 1 / 6)
    scores = torch.zeros_like(weights)
    result = passive_statistics(scores, weights, visual=[1, 2], reasoning=[4, 5])
    assert result["visual_mass"] == pytest.approx([1 / 3] * 2)
    assert result["qk_visual_nonvisual"] == pytest.approx([-math.log(2)] * 2)
    assert result["qk_visual_reasoning"] == pytest.approx([0.] * 2)
    assert result["visual_entropy"] == pytest.approx([1.] * 2)
    assert result["visual_effective_count"] == pytest.approx([2.] * 2)
    assert result["sink_mass"] == pytest.approx([1 / 6] * 2)


def test_passive_statistics_reject_future_or_overlapping_source_indices():
    a = torch.ones(2, 6) / 6
    with pytest.raises(ValueError):
        passive_statistics(a, a, visual=[1, 2], reasoning=[2, 5])
    with pytest.raises(ValueError):
        passive_statistics(a, a, visual=[6], reasoning=[4, 5])


def test_value_patch_uses_gqa_mapping_and_only_selected_source_heads():
    # Logical heads 0/1 share KV0; 2/3 share KV1. Only source1 changes.
    alpha = torch.tensor([[[[.2, .3, .5]], [[.1, .6, .3]],
                           [[.4, .1, .5]], [[.3, .2, .5]]]])
    native = torch.zeros(1, 2, 3, 2)
    donor = native.clone()
    donor[0, 0, 1] = torch.tensor([2., 4.])
    donor[0, 1, 1] = torch.tensor([5., 10.])
    delta = value_delta(alpha, native, donor, positions=[1], heads=[1, 2])
    expected = torch.zeros(1, 1, 4, 2)
    expected[0, 0, 1] = torch.tensor([1.2, 2.4])
    expected[0, 0, 2] = torch.tensor([.5, 1.])
    torch.testing.assert_close(delta, expected)
    assert torch.equal(value_delta(alpha, native, native, positions=[1], heads=[1, 2]), torch.zeros_like(delta))
    assert torch.count_nonzero(native) == 0


def test_js_is_symmetric_bounded_and_zero_for_identical_distributions():
    p, q = torch.tensor([100., -100.]), torch.tensor([-100., 100.])
    assert js_divergence(p, p) == 0.
    assert js_divergence(p, q) == pytest.approx(math.log(2), abs=1e-6)
    assert js_divergence(p, q) == js_divergence(q, p)


def test_actual_attention_capture_is_noop_and_fixed_route_self_is_noop():
    from transformers.models.qwen3_vl.configuration_qwen3_vl import Qwen3VLTextConfig
    from transformers.models.qwen3_vl.modeling_qwen3_vl import Qwen3VLTextAttention
    from types import SimpleNamespace

    torch.manual_seed(4)
    config = Qwen3VLTextConfig(hidden_size=16, num_attention_heads=4,
                             num_key_value_heads=2, head_dim=4,
                             num_hidden_layers=1, intermediate_size=32)
    config._attn_implementation = "eager"
    attn = Qwen3VLTextAttention(config, 0).eval()
    model = SimpleNamespace(model=SimpleNamespace(language_model=SimpleNamespace(
        layers=[SimpleNamespace(self_attn=attn)])))
    hidden = torch.randn(1, 6, 16)
    rope = (torch.ones(1, 6, 4), torch.zeros(1, 6, 4))
    mask = torch.full((1, 1, 6, 6), -torch.inf).triu(1)
    kwargs = dict(hidden_states=hidden, position_embeddings=rope, attention_mask=mask)
    with torch.no_grad():
        baseline = attn(**kwargs)[0]
        with AttentionAssay(model, layers=[0], visual=[1, 2], prompt_length=4) as assay:
            captured = attn(**kwargs)[0]
        assert torch.equal(baseline, captured)
        assert len(assay.records[0]["passive"]) == 6
        with AttentionAssay(model, layers=[0], visual=[1, 2], prompt_length=4,
                            frozen=assay.states, donor_values={0: assay.states[0]["value"]},
                            positions=[1, 2]) as patch:
            self_output = attn(**kwargs)[0]
        assert torch.equal(baseline, self_output)
        assert patch.records[0]["fixed_routing"]
        # Even a changed upstream state must not silently change fixed routing.
        donor = assay.states[0]["value"].clone()
        donor[:, :, 1:3] += .5
        with AttentionAssay(model, layers=[0], visual=[1, 2], prompt_length=4,
                            frozen=assay.states, donor_values={0: donor},
                            positions=[1, 2]) as patch:
            changed = attn(**{**kwargs, "hidden_states": hidden + .2})[0]
        assert not torch.equal(baseline, changed)
        assert patch.records[0]["routing_max_abs_delta"] == 0.
        assert torch.equal(attn(**kwargs)[0], baseline)
