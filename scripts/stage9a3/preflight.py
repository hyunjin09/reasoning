"""Eight fixed actual-model V1–V6 validations and a length-only cap freeze."""
import argparse,gc,os,socket,time,traceback
import torch
from scripts.stage9a3.prepare import ROOT,load,save,sha,now
from scripts.stage9a3.runtime import load_runtime,inputs,generate,start,resume
from visual_reasoning.stage9a3.access import AccessMask,depth_count,blocked_rows
from visual_reasoning.stage0.modeling import _reset_generation_state
from scripts.stage9a3.validation_sequence import fixed_cache_sequence,needs_resume


@torch.inference_mode()
def check(key,cfg,model,processor,row):
    prepared,meta=inputs(processor,model,row);p=meta['prompt_length'];layers=model.config.text_config.num_hidden_layers
    args=dict(backend=key,visual=meta['visual'],prompt_length=p,layers=layers)
    begin=time.perf_counter()
    baseline,b=start(model,prepared,cfg['seed'],24,sample=False,logits=True)
    native=baseline.sequences[0,p:].tolist()
    fixed=fixed_cache_sequence(native,processor.tokenizer.encode(' Count the visible objects step by step.',add_special_tokens=False))
    with AccessMask(**args,layer_cutoff=layers,token_cutoff=None):
        sentinel,s=start(model,prepared,cfg['seed'],24,sample=False,logits=True)
    assert torch.equal(baseline.sequences,sentinel.sequences)
    assert all(torch.equal(x,y) for x,y in zip(b.logits,s.logits))
    first_logit=b.logits[0].clone();del baseline,b,sentinel,s
    audits=[]
    for frac,tc,mode in [(0,0,'standard'),(.5,4,'standard'),(.75,2,'standard'),(1,4,'standard'),(.5,4,'null_sink')]:
        lc=depth_count(frac,layers)
        with AccessMask(**args,layer_cutoff=lc,token_cutoff=tc,mode=mode,audit=True) as mask:
            _reset_generation_state(model,cfg['seed'])
            output=model(**prepared,use_cache=True,return_dict=True,logits_to_keep=1)
            assert torch.equal(output.logits[:,-1],first_logit),'Prefill differs from native generation'
            cache=output.past_key_values;rope=model.model.rope_deltas.clone();del output
            for i,token in enumerate(fixed):
                text=torch.tensor([[p+i]],device='cuda:0');vision=text[None].expand(3,-1,-1)+rope.reshape(1,1,1)
                positions=vision if key=='qwen25' else torch.cat([text[None],vision],dim=0)
                model.model.rope_deltas=rope.clone()
                output=model(input_ids=torch.tensor([[token]],device='cuda:0'),attention_mask=torch.ones(1,p+i+1,device='cuda:0',dtype=torch.long),
                             position_ids=positions,past_key_values=cache,use_cache=True,return_dict=True,logits_to_keep=1)
                cache=output.past_key_values;assert cache.get_seq_length()==p+i+1
                assert torch.isfinite(output.logits).all();del output
        assert {r['layer'] for r in mask.records}==set(range(layers))
        for r in mask.records:
            expected=blocked_rows(r['layer'],r['query_start'],r['query_length'],p,lc,tc)
            assert r['blocked_absolute_queries']==[r['query_start']+i for i in expected]
            if expected:assert r['masked_probability_max']==0
            if mode=='null_sink':assert r.get('nonvisual_probability_delta',0)==0
        audits.append(dict(fraction=frac,token_cutoff=tc,mode=mode,records=mask.records));del cache
    for lc,tc,prefix in [(layers,4,4),(depth_count(.5,layers),None,1)]:
        with AccessMask(**args,layer_cutoff=lc,token_cutoff=tc):
            whole,_=start(model,prepared,cfg['seed'],24,sample=False)
        base,_=start(model,prepared,cfg['seed'],prefix,sample=False)
        eos=model.generation_config.eos_token_id;eos=[eos] if isinstance(eos,int) else list(eos)
        if needs_resume(base.sequences[0,p:].tolist(),eos):
            with AccessMask(**args,layer_cutoff=lc,token_cutoff=tc):
                branch,_=resume(model,base,24-prefix,sample=False)
        else:branch=base
        assert torch.equal(whole.sequences,branch.sequences),'Cached continuation parity failed'
        del whole,base,branch
    technical=generate(model,processor,prepared,1024,cfg['seed'])
    return dict(query_id=row['query_id'],pass_all=True,input=meta,audits=audits,
        native_short_probe_tokens=native,fixed_cache_probe_tokens=fixed,teacher_forcing_padding=len(native)<8,
        V1_exact_noop_logits_tokens=True,V2_exact_zero_image_probability=True,V3_exact_prefill=True,
        V4_cached_continuation_parity=True,V5_all_layer_cutoffs=True,V6_generated_query_indexing=True,
        technical_full=technical,elapsed_seconds=time.perf_counter()-begin)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--model',choices=['qwen25','qwen3'],required=True)
    ap.add_argument('--then-full',action='store_true');args=ap.parse_args();key=args.model
    cfg,processor,model=load_runtime(key);rows=[r for r in load(ROOT/'audit/inference_tasks.json')['rows'] if r['split']=='technical'];assert len(rows)==8
    import transformers
    save(ROOT/f'audit/{key}_preflight_v2/environment.json',dict(at=now(),node=socket.gethostname(),slurm_job_id=os.environ['SLURM_JOB_ID'],
        torch_version=torch.__version__,transformers_version=transformers.__version__,gpu=torch.cuda.get_device_name(0),dtype=str(next(model.parameters()).dtype),
        language_layers=model.config.text_config.num_hidden_layers,model_revision=cfg['models'][key]['revision'],language_backend='eager',vision_backend='sdpa'))
    checks=[]
    for row in rows:
        print('CHECK_START',row['query_id'],now(),flush=True);result=check(key,cfg,model,processor,row)
        path=ROOT/f'audit/{key}_preflight_v2'/f"{row['query_id']}.json";save(path,result);checks.append((path,result))
        print('CHECK_PASS',row['query_id'],result['elapsed_seconds'],result['technical_full']['tokens'],flush=True);gc.collect();torch.cuda.empty_cache()
    full=[r['technical_full'] for _,r in checks];normal=[r['tokens'] for r in full if r['normal_eos']];assert normal,'No normally completed technical baseline'
    cap=2048 if any(r['at_length_cap'] for r in full) else next(x for x in (256,512,1024,2048) if x>=1.5*max(normal))
    if key=='qwen3':cap=load(ROOT/'stage9a3_mask_validation_qwen25.json')['scientific_cap']
    save(ROOT/f'stage9a3_mask_validation_{key}.json',dict(at=now(),model=key,pass_all=True,examples=8,scientific_cap=cap,
        checks_sha256={str(p):sha(p) for p,_ in checks},config_sha256=sha(ROOT/'config.json'),
        source_sha256={p:sha(p) for p in ['scripts/stage9a3/preflight.py','scripts/stage9a3/validation_sequence.py','scripts/stage9a3/runtime.py','code/visual_reasoning/stage9a3/access.py']},
        technical_tokens=sum(r['tokens'] for r in full),technical_generation_seconds=sum(r['runtime_seconds'] for r in full),slurm_job_id=os.environ['SLURM_JOB_ID']))
    print('PREFLIGHT_PASS',key,'cap',cap,flush=True)
    if args.then_full:
        from scripts.stage9a3.worker import run_queue
        run_queue(key,cfg,processor,model)


if __name__=='__main__':
    try:main()
    except Exception as exc:
        import sys
        key=sys.argv[sys.argv.index('--model')+1]
        save(ROOT/f'audit/{key}_preflight/failure_{os.environ.get("SLURM_JOB_ID","local")}.json',dict(at=now(),error=repr(exc),traceback=traceback.format_exc()))
        raise
