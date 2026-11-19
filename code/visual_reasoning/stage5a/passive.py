"""Unmodified current-query late-layer telemetry with explicit optional sources."""
from contextlib import AbstractContextManager
from types import MethodType
import hashlib,math,re
import torch
from visual_reasoning.stage3b6.heads import _attention_module,_project_attention_output
from visual_reasoning.stage3c1.metrics import _repeat_kv
from visual_reasoning.stage3c3.runtime import _projection_parts,_run_attention
from visual_reasoning.stage3c9.streaming import clone_streaming_state,advance_streaming_state,score_preference_from_streaming_state
from visual_reasoning.stage4a.runtime import make_event_root,TELEMETRY_HEADS


def routing_summary(q,k,v,alpha,wo,scaling,kv_groups,groups):
    """Same BF16 dot/alpha-V definitions as historical telemetry, all32 heads."""
    q=q[0,:,0];k=_repeat_kv(k,kv_groups)[0];v=_repeat_kv(v,kv_groups)[0];a=alpha[0,:,0]
    h,d=q.shape;per=[{'logical_query_head':i,'groups':{}} for i in range(h)]
    post={};vectors={};aggregate={}
    for name,positions in groups.items():
        positions=sorted(set(positions));assert positions and min(positions)>=0 and max(positions)<a.shape[-1]
        kk=k[:,positions];vv=v[:,positions];aa=a[:,positions]
        dot=torch.matmul(kk,q[:,:,None]).squeeze(-1);scaled=dot*scaling
        cosine=dot.float()/(kk.float().norm(dim=-1)*q.float().norm(dim=-1)[:,None]).clamp_min(1e-30)
        av=(aa[:,:,None].to(vv.dtype)*vv).sum(1)
        # Per-head output contributions; no source term is applied to model state.
        projected=torch.stack([torch.nn.functional.linear(av[i].to(wo.dtype),wo[:,i*d:(i+1)*d]) for i in range(h)])
        post[name]=projected;vectors[name]=kk.float().mean(1)
        fields={'qk_cosine':cosine.mean(1),'raw_qk_dot':dot.float().mean(1),'scaled_logit':scaled.float().mean(1),
                'attention_mass':aa.float().sum(1),'attention_density':aa.float().mean(1),
                'alpha_v_norm':av.float().norm(dim=-1),'post_wo_norm':projected.float().norm(dim=-1)}
        values={key:t.detach().cpu().tolist() for key,t in fields.items()};av_cpu=av.float().cpu().tolist()
        for i in range(h):per[i]['groups'][name]={'token_count':len(positions),**{key:x[i] for key,x in values.items()},'alpha_v_vector':av_cpu[i]}
        aggregate[name]={'token_count':len(positions),**{'mean_'+key:sum(x)/h for key,x in values.items()},
                         'head_set_post_wo_sum_norm':float(projected.sum(0).float().norm().item())}
    ent=-(a.float().clamp_min(1e-30)*a.float().clamp_min(1e-30).log()).sum(-1)
    for i in range(h):per[i]['attention_entropy']=float(ent[i].item())
    cross={}
    if 'text_entity' in vectors:
        for name in ('T','M','X','text_control'):
            if name in vectors:
                x,y=vectors['text_entity'],vectors[name]
                cross['text_entity_key_cosine_to_'+name]=((x*y).sum(-1)/(x.norm(dim=-1)*y.norm(dim=-1)).clamp_min(1e-30)).cpu().tolist()
    return {'per_head':per,'groups':aggregate,'mean_attention_entropy':float(ent.mean().item()),
            'visible_source_token_count':int(a.shape[-1]),'text_visual_key_summary':cross,
            'all_values_finite':all(math.isfinite(x) for g in aggregate.values() for x in g.values())}


def entity_groups(tokenizer,meta,event,current):
    """Last exact native-token matches to reviewed named entities, descriptive."""
    prompt=meta['prompt_metadata']['prompt_token_ids'];history=event['history_before_ed_token_ids'][:current]
    ids=prompt+history;p=len(prompt);visible=set(meta['prompt_metadata']['visual_token_indices'])
    names=sorted(set(re.findall(r'(?<![A-Za-z])[A-Z]{1,4}(?![A-Za-z])',event['mentioned_visual_entity'])))
    matches=[]
    for name in names:
        for text in (name,' '+name):
            pattern=tokenizer.encode(text,add_special_tokens=False)
            if not pattern:continue
            for start in range(len(ids)-len(pattern)+1):
                if ids[start:start+len(pattern)]==pattern:
                    span=list(range(start,start+len(pattern)))
                    if not set(span)&visible:matches.extend(span)
    positions=sorted(set(matches))[-16:]
    if not positions:return {},{'status':'unavailable','rule':'no preceding exact token occurrence of a reviewed named entity'}
    control=[i for i in range(len(ids)-1,p-1,-1) if i not in positions][:len(positions)]
    groups={'text_entity':positions}
    if len(control)==len(positions):groups['text_control']=sorted(control)
    return groups,{'status':'exact_token_matches','names':names,'positions':positions,'control':'latest equally many other preceding reasoning tokens; descriptive position mismatch retained'}


class PassiveStep(AbstractContextManager):
    def __init__(self,model,absolute_query,groups):
        self.model=model;self.absolute_query=absolute_query;self.groups=groups;self.originals=[];self.handles=[]
        self.telemetry={};self.residual={};self.output_norms={}

    def _run(self,module,hidden_states,position_embeddings,attention_mask,past_key_values=None,**kwargs):
        assert hidden_states.shape[1]==1
        _,_,q,k,v=_projection_parts(module,hidden_states,position_embeddings)
        if past_key_values is not None:k,v=past_key_values.update(k,v,int(module.layer_idx))
        assert k.shape[2]-1==self.absolute_query
        native,alpha=_run_attention(module,q,k,v,attention_mask,kwargs)
        result=routing_summary(q,k,v,alpha,module.o_proj.weight,float(module.scaling),int(module.num_key_value_groups),self.groups)
        output=_project_attention_output(module,native,hidden_states)
        self.telemetry[str(module.layer_idx)]=result;self.output_norms[str(module.layer_idx)]=float(output.float().norm().item())
        return output,alpha

    def __enter__(self):
        for layer in (28,29):
            module=_attention_module(self.model,layer);self.originals.append((module,module.forward))
            def forward(module,hidden_states,position_embeddings,attention_mask,past_key_values=None,**kwargs):
                return self._run(module,hidden_states,position_embeddings,attention_mask,past_key_values,**kwargs)
            module.forward=MethodType(forward,module)
            def capture(module,args,index=layer):self.residual[str(index)]=float(args[0].float().norm().item())
            self.handles.append(self.model.model.language_model.layers[layer].register_forward_pre_hook(capture))
        return self

    def __exit__(self,*args):
        for m,old in self.originals:m.forward=old
        for h in self.handles:h.remove()


@torch.inference_mode()
def collect_event(model,processor,prefill,meta,event,*,prior=False):
    current=event['current_query_zero_based']-(8 if prior else 0)
    if current<0:return {'available':False,'reason':'t-minus8 precedes generated reasoning'}
    end=current+1;context=event['history_before_ed_token_ids'][:end]
    adjusted={**event,'candidate_start_token':end,'current_query_zero_based':current,'history_before_ed_token_ids':context}
    if end>=8:
        state=make_event_root(model,prefill,adjusted);start=end-8
    else:state=clone_streaming_state(prefill);start=0
    for i in range(start,current):advance_streaming_state(model=model,state=state,token_ids=[context[i]],seed=1234,chunk_size=1,release_allocator_cache=True)
    p=prefill.prompt_length
    groups={**event['source_groups'],'visual':meta['prompt_metadata']['visual_token_indices'],'sink':[0]}
    groups.pop('joint',None)
    groups['prompt_text']=[i for i in range(1,p) if i not in set(groups['visual'])]
    groups['reasoning']=list(range(p,p+current+1))
    if event['roi_aliases'].get('M')=='T':groups['M']=groups['T']
    if current:groups['R16']=list(range(p+max(0,current-16),p+current))
    texts,text_audit=entity_groups(processor.tokenizer,meta,event,current);groups.update(texts)
    with PassiveStep(model,p+current,groups) as capture:
        advance_streaming_state(model=model,state=state,token_ids=[context[current]],seed=1234,chunk_size=1,release_allocator_cache=True)
    assert set(capture.telemetry)=={'28','29'} and all(v['all_values_finite'] for v in capture.telemetry.values())
    logits=state.last_logits.float();lp=torch.log_softmax(logits,dim=-1)
    result={'available':True,'current_query_zero_based':current,'absolute_current_query':p+current,
        'groups':groups,'telemetry':capture.telemetry,'residual_norms':capture.residual,'attention_output_norms':capture.output_norms,
        'predictive_entropy':float(-(lp.exp()*lp).sum().item()),'current_logits_sha256':hashlib.sha256(logits.cpu().numpy().tobytes()).hexdigest(),
        'text_entity_audit':text_audit,'historical_selected_heads':TELEMETRY_HEADS,'selected_head_scope':'descriptive coordinates, not newly validated causal heads'}
    if not prior:result.update(score_preference_from_streaming_state(model=model,state=state,
        original_suffix_ids=event['original_divergent_suffix_ids'],counterfactual_suffix_ids=event['counterfactual_divergent_suffix_ids'],seed=1234))
    return result
