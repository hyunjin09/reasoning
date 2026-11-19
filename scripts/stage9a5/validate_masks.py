"""Eight actual4B model-wide checks at the exact scientific time boundaries."""
import os,gc,time,traceback
import torch
from scripts.stage9a5.common import ROOT,load,save,sha,now,tasks
from scripts.stage9a5.runtime import load_runtime,inputs,start,resume,environment
from scripts.stage9a3.validation_sequence import needs_resume
from visual_reasoning.stage9a3.access import AccessMask,blocked_rows
from visual_reasoning.stage0.modeling import _reset_generation_state


@torch.inference_mode()
def main():
    assert load(ROOT/'stage9a5_thinking_full_baseline.json')['gates']['pass']
    cfg,processor,model=load_runtime();save(ROOT/'audit/mask_environment.json',environment(model));paths=[]
    for row in tasks('technical'):
        begin=time.perf_counter();prepared,meta=inputs(processor,model,row);p=meta['prompt_length']
        args=dict(backend='qwen3',visual=meta['visual'],prompt_length=p,layers=36,layer_cutoff=36)
        native,out=start(model,prepared,cfg['seed'],24,sample=False,logits=True)
        first=out.logits[0].clone();tokens=native.sequences[0,p:].tolist()
        eos=model.generation_config.eos_token_id;eos=[eos] if isinstance(eos,int) else list(eos)
        fixed=[t for t in tokens if t not in eos]
        filler=processor.tokenizer.encode(' Count the visible objects step by step.',add_special_tokens=False)
        fixed=(fixed+filler*258)[:257];del native,out
        audits=[]
        for cutoff,mode in [(0,'standard'),(64,'standard'),(128,'standard'),(256,'standard'),(64,'null_sink')]:
            _reset_generation_state(model,cfg['seed'])
            with AccessMask(**args,token_cutoff=cutoff,mode=mode,audit=True) as mask:
                out=model(**prepared,use_cache=True,return_dict=True,logits_to_keep=1)
                assert torch.equal(out.logits[:,-1],first),'Prefill changed'
                cache=out.past_key_values;rope=model.model.rope_deltas.clone();del out
                text=torch.arange(p,p+257,device='cuda:0').reshape(1,-1)
                vision=text[None].expand(3,-1,-1)+rope.reshape(1,1,1)
                out=model(input_ids=torch.tensor([fixed],device='cuda:0'),position_ids=torch.cat([text[None],vision]),
                    attention_mask=torch.ones(1,p+257,device='cuda:0',dtype=torch.long),past_key_values=cache,
                    use_cache=True,return_dict=True,logits_to_keep=1)
                assert out.past_key_values.get_seq_length()==p+257 and torch.isfinite(out.logits).all()
                next_id=out.logits[:,-1].argmax(-1).reshape(1,1);cache=out.past_key_values;del out
                # One genuine autoregressive cached query beyond the last tested boundary.
                text=torch.tensor([[p+257]],device='cuda:0');vision=text[None].expand(3,-1,-1)+rope.reshape(1,1,1)
                out=model(input_ids=next_id,position_ids=torch.cat([text[None],vision]),past_key_values=cache,
                    attention_mask=torch.ones(1,p+258,device='cuda:0',dtype=torch.long),use_cache=True,return_dict=True,logits_to_keep=1)
                assert out.past_key_values.get_seq_length()==p+258 and torch.isfinite(out.logits).all();del out,cache
            assert {r['layer'] for r in mask.records}==set(range(36))
            for r in mask.records:
                expected=blocked_rows(r['layer'],r['query_start'],r['query_length'],p,36,cutoff)
                assert r['blocked_absolute_queries']==[r['query_start']+i for i in expected]
                if expected:assert r['masked_probability_max']==0
                if mode=='null_sink':assert r.get('nonvisual_probability_delta',0)==0
            generated=[r for r in mask.records if r['query_start']==p]
            assert len(generated)==36 and all(r['blocked_absolute_queries']==list(range(p+cutoff,p+257)) for r in generated)
            audits.append(dict(cutoff=cutoff,mode=mode,records=mask.records))
        # Native greedy continuation equality at the token64 boundary, respecting EOS.
        with AccessMask(**args,token_cutoff=64):whole,_=start(model,prepared,cfg['seed'],80,sample=False)
        base,_=start(model,prepared,cfg['seed'],65,sample=False)
        active=needs_resume(base.sequences[0,p:].tolist(),eos)
        if active:
            with AccessMask(**args,token_cutoff=64):branch,_=resume(model,base,15,sample=False)
        else:branch=base
        assert torch.equal(whole.sequences,branch.sequences)
        path=ROOT/'audit/masks'/f"{row['query_id']}.json"
        save(path,dict(at=now(),query_id=row['query_id'],pass_all=True,input=meta,audits=audits,
            teacher_forcing_only=True,fixed_tokens=fixed,native_cached_branch_exercised=active,
            V1_noop_receipt_sha256=sha(ROOT/'audit/noop'/f"{row['query_id']}.json"),
            V2_exact_zero=True,V3_prefill_unchanged=True,V4_cache_valid=True,V5_cutoffs=[64,128,256],V6_layers=36,
            elapsed_seconds=time.perf_counter()-begin))
        paths.append(path);print('MASK_PASS',row['query_id'],round(time.perf_counter()-begin,2),flush=True)
        del whole,base,branch,prepared;gc.collect();torch.cuda.empty_cache()
    source=['scripts/stage9a5/validate_masks.py','scripts/stage9a5/runtime.py','code/visual_reasoning/stage9a3/access.py']
    save(ROOT/'stage9a5_thinking_mask_validation.json',dict(at=now(),pass_all=True,examples=8,
        config_sha256=sha(ROOT/'config.json'),checks_sha256={str(p):sha(p) for p in paths},source_sha256={p:sha(p) for p in source},
        slurm_job_id=os.environ['SLURM_JOB_ID'],scientific_cap=512))


if __name__=='__main__':
    try:main()
    except Exception as e:
        save(ROOT/f'audit/mask_failure_{os.environ.get("SLURM_JOB_ID","local")}.json',dict(at=now(),error=repr(e),traceback=traceback.format_exc()));raise
