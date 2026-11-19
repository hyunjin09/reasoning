import torch
import pytest
from visual_reasoning.stage3c10.runtime import delete_sources
from visual_reasoning.stage3c4.runtime import apply_source_contribution_window

def tensors():
    g=torch.Generator().manual_seed(87)
    values=torch.randn(1,4,40,8,generator=g).bfloat16()
    alpha=torch.softmax(torch.randn(1,4,1,40,generator=g),-1).bfloat16()
    output=torch.matmul(alpha,values).transpose(1,2)
    return output,alpha,values

def test_single_source_exactly_reuses_t0_and_noop_is_exact():
    o,a,v=tensors(); snapshots=[x.clone() for x in (o,a,v)]
    result,_=delete_sources(o,a,v,[[1,3,4]],offset=39)
    expected,_,_=apply_source_contribution_window(o,a,v,source_positions=[1,3,4],selected_heads=list(range(4)),query_positions=[0],query_position_offset=39,gain=0.)
    assert torch.equal(result,expected)
    noop,_=delete_sources(o,a,v,[[1,3,4]],offset=39,gain=1.)
    assert torch.equal(o,noop)
    assert all(torch.equal(x,y) for x,y in zip((o,a,v),snapshots))

def test_joint_sources_are_native_disjoint_and_single_rounding():
    o,a,v=tensors(); source1=[1,3,4];source2=[7,8]
    actual,_=delete_sources(o,a,v,[source1,source2],offset=39)
    contributions=[(a[:,:,:,s].squeeze(2)[...,None]*v[:,:,s]).sum(2).float() for s in [source1,source2]]
    expected=(o[:,0].float()-contributions[0]-contributions[1]).bfloat16()
    assert torch.equal(actual[:,0],expected)
    with pytest.raises(ValueError):delete_sources(o,a,v,[[1],[1]],offset=39)
