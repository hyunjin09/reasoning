"""Observe exact native tensors; persist every reconstruction before gating.

This module is diagnostic only. It never substitutes a model output or cache.
FP32 references are explicitly named and cannot authorize scientific execution.
"""
import json
from contextlib import AbstractContextManager
from pathlib import Path

import torch
import torch.nn.functional as F

from .native_partition import full_axis_parts

LAYERS = (19,20,21,22)


def error_record(native, reconstructed):
    a,b = native.detach().float(), reconstructed.detach().float()
    delta = b-a
    flat = int(delta.abs().argmax())
    index = list(torch.unravel_index(torch.tensor(flat), delta.shape))
    relative = float(delta.norm()/a.norm().clamp_min(1e-12))
    absolute = float(delta.abs().max())
    return dict(native_norm=float(a.norm()), reconstructed_norm=float(b.norm()),
        relative_l2=relative, max_abs=absolute,
        largest_error_index=[int(x) for x in index],
        native_at_max=float(a.flatten()[flat]), reconstructed_at_max=float(b.flatten()[flat]),
        native_dtype=str(native.dtype), reconstructed_dtype=str(reconstructed.dtype),
        pass_bounds=relative<=.02 and absolute<=.125)


def source_partition(*, total, visual, valid):
    v=set(int(i) for i in visual);k=set(int(i) for i in valid)
    n=k-v
    return dict(total_kv_positions=int(total),valid_positions=sorted(k),visual_positions=sorted(v),
        nonvisual_positions=sorted(n),masked_positions=sorted(set(range(total))-k),
        overlap_count=len(v&n),uncovered_count=len(k-(v|n)),invalid_visual_count=len(v-k),
        valid_count=len(k),visual_count=len(v),nonvisual_count=len(n),
        pass_partition=not(v&n or k-(v|n) or v-k))


class DecompositionForensics(AbstractContextManager):
    def __init__(self,model,*,visual,prompt_length,path,item_id):
        self.model,self.visual,self.prompt_length=model,list(visual),prompt_length
        self.path,self.item_id=Path(path),item_id
        self.case,self.token_index=None,None
        self.rows,self.partitions,self.pending,self.residuals=[],{}, {},{}
        self.handles=[]

    def select(self,case,token_index):
        self.case,self.token_index=case,int(token_index)

    def __enter__(self):
        from transformers.models.qwen3_vl import modeling_qwen3_vl as impl
        self.impl,self.original=impl,impl.eager_attention_forward
        impl.eager_attention_forward=self.attention
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self.stream=self.path.open('x')
        for layer in LAYERS:
            module=self.model.model.language_model.layers[layer]
            self.handles.append(module.register_forward_pre_hook(self.residual_pre(layer),with_kwargs=True))
            self.handles.append(module.self_attn.o_proj.register_forward_hook(self.projected(layer)))
            self.handles.append(module.post_attention_layernorm.register_forward_pre_hook(self.residual_post(layer)))
        return self

    def residual_pre(self,layer):
        def hook(_module,args,kwargs):
            if self.case is not None:
                self.residuals[layer]=(args[0] if args else kwargs['hidden_states']).detach()
        return hook

    def attention(self,module,query,key,value,attention_mask,scaling,dropout=0.,**kwargs):
        result=self.original(module,query,key,value,attention_mask,scaling=scaling,dropout=dropout,**kwargs)
        layer=getattr(module,'layer_idx',None)
        if self.case is None or layer not in LAYERS:return result
        weights=result[1][0,:,-1,:]
        repeated=self.impl.repeat_kv(value,module.num_key_value_groups)[0]
        total=key.shape[-2]
        if attention_mask is None:valid=list(range(total))
        else:
            mask=attention_mask[0,0,-1,:]
            valid=torch.nonzero(mask if mask.dtype==torch.bool else mask>torch.finfo(mask.dtype).min/2).flatten().tolist()
        partition=source_partition(total=total,visual=self.visual,valid=valid)
        n=partition['nonvisual_positions']
        av=weights[:,self.visual].unsqueeze(1);an=weights[:,n].unsqueeze(1)
        cv,cn=full_axis_parts(weights,repeated,self.visual)
        native=result[0][0,-1]
        joined=(cv+cn)
        full=torch.matmul(weights.unsqueeze(1),repeated).squeeze(1)
        # Diagnostic references only; the production gain remains BF16.
        old_tf32=torch.backends.cuda.matmul.allow_tf32
        torch.backends.cuda.matmul.allow_tf32=False
        try:
            cv32=torch.matmul(av.float(),repeated[:,self.visual].float()).squeeze(1)
            cn32=torch.matmul(an.float(),repeated[:,n].float()).squeeze(1)
        finally:torch.backends.cuda.matmul.allow_tf32=old_tf32
        partition_id=f'{self.item_id}:{self.token_index}:{layer}'
        self.partitions[partition_id]=partition
        row=dict(item_id=self.item_id,case_id=self.case,token_index=self.token_index,layer=layer,
            partition_id=partition_id,valid_kv=partition['valid_count'],visual_count=partition['visual_count'],
            nonvisual_count=partition['nonvisual_count'],overlap_count=partition['overlap_count'],
            uncovered_count=partition['uncovered_count'],invalid_visual_count=partition['invalid_visual_count'],
            partition_pass=partition['pass_partition'],prompt_length=self.prompt_length,cache_positions=total,
            query_heads=query.shape[1],kv_heads=key.shape[1],gqa_factor=module.num_key_value_groups,
            q_to_kv=[i//module.num_key_value_groups for i in range(query.shape[1])],
            gqa_native_mapping_exact=torch.equal(repeated,value[0].repeat_interleave(module.num_key_value_groups,dim=0)),
            query_dtype=str(query.dtype),key_dtype=str(key.dtype),value_dtype=str(value.dtype),
            weights_dtype=str(weights.dtype),pre_output_dtype=str(native.dtype),scaling=float(scaling),
            mask_dtype=str(attention_mask.dtype) if attention_mask is not None else None,
            weights_origin='exact native eager returned probabilities; Q/K already rotary-applied and cache-updated',
            visual_pre_norm=float(cv.float().norm()),nonvisual_pre_norm=float(cn.float().norm()),
            pre_native_replay=error_record(native,full),
            pre_legacy=error_record(native,cv.float()+cn.float()),
            pre_bf16_sum=error_record(native,joined),
            pre_fp32_diagnostic=error_record(native,(cv32+cn32).to(native.dtype)),
            per_head=[error_record(native[h],joined[h]) for h in range(query.shape[1])],
            concatenation=error_record(native.flatten(),joined.flatten()),
            partition_kernel='full native KV axis; zero-masked exact BF16 weights',fp32_diagnostic_only=True,bf16_reduced_precision_reduction=torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction)
        self.pending[layer]=dict(row=row,cv=cv,cn=cn,native=native,joined=joined)
        return result

    def projected(self,layer):
        def hook(module,args,output):
            if layer not in self.pending:return
            d=self.pending[layer];row=d['row'];cv=d['cv'].flatten()[None,None,:];cn=d['cn'].flatten()[None,None,:]
            pv=F.linear(cv,module.weight,bias=None)
            pn=F.linear(cn,module.weight,bias=module.bias)
            joint=F.linear(d['joined'].flatten()[None,None,:],module.weight,bias=module.bias)
            native_reproject=F.linear(d['native'].flatten()[None,None,:],module.weight,bias=module.bias)
            row.update(projection_dtype=str(module.weight.dtype),bias_exists=module.bias is not None,
                bias_norm=float(module.bias.float().norm()) if module.bias is not None else 0.,
                bias_count=1 if module.bias is not None else 0,
                concat_native_exact=torch.equal(args[0][0,-1],d['native'].flatten()),
                post_native_reproject=error_record(output,native_reproject),
                post_legacy=error_record(output,pv.float()+pn.float()),
                post_bf16_separate=error_record(output,pv+pn),
                post_bf16_joint=error_record(output,joint),
                visual_post_norm=float(pv.float().norm()),nonvisual_post_norm=float(pn.float().norm()))
            d.update(pv=pv,pn=pn,joint=joint,native_projected=output.detach())
        return hook

    def residual_post(self,layer):
        def hook(_module,args):
            if layer not in self.pending:return
            d=self.pending.pop(layer);row=d['row'];before=self.residuals.pop(layer);native=args[0].detach()
            row.update(residual_dtype=str(native.dtype),residual_pre_norm=float(before.float().norm()),
                residual_native_replay=error_record(native,before+d['native_projected']),
                residual_separate=error_record(native,before+(d['pv']+d['pn'])),
                residual_left_associative=error_record(native,(before+d['pv'])+d['pn']),
                residual_joint=error_record(native,before+d['joint']))
            # No numerical assertion occurs before this flushed complete record.
            self.stream.write(json.dumps(row,allow_nan=False)+'\n');self.stream.flush()
            self.rows.append(row)
        return hook

    def __exit__(self,*exc):
        self.impl.eager_attention_forward=self.original
        for handle in self.handles:handle.remove()
        self.stream.close()
        return False
