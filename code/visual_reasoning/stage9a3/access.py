"""Validated model-wide generated-query image-key rectangle for both backends."""
from contextlib import AbstractContextManager
import importlib
import math
import torch


def depth_count(fraction,layers):
    assert fraction in (0,.5,.75,1)
    return math.floor(fraction*layers)


def canonical(fraction,token):
    return (0,0) if fraction==0 or token==0 else (fraction,token)


def blocked_rows(layer,start,length,prompt_length,layer_cutoff,token_cutoff):
    return [i for i,absolute in enumerate(range(start,start+length)) if absolute>=prompt_length and
            (layer>=layer_cutoff or (token_cutoff is not None and absolute-prompt_length+1>token_cutoff))]


class AccessMask(AbstractContextManager):
    def __init__(self,*,backend,visual,prompt_length,layers,layer_cutoff,token_cutoff,mode='standard',audit=False):
        assert backend in ('qwen25','qwen3') and mode in ('standard','null_sink')
        assert 0<=layer_cutoff<=layers and (token_cutoff is None or token_cutoff>=0)
        assert visual and all(0<=v<prompt_length for v in visual)
        name='qwen2_5_vl' if backend=='qwen25' else 'qwen3_vl'
        self.impl=importlib.import_module(f'transformers.models.{name}.modeling_{name}')
        self.visual=tuple(visual);self.p=prompt_length;self.layers=layers;self.lc=layer_cutoff;self.tc=token_cutoff
        self.mode=mode;self.audit=audit;self.records=[];self.original=None

    def forward(self,module,query,key,value,attention_mask,scaling,dropout=0.,**kwargs):
        assert hasattr(module,'layer_idx'),'Vision must use SDPA; language alone uses patched eager'
        assert not module.training and dropout==0
        start=key.shape[-2]-query.shape[-2]
        rows=blocked_rows(module.layer_idx,start,query.shape[-2],self.p,self.lc,self.tc)
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
            _,native=self.original(module,query,key,value,attention_mask,scaling=scaling,dropout=dropout,**kwargs)
            weights=native.clone();rr=torch.tensor(rows,device=query.device);vv=torch.tensor(self.visual,device=query.device)
            weights[...,rr[:,None],vv]=0
            output=torch.matmul(weights,self.impl.repeat_kv(value,module.num_key_value_groups)).transpose(1,2).contiguous()
            if self.audit:
                others=[i for i in range(key.shape[-2]) if i not in self.visual]
                extra=dict(nonvisual_probability_delta=float((weights[...,others]-native[...,others]).abs().max()),
                           sink_mass_max=float(native[...,rr[:,None],vv].float().sum(-1).max()))
        if self.audit:
            maximum=float(weights[...,rows,:][...,self.visual].abs().max()) if rows else None
            if rows:assert maximum==0
            self.records.append(dict(layer=module.layer_idx,query_start=start,query_length=query.shape[-2],
                blocked_absolute_queries=[start+i for i in rows],masked_probability_max=maximum,
                image_probability_max=float(weights[...,self.visual].max()),**extra))
        return output,weights

    def __enter__(self):
        self.original=self.impl.eager_attention_forward
        self.impl.eager_attention_forward=self.forward
        return self

    def __exit__(self,*exc):
        self.impl.eager_attention_forward=self.original
        return False
