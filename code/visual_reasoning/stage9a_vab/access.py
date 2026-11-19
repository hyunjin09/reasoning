"""Restrict current query -> image keys; keep the existing cache and prefill."""
from contextlib import AbstractContextManager

import torch


def blocked_rows(layer, start, length, prompt_length, layer_cutoff, token_cutoff,
                 query_text=(), query_control=False):
    rows=[]
    for local,absolute in enumerate(range(start,start+length)):
        generated=absolute>=prompt_length
        temporal=token_cutoff is not None and absolute-prompt_length+1>token_cutoff
        if generated and (layer>=layer_cutoff or temporal):rows.append(local)
        elif query_control and layer>=layer_cutoff and absolute in query_text:rows.append(local)
    return rows


class AccessMask(AbstractContextManager):
    def __init__(self,*,visual,prompt_length,layer_cutoff,token_cutoff,mode='standard',
                 query_text=(),query_control=False,audit=False,enabled=True):
        if mode not in ('standard','null_sink'):raise ValueError(mode)
        assert 0<=layer_cutoff<=28 and (token_cutoff is None or token_cutoff>=0)
        assert visual and all(0<=i<prompt_length for i in visual)
        self.visual=tuple(visual);self.prompt_length=prompt_length
        self.layer_cutoff=layer_cutoff;self.token_cutoff=token_cutoff
        self.mode=mode;self.query_text=set(query_text);self.query_control=query_control
        self.audit=audit;self.enabled=enabled;self.records=[];self.original=None

    def forward(self,module,query,key,value,attention_mask,scaling,dropout=0.,**kwargs):
        from transformers.models.qwen3_vl import modeling_qwen3_vl as impl
        assert not module.training and dropout==0
        start=key.shape[-2]-query.shape[-2]
        rows=blocked_rows(module.layer_idx,start,query.shape[-2],self.prompt_length,
                          self.layer_cutoff,self.token_cutoff,self.query_text,self.query_control) if self.enabled else []
        extra={}
        if not rows:
            output,weights=self.original(module,query,key,value,attention_mask,scaling=scaling,dropout=dropout,**kwargs)
        elif self.mode=='standard':
            shape=(query.shape[0],1,query.shape[-2],key.shape[-2])
            mask=torch.zeros(shape,device=query.device,dtype=query.dtype) if attention_mask is None else attention_mask.expand(shape).clone()
            rr=torch.tensor(rows,device=query.device);vv=torch.tensor(self.visual,device=query.device)
            mask[...,rr[:,None],vv]=-torch.inf
            output,weights=self.original(module,query,key,value,mask,scaling=scaling,dropout=dropout,**kwargs)
        else:
            _,native_weights=self.original(module,query,key,value,attention_mask,scaling=scaling,dropout=dropout,**kwargs)
            weights=native_weights.clone()
            rr=torch.tensor(rows,device=query.device);vv=torch.tensor(self.visual,device=query.device)
            weights[...,rr[:,None],vv]=0
            output=torch.matmul(weights,impl.repeat_kv(value,module.num_key_value_groups)).transpose(1,2).contiguous()
            if self.audit:
                nonvisual=[i for i in range(key.shape[-2]) if i not in self.visual]
                extra=dict(real_nonvisual_probability_max_delta=float((weights[...,nonvisual]-native_weights[...,nonvisual]).abs().max()),
                           sink_mass_max=float(native_weights[...,rr[:,None],vv].float().sum(-1).max()))
        if self.audit:
            masked=float(weights[...,rows,:][...,self.visual].abs().max()) if rows else None
            if rows:assert masked==0
            self.records.append(dict(layer=module.layer_idx+1,query_start=start,query_length=query.shape[-2],
                blocked_absolute_queries=[start+i for i in rows],masked_image_probability_max=masked,**extra))
        return output,weights

    def __enter__(self):
        from transformers.models.qwen3_vl import modeling_qwen3_vl as impl
        self.original=impl.eager_attention_forward
        impl.eager_attention_forward=self.forward
        return self

    def __exit__(self,*exc):
        from transformers.models.qwen3_vl import modeling_qwen3_vl as impl
        impl.eager_attention_forward=self.original
        return False
