"""Narrow vLLM0.11 FlashAttention2 decode adapter, loaded only in Slurm workers.

No weights/packages are patched on disk. Prefill uses the original backend.
OFF compacts a read-only view of retained cached keys/values for a single
generated query. Original paged cache is retained, including visual entries.
"""
import hashlib
from scripts.stage14d.technical_core_v1 import kept_positions, block_decode

STATE = None
ORIGINAL = None


def configure_worker(worker, config):
    import torch
    from vllm.v1.attention.backends.flash_attn import FlashAttentionImpl
    global STATE, ORIGINAL
    assert torch.cuda.is_available()
    if ORIGINAL is None:
        ORIGINAL = FlashAttentionImpl.forward
        FlashAttentionImpl.forward = controlled_forward
    STATE = dict(config, layers={})
    return dict(config=config,installed=True,version='stage14d-technical-v1')


def collect_worker(worker):
    return STATE


def digest(tensor):
    return hashlib.sha256(tensor.contiguous().view(__import__('torch').uint8).cpu().numpy().tobytes()).hexdigest()


def gather_cache(kv_cache, metadata, positions):
    import torch
    p=torch.tensor(positions,dtype=torch.long,device=kv_cache.device)
    block_size=kv_cache.shape[2]
    physical=metadata.block_table[0,p//block_size].to(torch.long)
    return kv_cache[0,physical,p%block_size],kv_cache[1,physical,p%block_size]


def compact_flash(impl, query, keys, values):
    import torch
    from vllm.attention.utils.fa_utils import flash_attn_varlen_func
    device=query.device
    return flash_attn_varlen_func(q=query[:1],k=keys.contiguous(),v=values.contiguous(),
        max_seqlen_q=1,cu_seqlens_q=torch.tensor([0,1],device=device,dtype=torch.int32),
        max_seqlen_k=keys.shape[0],cu_seqlens_k=torch.tensor([0,keys.shape[0]],device=device,dtype=torch.int32),
        softmax_scale=impl.scale,causal=False,window_size=(-1,-1),softcap=0.,fa_version=2)


def dense_reference(impl, query, keys, values, image_positions, off):
    import torch
    k=keys.float().repeat_interleave(impl.num_queries_per_kv,dim=1)
    v=values.float().repeat_interleave(impl.num_queries_per_kv,dim=1)
    scores=torch.einsum('qhd,khd->hqk',query[:1].float(),k)*impl.scale
    if off:scores[:,:,image_positions]=-torch.inf
    weights=torch.softmax(scores,dim=-1)
    if off:assert weights[:,:,image_positions].count_nonzero().item()==0
    return torch.einsum('hqk,khd->qhd',weights,v),float(weights[:,:,image_positions].sum(-1).max().item())


def controlled_forward(self, layer, query, key, value, kv_cache, attn_metadata,
                       output=None, output_scale=None, output_block_scale=None):
    import torch
    from vllm.attention.utils.fa_utils import reshape_and_cache_flash
    original_args=(self,layer,query,key,value,kv_cache,attn_metadata,output,output_scale,output_block_scale)
    if STATE is None or attn_metadata is None:return ORIGINAL(*original_args)
    assert attn_metadata.query_start_loc.shape[0]==2,'Only one active request is authorized'
    assert self.vllm_flash_attn_version==2 and self.kv_cache_dtype in ('auto','bfloat16')
    assert self.alibi_slopes is None and self.sliding_window==(-1,-1)
    assert self.logits_soft_cap==0 and self.sinks is None and not attn_metadata.use_cascade
    assert output_scale is None and output_block_scale is None and output is not None
    seq_len=int(attn_metadata.seq_lens[0].item());qlen=attn_metadata.num_actual_tokens
    name=layer.layer_name
    record=STATE['layers'].setdefault(name,dict(prefill_calls=0,decode_calls=0,masked_queries=0))
    off=block_decode(qlen,seq_len,STATE['prompt_len'],STATE['off'])
    decoding=seq_len>STATE['prompt_len']
    if not decoding:
        record['prefill_calls']+=1
        result=ORIGINAL(*original_args)
        if seq_len==STATE['prompt_len']:
            k,v=gather_cache(kv_cache,attn_metadata,list(range(seq_len)))
            record['prefill_K_sha256']=digest(k);record['prefill_V_sha256']=digest(v)
            record['prefill_complete']=True
        return result
    assert qlen==1 and record.get('prefill_complete'),'Unvalidated prefill/decode boundary'
    record['decode_calls']+=1
    first=record['decode_calls']==1
    before=None
    if first:
        k0,v0=gather_cache(kv_cache,attn_metadata,list(range(STATE['prompt_len'])))
        before=(digest(k0),digest(v0))
        assert before==(record['prefill_K_sha256'],record['prefill_V_sha256'])
    if off:
        # Append only current K/V, exactly as the original backend does.
        reshape_and_cache_flash(key,value,kv_cache[0],kv_cache[1],attn_metadata.slot_mapping,
                                self.kv_cache_dtype,layer._k_scale,layer._v_scale)
        kept=kept_positions(seq_len,STATE['image_positions'])
        assert kept[-1]==seq_len-1 and len(kept)+len(STATE['image_positions'])==seq_len
        k,v=gather_cache(kv_cache,attn_metadata,kept)
        output[:1].copy_(compact_flash(self,query,k,v))
        result=output;record['masked_queries']+=1
        record.setdefault('first_masked_absolute_query',seq_len-1)
    else:result=ORIGINAL(*original_args)
    if first:
        old_k,old_v=gather_cache(kv_cache,attn_metadata,list(range(STATE['prompt_len'])))
        assert before==(digest(old_k),digest(old_v)),'Existing K/V was changed'
        all_k,all_v=gather_cache(kv_cache,attn_metadata,list(range(seq_len)))
        ref,mass=dense_reference(self,query,all_k,all_v,STATE['image_positions'],off)
        # Preregistered BF16 numerical tolerance, not an output/accuracy gate.
        err=float((output[:1].float()-ref).abs().max().item())
        torch.testing.assert_close(output[:1].float(),ref,rtol=.02,atol=.015625)
        unmasked_compact_error=None
        if not off:
            compact=compact_flash(self,query,all_k,all_v)
            unmasked_compact_error=float((output[:1].float()-compact.float()).abs().max().item())
            torch.testing.assert_close(output[:1].float(),compact.float(),rtol=.02,atol=.015625)
        record.update(first_decode_query=seq_len-1,old_KV_preserved=True,
            reference_max_abs_error=err,image_attention_mass_max_head=mass,
            unmasked_paged_vs_compact_max_abs_error=unmasked_compact_error,
            tested_dense_reference=True,removed_image_keys=len(STATE['image_positions']) if off else 0)
    return result
