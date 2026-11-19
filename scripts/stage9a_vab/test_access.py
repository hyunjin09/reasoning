from types import SimpleNamespace

import torch

from visual_reasoning.stage9a_vab.access import AccessMask, blocked_rows


def test_generation_query_indexing_preserves_prefill_and_cutoff_inclusivity():
    assert blocked_rows(0,0,8,8,28,0)==[]
    assert blocked_rows(0,8,4,8,28,2)==[2,3]
    assert blocked_rows(27,8,4,8,28,None)==[]
    assert blocked_rows(1,8,4,8,1,20)==[0,1,2,3]
    assert blocked_rows(0,8,1,8,0,None)==[0]


def test_query_text_control_changes_only_declared_prompt_rows_above_layer_cutoff():
    args=(0,0,8,8,1,None)
    assert blocked_rows(*args,query_text=(5,6),query_control=True)==[]
    assert blocked_rows(1,*args[1:],query_text=(5,6),query_control=True)==[5,6]


def test_mask_vs_null_sink_have_different_real_attention_normalization():
    from transformers.models.qwen3_vl import modeling_qwen3_vl as impl
    module=SimpleNamespace(layer_idx=0,num_key_value_groups=1,training=False)
    q=torch.zeros(1,1,1,2);k=torch.zeros(1,1,3,2)
    v=torch.tensor([[[[1.,0.],[9.,9.],[0.,1.]]]])
    standard=AccessMask(visual=(1,),prompt_length=2,layer_cutoff=0,token_cutoff=None)
    sink=AccessMask(visual=(1,),prompt_length=2,layer_cutoff=0,token_cutoff=None,mode='null_sink')
    standard.original=sink.original=impl.eager_attention_forward
    out,w=standard.forward(module,q,k,v,None,scaling=1.)
    sout,sw=sink.forward(module,q,k,v,None,scaling=1.)
    assert w[0,0,0,1]==0 and sw[0,0,0,1]==0
    torch.testing.assert_close(w[0,0,0],torch.tensor([.5,0.,.5]))
    torch.testing.assert_close(sw[0,0,0],torch.tensor([1/3,0.,1/3]))
    torch.testing.assert_close(out,torch.tensor([[[[.5,.5]]]]))
    torch.testing.assert_close(sout,torch.tensor([[[[1/3,1/3]]]]))


def test_noop_leaves_native_attention_bit_identical_and_restores_function():
    from transformers.models.qwen3_vl import modeling_qwen3_vl as impl
    module=SimpleNamespace(layer_idx=27,num_key_value_groups=1,training=False)
    torch.manual_seed(1);q=torch.randn(1,1,1,3);k=torch.randn(1,1,4,3);v=torch.randn_like(k)
    original=impl.eager_attention_forward
    expected=original(module,q,k,v,None,scaling=.5)
    with AccessMask(visual=(1,),prompt_length=2,layer_cutoff=28,token_cutoff=None):
        actual=impl.eager_attention_forward(module,q,k,v,None,scaling=.5)
    assert impl.eager_attention_forward is original
    assert all(torch.equal(a,b) for a,b in zip(actual,expected))
