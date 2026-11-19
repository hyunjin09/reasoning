from types import SimpleNamespace
import torch
from visual_reasoning.stage9a_dynamics.access import TemporalAccessMask, blocked_rows


def test_temporal_mask_reopens_and_preserves_prefill_and_other_layers():
    assert blocked_rows(19,0,8,8,[(1,3)])==[]
    assert blocked_rows(19,8,4,8,[(1,3)])==[0,1]
    assert blocked_rows(18,8,4,8,[(1,3)])==[]
    assert blocked_rows(22,8,4,8,[(3,None)])==[2,3]
    assert blocked_rows(23,8,4,8,[(1,None)])==[]


def test_standard_and_sink_probability_semantics():
    from transformers.models.qwen3_vl import modeling_qwen3_vl as impl
    m=SimpleNamespace(layer_idx=19,num_key_value_groups=1,training=False)
    q=torch.zeros(1,1,1,2);k=torch.zeros(1,1,3,2);v=torch.tensor([[[[1.,0.],[9.,9.],[0.,1.]]]])
    for mode,expected in [('standard',.5),('null_sink',1/3)]:
        with TemporalAccessMask(visual=[1],prompt_length=2,intervals=[(1,2)],mode=mode,audit=True) as mask:
            out,w=impl.eager_attention_forward(m,q,k,v,None,scaling=1.)
        assert w[0,0,0,1]==0
        torch.testing.assert_close(out,torch.full_like(out,expected))
        if mode=='null_sink':assert mask.records[0]['nonvisual_probability_max_delta']==0


def test_full_access_is_exact_and_context_restores_backend():
    from transformers.models.qwen3_vl import modeling_qwen3_vl as impl
    f=impl.eager_attention_forward;m=SimpleNamespace(layer_idx=19,num_key_value_groups=1,training=False)
    torch.manual_seed(7);q=torch.randn(1,1,1,3);k=torch.randn(1,1,4,3);v=torch.randn_like(k)
    expected=f(m,q,k,v,None,scaling=.5)
    with TemporalAccessMask(visual=[1],prompt_length=2,intervals=[]):
        actual=impl.eager_attention_forward(m,q,k,v,None,scaling=.5)
    assert impl.eager_attention_forward is f
    assert all(torch.equal(a,b) for a,b in zip(expected,actual))
