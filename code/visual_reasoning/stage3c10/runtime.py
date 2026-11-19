"""Current-token source deletion and native-Q mediation on canonical cached steps."""
from contextlib import AbstractContextManager, ExitStack
from types import MethodType
import torch

from visual_reasoning.stage3b6.heads import _attention_module, _project_attention_output
from visual_reasoning.stage3c1.metrics import _repeat_kv
from visual_reasoning.stage3c3.metrics import summarize_routing_state
from visual_reasoning.stage3c3.runtime import _projection_parts, _run_attention, splice_current_query_heads
from visual_reasoning.stage3c4.runtime import apply_source_contribution_window
from visual_reasoning.stage3c9.streaming import (
    advance_streaming_state, clone_streaming_state, score_preference_from_streaming_state,
)


def delete_sources(output, attention, values, groups, *, offset, gain=0.):
    """Subtract disjoint source terms from one native output with one BF16 write."""
    if any(set(a) & set(b) for i,a in enumerate(groups) for b in groups[i+1:]):
        raise ValueError('Simultaneous source groups must be disjoint')
    contributions, audits = [], []
    for sources in groups:
        patched, parts, audit = apply_source_contribution_window(
            output, attention, values, source_positions=sources,
            selected_heads=list(range(output.shape[2])), query_positions=[0],
            query_position_offset=offset, gain=gain)
        contributions.append(parts[offset])
        audits.append(audit)
    if not groups or gain == 1.:
        return output, audits
    if len(groups) == 1:
        return patched, audits  # exactly inherited T0 arithmetic
    modified = output.clone()
    expected = output[:,0].float()
    for contribution in contributions:
        expected = expected - (1. - gain) * contribution
    modified[:,0] = expected.to(output.dtype)
    return modified, audits


def cache_prefix_audit(before, after):
    n = before.prompt_length + before.generated_length
    rows=[]
    for layer, (a,b) in enumerate(zip(before.cache.layers,after.cache.layers)):
        rows.append({'layer_index':layer,
            'past_key_exact':torch.equal(a.keys,b.keys[:,:,:n]),
            'past_value_exact':torch.equal(a.values,b.values[:,:,:n])})
    return {'past_length':n,'layers':rows,'passed':all(x['past_key_exact'] and x['past_value_exact'] for x in rows)}


class QueryStepPatch(AbstractContextManager):
    """Hook only a single-token step; past K/V stay in the recipient cache."""
    def __init__(self, *, model, routing_layer, heads, noncausal_heads, groups,
                 trigger_positions=(), trigger_layers=(), roi_positions=(),
                 donor_q=None, rescue_heads=(), donor_hpre=None, gain=0.):
        self.model=model; self.layer=int(routing_layer); self.heads=heads
        self.noncausal_heads=noncausal_heads; self.groups=groups
        self.trigger=list(trigger_positions); self.layers=set(trigger_layers)
        self.roi=list(roi_positions); self.donor_q=donor_q
        self.rescue_heads=list(rescue_heads); self.donor_hpre=donor_hpre; self.gain=gain
        self.originals=[]; self.handles=[]; self.audits=[]; self.norms=[]
        self.routing=None; self.q=None; self.hpre=None; self.q_audit=None
        self.hpre_audit=None

    def _hpre(self, module, args):
        hidden=args[0]
        if hidden.shape[1]!=1: raise RuntimeError('Current-query step must contain exactly one token')
        self.hpre=hidden.detach().clone()
        if self.donor_hpre is not None:
            patched=hidden.clone(); patched[:,0]=self.donor_hpre[:,0].to(hidden)
            self.hpre_audit={'current_query_only':True,'copied_native_exact':torch.equal(patched,self.donor_hpre.to(hidden))}
            return (patched,*args[1:])

    def _run(self, module, hidden_states, position_embeddings, attention_mask,
             past_key_values=None, **kwargs):
        if hidden_states.shape[1]!=1: raise RuntimeError('Patch escaped the single current query')
        layer=int(module.layer_idx)
        pre_q,pre_k,query,key,value=_projection_parts(module,hidden_states,position_embeddings)
        if past_key_values is not None:
            key,value=past_key_values.update(key,value,layer)
        offset=int(key.shape[2])-1
        q_before=query.clone(); k_before=key.clone(); v_before=value.clone()
        if layer==self.layer and self.donor_q is not None:
            query,splice=splice_current_query_heads(query,self.donor_q.to(query),
                recipient_position=0,selected_heads=self.rescue_heads)
            self.q_audit={**splice,'recipient_key_exact':torch.equal(key,k_before),
                'recipient_value_exact':torch.equal(value,v_before),
                'donor_same_position':True,'formulation':'direct_post_rope_same_position'}
        native,attention=_run_attention(module,query,key,value,attention_mask,kwargs)
        attention_before=attention.clone()
        if layer==self.layer:
            state={'post_rope_query':query[:,:,0].detach(), 'key':key.detach(),
                'value':value.detach(),'attention':attention[:,:,0].detach(),
                'wo_weight':module.o_proj.weight.detach(), 'scaling':float(module.scaling),
                'num_key_value_groups':int(module.num_key_value_groups)}
            self.routing={role:summarize_routing_state(state,groups=self.groups,selected_heads=hs)
                          for role,hs in [('causal',self.heads),('noncausal',self.noncausal_heads)]}
            self.q=query[:,:,0].detach().clone()
        sources=[]; names=[]
        if layer in self.layers and self.trigger: sources.append(self.trigger); names.append('trigger')
        if self.roi: sources.append(self.roi); names.append('visual_roi')
        patched,audits=delete_sources(native,attention,_repeat_kv(value,int(module.num_key_value_groups)),
                                      sources,offset=offset,gain=self.gain)
        for name,audit in zip(names,audits):
            self.audits.append({**audit,'source_kind':name,'layer_index':layer,
                'query_unchanged_by_source_deletion':torch.equal(query,q_before) if self.donor_q is None or layer!=self.layer else None,
                'key_unchanged_by_source_deletion':torch.equal(key,k_before),
                'value_unchanged_by_source_deletion':torch.equal(value,v_before),
                'attention_unchanged_by_source_deletion':torch.equal(attention,attention_before)})
        projected=_project_attention_output(module,patched,hidden_states)
        self.norms.append({'layer_index':layer,'attention_input_norm':float(hidden_states.float().norm().item()),
            'attention_output_norm':float(projected.float().norm().item()),
            'finite':bool(torch.isfinite(projected).all().item())})
        return projected,attention

    def __enter__(self):
        self.handles.append(self.model.model.language_model.layers[self.layer].register_forward_pre_hook(self._hpre))
        for layer in range(36):
            module=_attention_module(self.model,layer); self.originals.append((module,module.forward))
            def forward(module,hidden_states,position_embeddings,attention_mask,past_key_values=None,**kwargs):
                return self._run(module,hidden_states,position_embeddings,attention_mask,past_key_values,**kwargs)
            module.forward=MethodType(forward,module)
        return self

    def __exit__(self,*args):
        for module,original in self.originals: module.forward=original
        for handle in self.handles: handle.remove()


@torch.inference_mode()
def score_arm(*, model, root, context, partition, target, groups, trigger_positions=(),
              trigger_layers=(), roi_positions=(), donor_q=None, rescue_heads=(),
              donor_hpre=None, gain=0., original_suffix, counterfactual_suffix,
              validate=False):
    state=clone_streaming_state(root)
    current=root.generated_length
    patch=QueryStepPatch(model=model,routing_layer=target['layer_index'],heads=target['causal_heads'],
        noncausal_heads=target['noncausal_heads'],groups=groups,trigger_positions=trigger_positions,
        trigger_layers=trigger_layers,roi_positions=roi_positions,donor_q=donor_q,
        rescue_heads=rescue_heads,donor_hpre=donor_hpre,gain=gain)
    with patch:
        advance_streaming_state(model=model,state=state,token_ids=context[current:current+1],
                                 seed=1234,chunk_size=1,release_allocator_cache=True)
    invariance=cache_prefix_audit(root,state) if validate else None
    current_logits=state.last_logits.float()
    lp=torch.log_softmax(current_logits,dim=-1)
    entropy=float(-(lp.exp()*lp).sum().item())
    for left,right in partition:
        if left>=current+1:
            if state.generated_length!=left: raise RuntimeError('Unmatched continuation partition')
            advance_streaming_state(model=model,state=state,token_ids=context[left:right],
                                    seed=1234,chunk_size=2048,release_allocator_cache=True)
    score=score_preference_from_streaming_state(model=model,state=state,original_suffix_ids=original_suffix,
                                               counterfactual_suffix_ids=counterfactual_suffix,seed=1234)
    public={**score,'rds':patch.routing['causal']['RDS_T_vs_M'],'routing':patch.routing,
        'current_query_entropy':entropy,'candidate_nll':{'original':-score['L_o'],'counterfactual':-score['L_c']},
        'current_query_residual_norm':float(patch.hpre.float().norm().item()),
        'layer_norms':patch.norms,'source_audits':patch.audits,'q_patch_audit':patch.q_audit,
        'hpre_patch_audit':patch.hpre_audit,'past_cache_audit':invariance,
        'current_generated_index_zero_based':current,'absolute_current_query':root.prompt_length+current,
        'partition':partition,'trigger_positions':list(trigger_positions),'trigger_layers':list(trigger_layers),
        'roi_positions':list(roi_positions),'gain':gain}
    return public, {'q':patch.q,'hpre':patch.hpre}
