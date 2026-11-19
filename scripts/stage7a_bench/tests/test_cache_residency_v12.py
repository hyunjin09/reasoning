"""CPU guards for exact cache values, ownership, and prefix audit semantics."""
import copy
from types import SimpleNamespace
import pytest
import torch
from transformers.cache_utils import DynamicCache
from visual_reasoning.stage3c9.streaming import StreamingPrefixState
from scripts.stage7a_bench.cache_residency_v12 import clone_streaming_state, cache_prefix_audit, offload_cache


def state():
    cache=DynamicCache()
    for i in range(3):
        k=torch.arange(40,dtype=torch.bfloat16).reshape(1,2,5,4)+i
        cache.update(k,k+10,i)
    return StreamingPrefixState(cache,torch.tensor([[7]]),5,0,torch.arange(64,dtype=torch.bfloat16))


def test_clone_preserves_exact_state_and_independent_storage():
    a=state(); b=clone_streaming_state(a)
    assert b is not a and b.cache is not a.cache
    for x,y in zip(a.cache.layers,b.cache.layers):
        assert torch.equal(x.keys,y.keys) and torch.equal(x.values,y.values)
        assert x.keys.data_ptr()!=y.keys.data_ptr() and x.values.data_ptr()!=y.values.data_ptr()
    assert a.prompt_length==b.prompt_length and a.generated_length==b.generated_length
    assert torch.equal(a.rope_deltas,b.rope_deltas) and torch.equal(a.last_logits,b.last_logits)
    b.cache.layers[0].keys.add_(1); b.last_logits.add_(1)
    assert not torch.equal(a.cache.layers[0].keys,b.cache.layers[0].keys)
    assert not torch.equal(a.last_logits,b.last_logits)


def test_prefix_audit_ignores_new_suffix_and_catches_past_mutation():
    a=state();b=clone_streaming_state(a)
    for i in range(3):
        k=torch.zeros(1,2,1,4,dtype=torch.bfloat16);b.cache.update(k,k,i)
    b.generated_length=1
    assert cache_prefix_audit(a,b)['passed']
    b.cache.layers[2].values[:,:,0,0]+=1
    result=cache_prefix_audit(a,b)
    assert not result['passed'] and not result['layers'][2]['past_value_exact']


def test_offload_is_idempotent_and_preserves_compute_side_metadata():
    a=state();before=copy.deepcopy(a);offload_cache(a);offload_cache(a)
    assert cache_prefix_audit(before,a)['passed']
    assert torch.equal(a.last_logits,before.last_logits)
    assert torch.equal(a.rope_deltas,before.rope_deltas)


def test_invalid_cache_rejected_before_clone():
    a=state();a.cache.layers[0].values=torch.zeros(3)
    with pytest.raises(ValueError):clone_streaming_state(a)


@pytest.mark.parametrize('candidate',[[3],[3,4],[3,4,5]])
def test_candidate_scores_equal_original_replay(candidate):
    from scripts.stage7a_bench.tests.test_causal_prefix_v2 import fixture
    from scripts.stage7a_bench.causal_prefix_v12 import make_benchmark_root
    from scripts.stage7a_bench.candidate_score_v12 import score_candidate_from_streaming_state as repaired
    from visual_reasoning.stage3c9.streaming import score_candidate_from_streaming_state as original
    model,prepared,event=fixture()
    with torch.inference_mode():
        root,_=make_benchmark_root(model,prepared,dict(no_image=False),event)
        expected=original(model=model,state=root,candidate_token_ids=candidate,seed=1234)
        before=copy.deepcopy(root)
        actual=repaired(model=model,state=root,candidate_token_ids=candidate,seed=1234)
        assert actual==expected
        assert cache_prefix_audit(before,root)['passed']
