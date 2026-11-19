"""One Slurm GPU, immutable finite queue, exact token-step intervention receipts."""
import argparse,importlib.metadata,os,socket,time,traceback
from pathlib import Path
from scripts.stage13c.execution import *

def main(manifest_path,manifest_sha):
    start=time.monotonic();job=os.environ['SLURM_JOB_ID'];node=socket.gethostname().split('.')[0]
    assert node in ALLOWED_NODES and sha(manifest_path)==manifest_sha
    m=load(manifest_path);cfg_path=m.get('config_path',str(ROOT/'config.json'));cfg=load(cfg_path);dest=ROOT/'workers'/job;authorize(m)
    for p,h in cfg['source_sha256'].items():assert sha(p)==h,p
    tasks=[]
    for t in m['rows']:
        folder=ROOT/'generations'/t['task_id']
        if (folder/'result.json').exists():
            r=load(folder/'result.json');assert r['task_sha256']==fingerprint(t) and r['generation_sha256']==sha(folder/'generation.json')
        else:
            assert not folder.exists(),'Preserve partial attempt before explicit repair'
            tasks.append(t)
    assert tasks
    arm=cfg['models'][m['model_key']];info=arm['model']
    for name,h in info['files_sha256'].items():assert sha(Path(info['checkpoint'])/name)==h,name
    try:
        import torch
        from vllm import LLM,SamplingParams
        from transformers import AutoTokenizer
        assert torch.cuda.device_count()==1
        tok=AutoTokenizer.from_pretrained(info['checkpoint']);rt=cfg['runtime']
        save(dest/'environment.json',dict(at=now(),job=job,node=node,gpu=torch.cuda.get_device_name(0),
            packages={p:importlib.metadata.version(p) for p in cfg['environment']},model=info,
            manifest_path=manifest_path,manifest_sha256=manifest_sha,config_sha256=sha(cfg_path)))
        llm=LLM(model=info['checkpoint'],tensor_parallel_size=1,gpu_memory_utilization=rt['gpu_memory_utilization'],
            trust_remote_code=True,max_model_len=rt['max_model_len'],limit_mm_per_prompt={'image':0,'video':0},
            seed=rt['engine_seed'],max_num_seqs=rt['batch_size'],enable_prefix_caching=False,
            logits_processors=['scripts.stage13c.forcing:ForcedTrace'])
        assert str(llm.llm_engine.model_config.dtype)=='torch.bfloat16'
        save(dest/'engine_ready.json',dict(at=now(),dtype='bfloat16',runtime=rt,expected_calls=len(tasks),
            prefix_caching=False,speculative_decoding=False,forced_prefix_prefill=False))
        original_step=llm.llm_engine.step;mapping={};batch_start=0
        def step(*args,**kwargs):
            result=original_step(*args,**kwargs)
            for out in result:
                if not out.finished:continue
                t=mapping[out.request_id];folder=ROOT/'generations'/t['task_id'];o=out.outputs[0];ids=list(o.token_ids)
                assert o.finish_reason in ['stop','length']
                assert o.finish_reason!='length' or len(ids)==t['cap']
                raw=tok.decode(ids,skip_special_tokens=False)
                forced=t.get('forced_token_ids',[]);receipt=None
                if forced:
                    assert ids[:len(forced)]==forced
                    fp=folder/'forced_receipt.json';receipt=load(fp) if fp.exists() else None
                    assert receipt and receipt['forced_decoding_step_count']==len(forced)
                    assert t['open_id'] not in ids[len(forced):]
                g=dict(at=now(),task_id=t['task_id'],item_id=t['item_id'],family_id=t['family_id'],condition=t['condition'],
                    model_key=t['model_key'],phase=t['phase'],raw_decoded_response=raw,vllm_text=o.text,
                    generated_token_ids=ids,tokens=len(ids),prompt_token_ids=list(out.prompt_token_ids),
                    prompt_tokens=len(out.prompt_token_ids),visual_tokens=sum(x==151655 for x in out.prompt_token_ids),
                    finish_reason=o.finish_reason,stop_reason=o.stop_reason,cap_hit=o.finish_reason=='length',
                    normal_stop=o.finish_reason=='stop',request_latency_seconds=time.monotonic()-batch_start,
                    task_sha256=fingerprint(t),config_sha256=sha(cfg_path),manifest_sha256=manifest_sha,
                    job=job,node=node,seed=t['seed'],replicate=t['replicate'],sampling=dict(arm['recipe'],max_tokens=t['cap']),
                    forced_receipt_sha256=sha(folder/'forced_receipt.json') if receipt else None,
                    answer_text=tok.decode(ids[len(forced):],skip_special_tokens=True) if forced else None)
                assert g['visual_tokens']==0 and g['prompt_token_ids']==t['prompt_token_ids']
                assert g['prompt_tokens']+g['tokens']<rt['max_model_len']
                save(folder/'generation.json',g)
                save(folder/'result.json',dict(at=now(),task_id=t['task_id'],job=job,task_sha256=fingerprint(t),
                    generation_sha256=sha(folder/'generation.json'),input_sha256=sha(folder/'input.json')))
                print('COMPLETE',t['task_id'],'tokens',len(ids),o.finish_reason,flush=True)
            return result
        llm.llm_engine.step=step;counter=0;timings=[]
        for offset in range(0,len(tasks),rt['batch_size']):
            batch=tasks[offset:offset+rt['batch_size']];inputs=[];params=[]
            for i,t in enumerate(batch):
                folder=ROOT/'generations'/t['task_id'];extra={}
                if t.get('forced_token_ids'):
                    extra['stage13c_forced']=dict(ids=t['forced_token_ids'],reasoning_count=len(t['forced_token_ids'])-1,
                        close_id=t['close_id'],open_id=t['open_id'],receipt=str(folder/'forced_receipt.json'))
                param=SamplingParams(**arm['recipe'],max_tokens=t['cap'],seed=t['seed'],stop_token_ids=[],extra_args=extra)
                save(folder/'input.json',dict(at=now(),task=t,chat_prompt=t['chat_prompt'],image_present=False,
                    sampling=repr(param),task_sha256=fingerprint(t),forced_tokens_in_prefill=False))
                assert not set([151652,151653,151655,151656]).intersection(t['prompt_token_ids'])
                inputs.append(dict(prompt_token_ids=t['prompt_token_ids']));params.append(param);mapping[str(counter+i)]=t
            batch_start=time.monotonic();save(dest/f'batch_{offset}_started.json',dict(at=now(),tasks=[t['task_id'] for t in batch]))
            outputs=llm.generate(inputs,sampling_params=params)
            assert all((ROOT/'generations'/t['task_id']/'result.json').exists() for t in batch)
            timings.append(dict(n=len(batch),seconds=time.monotonic()-batch_start));counter+=len(batch)
        save(dest/'exit.json',dict(at=now(),complete=True,calls=len(tasks),batches=timings,seconds=time.monotonic()-start))
    except BaseException as exc:
        save(dest/'failure.json',dict(at=now(),error=repr(exc),traceback=traceback.format_exc()))
        raise

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('manifest');p.add_argument('--manifest-sha256',required=True)
    a=p.parse_args();main(a.manifest,a.manifest_sha256)
