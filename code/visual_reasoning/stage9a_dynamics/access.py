"""Eager attention mask with frozen generated-query intervals and layer support."""
from contextlib import AbstractContextManager
import torch
from .protocol import LAYERS


def blocked_rows(layer,start,length,prompt_length,intervals):
    if layer not in LAYERS:return []
    return [i for i,absolute in enumerate(range(start,start+length))
            if absolute>=prompt_length and any(absolute-prompt_length+1>=lo and
               (hi is None or absolute-prompt_length+1<hi) for lo,hi in intervals)]


class TemporalAccessMask(AbstractContextManager):
    def __init__(self,*,visual,prompt_length,intervals,mode='standard',audit=False,query_text=()):
        assert mode in ('standard','null_sink')
        assert visual and all(0<=v<prompt_length for v in visual)
        assert all(lo>=0 and (hi is None or hi>=lo) for lo,hi in intervals)
        self.visual=tuple(visual);self.prompt_length=prompt_length;self.intervals=intervals
        self.mode=mode;self.audit=audit;self.records=[];self.query_text=set(query_text)

    def forward(self,module,query,key,value,attention_mask,scaling,dropout=0.,**kwargs):
        from transformers.models.qwen3_vl import modeling_qwen3_vl as impl
        assert not module.training and dropout==0
        start=key.shape[-2]-query.shape[-2]
        rows=blocked_rows(module.layer_idx,start,query.shape[-2],self.prompt_length,self.intervals)
        if self.query_text and module.layer_idx in LAYERS:
            rows=sorted(set(rows)|{i for i in range(query.shape[-2]) if start+i in self.query_text})
        extra={}
        if not rows:
            out,w=self.original(module,query,key,value,attention_mask,scaling=scaling,dropout=dropout,**kwargs)
        elif self.mode=='standard':
            shape=(query.shape[0],1,query.shape[-2],key.shape[-2])
            mask=torch.zeros(shape,device=query.device,dtype=query.dtype) if attention_mask is None else attention_mask.expand(shape).clone()
            rr=torch.tensor(rows,device=query.device);vv=torch.tensor(self.visual,device=query.device)
            mask[...,rr[:,None],vv]=-torch.inf
            out,w=self.original(module,query,key,value,mask,scaling=scaling,dropout=dropout,**kwargs)
        else:
            _,native=self.original(module,query,key,value,attention_mask,scaling=scaling,dropout=dropout,**kwargs)
            w=native.clone();rr=torch.tensor(rows,device=query.device);vv=torch.tensor(self.visual,device=query.device)
            w[...,rr[:,None],vv]=0
            out=torch.matmul(w,impl.repeat_kv(value,module.num_key_value_groups)).transpose(1,2).contiguous()
            if self.audit:
                nonvisual=[i for i in range(key.shape[-2]) if i not in self.visual]
                extra=dict(nonvisual_probability_max_delta=float((w[...,nonvisual]-native[...,nonvisual]).abs().max()),
                           sink_mass_max=float(native[...,rr[:,None],vv].float().sum(-1).max()))
        if self.audit and module.layer_idx in LAYERS:
            maximum=float(w[...,rows,:][...,self.visual].abs().max()) if rows else None
            if rows:assert maximum==0
            self.records.append(dict(layer=module.layer_idx,query_start=start,query_length=query.shape[-2],
                blocked_absolute_queries=[start+i for i in rows],masked_image_probability_max=maximum,
                unmasked_image_probability_max=float(w[...,self.visual].abs().max()) if not rows else None,**extra))
        return out,w

    def __enter__(self):
        from transformers.models.qwen3_vl import modeling_qwen3_vl as impl
        self.original=impl.eager_attention_forward;impl.eager_attention_forward=self.forward
        return self

    def __exit__(self,*exc):
        from transformers.models.qwen3_vl import modeling_qwen3_vl as impl
        impl.eager_attention_forward=self.original
        return False
