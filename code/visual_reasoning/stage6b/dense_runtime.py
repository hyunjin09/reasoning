"""Passive native endpoints; no invented candidate contrasts or causal labels."""
import hashlib
import torch
from visual_reasoning.stage3c9.streaming import clone_streaming_state,advance_streaming_state
from visual_reasoning.stage6b.runtime import Stage6BPassiveStep
from visual_reasoning.stage6b.dense_partition import endpoint_partition


def same_state(a,b):
    return torch.equal(a.last_logits,b.last_logits) and all(torch.equal(x.keys,y.keys) and torch.equal(x.values,y.values) for x,y in zip(a.cache.layers,b.cache.layers))


@torch.inference_mode()
def endpoint_root(model,checkpoint,ids,end):
    boundary,partial,_=endpoint_partition(end)
    assert checkpoint.generated_length==boundary
    root=clone_streaming_state(checkpoint)
    for a,b in partial:
        advance_streaming_state(model=model,state=root,token_ids=ids[a:b],seed=1234,chunk_size=2048,release_allocator_cache=True)
    return root


@torch.inference_mode()
def collect_endpoint(model,root,ids,end,source_groups,input_meta,validate=False):
    current=end-1
    state=clone_streaming_state(root)
    for i in range(end-8,current):
        advance_streaming_state(model=model,state=state,token_ids=[ids[i]],seed=1234,chunk_size=1,release_allocator_cache=True)
    reference=clone_streaming_state(state)
    visual=input_meta['visual_token_indices'];groups={k:v for k,v in source_groups.items() if v}
    if visual:groups['visual']=visual
    groups['sink']=[0];visualset=set(visual)
    groups['prompt_text']=[i for i in range(1,root.prompt_length) if i not in visualset]
    groups['reasoning']=list(range(root.prompt_length,root.prompt_length+end))
    grid=(input_meta['image_grid_thw'][1]//2,input_meta['image_grid_thw'][2]//2) if visual else None
    with Stage6BPassiveStep(model,root.prompt_length+current,groups,grid) as capture:
        advance_streaming_state(model=model,state=state,token_ids=[ids[current]],seed=1234,chunk_size=1,release_allocator_cache=True)
    advance_streaming_state(model=model,state=reference,token_ids=[ids[current]],seed=1234,chunk_size=1,release_allocator_cache=True)
    exact=torch.equal(state.last_logits,reference.last_logits)
    kv_exact=same_state(state,reference) if validate else None
    assert exact and (not validate or kv_exact)
    logits=state.last_logits.float();logp=torch.log_softmax(logits,dim=-1);top=torch.topk(logp,k=50)
    telemetry=capture.telemetry
    assert set(telemetry)=={'28','29'} and all(t['all_values_finite'] for t in telemetry.values())
    for layer,t in telemetry.items():
        # Every head is measured; save primary means and fixed historical-head means.
        heads=t['historical_selected_heads']
        t['historical_selected_head_groups']={g:{k:sum(t['per_head'][h]['groups'][g][k] for h in heads)/len(heads)
            for k,v in t['per_head'][0]['groups'][g].items() if isinstance(v,(int,float))}
            for g in t['per_head'][0]['groups']}
        t.pop('per_head')
    result={'telemetry':telemetry,'residual_norms':capture.residual,'attention_output_norms':capture.output_norms,
        'predictive_entropy':float(-(logp.exp()*logp).sum()),'current_logits_sha256':hashlib.sha256(logits.cpu().numpy().tobytes()).hexdigest(),
        'top50_token_ids':top.indices.cpu().tolist(),'top50_log_probabilities':top.values.cpu().tolist(),
        'native_next_token_logP':float(logp[ids[end]]) if end<len(ids) else None,
        'candidate_margin':None,'candidate_margin_status':'No independently specified future semantic contrast at span endpoint; exact readout anchors scored separately.',
        'native_passive_logits_exact':exact,'mechanics_all_kv_exact':kv_exact,'current_query_zero_based':current,
        'feature_scope':'Primary mean over all32heads of layers28-29; fixed historical heads secondary only.'}
    del state,reference
    return result
