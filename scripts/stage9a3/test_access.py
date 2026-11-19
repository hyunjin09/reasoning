import torch
import pytest
from types import SimpleNamespace
from visual_reasoning.stage9a3.access import AccessMask,blocked_rows,depth_count,canonical


def test_two_model_depth_counts_and_aliases():
    assert [depth_count(f,36) for f in [0,.5,.75,1]]==[0,18,27,36]
    assert [depth_count(f,28) for f in [0,.5,.75,1]]==[0,14,21,28]
    assert len({canonical(f,t) for f in [0,.5,.75,1] for t in [0,16,64,None]})==10
    assert canonical(0,None)==canonical(1,0)


def test_generated_query_rectangle_preserves_prefill_and_cutoff_inclusivity():
    assert blocked_rows(35,0,8,8,0,0)==[]
    assert blocked_rows(17,8,4,8,18,2)==[2,3]
    assert blocked_rows(18,8,4,8,18,2)==[0,1,2,3]
    assert blocked_rows(35,8,4,8,36,None)==[]


@pytest.mark.parametrize('backend',['qwen25','qwen3'])
def test_actual_backend_probability_and_sink_operation(backend):
    module=SimpleNamespace(layer_idx=0,num_key_value_groups=1,training=False)
    q=torch.zeros(1,1,1,2);k=torch.zeros(1,1,3,2)
    v=torch.tensor([[[[1.,0.],[9.,9.],[0.,1.]]]])
    for mode,expected in [('standard',[.5,0,.5]),('null_sink',[1/3,0,1/3])]:
        mask=AccessMask(backend=backend,visual=[1],prompt_length=2,layers=36 if backend=='qwen25' else 28,
                        layer_cutoff=0,token_cutoff=None,mode=mode,audit=True)
        with mask:
            out,w=mask.impl.eager_attention_forward(module,q,k,v,None,scaling=1.)
        torch.testing.assert_close(w[0,0,0],torch.tensor(expected))
        torch.testing.assert_close(out[0,0,0],torch.tensor([expected[0],expected[2]]))
        assert mask.records[0]['masked_probability_max']==0
        if mode=='null_sink':assert mask.records[0]['nonvisual_probability_delta']==0


def test_sentinel_exact_and_restores_backend_on_exception():
    module=SimpleNamespace(layer_idx=35,num_key_value_groups=1,training=False)
    mask=AccessMask(backend='qwen25',visual=[0],prompt_length=2,layers=36,layer_cutoff=36,token_cutoff=None)
    native=mask.impl.eager_attention_forward
    q=torch.ones(1,1,1,2);k=torch.ones(1,1,3,2);v=torch.arange(6,dtype=torch.float32).reshape(1,1,3,2)
    expected=native(module,q,k,v,None,scaling=1.)
    with pytest.raises(RuntimeError):
        with mask:
            actual=mask.impl.eager_attention_forward(module,q,k,v,None,scaling=1.)
            assert all(torch.equal(a,b) for a,b in zip(actual,expected))
            raise RuntimeError('restore')
    assert mask.impl.eager_attention_forward is native
