import torch
from visual_reasoning.stage8c.native_partition import full_axis_parts


def test_full_axis_partition_preserves_gqa_heads_and_source_scope():
    weights=torch.tensor([[.2,.3,.5],[.4,.1,.5]],dtype=torch.float64)
    values=torch.arange(12,dtype=torch.float64).reshape(2,3,2)
    cv,cn=full_axis_parts(weights,values,[1])
    native=torch.matmul(weights[:,None,:],values).squeeze(1)
    assert torch.allclose(cv+cn,native)
    assert torch.equal(cv,weights[:,1,None]*values[:,1])
    assert cv.dtype==weights.dtype and cn.dtype==values.dtype


def test_bf16_rounding_is_not_assumed_distributive():
    # This native representational fact guards against treating an FP32
    # measurement of separately rounded partitions as an exact identity.
    a=torch.tensor(35.4,dtype=torch.float32)
    b=torch.tensor(-.13,dtype=torch.float32)
    separately=a.bfloat16().float()+b.bfloat16().float()
    jointly=(a+b).bfloat16().float()
    assert not torch.equal(separately,jointly)
