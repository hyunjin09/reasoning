"""Finite frozen Stage12C queues, one Slurm GPU; save each finished request."""
import argparse,hashlib,importlib.metadata,os,socket,sys,time,traceback
from pathlib import Path
from scripts.stage12c.common import ROOT,ALLOWED_NODES,load,save,sha,now
from scripts.stage12c.protocol import authorize_manifest

def fingerprint(task):
    import json
    return hashlib.sha256(json.dumps(task,sort_keys=True,ensure_ascii=False).encode()).hexdigest()

def main(manifest_path,manifest_sha):
    start=time.monotonic();job=os.environ['SLURM_JOB_ID'];node=socket.gethostname().split('.')[0]
    assert node in ALLOWED_NODES and sha(manifest_path)==manifest_sha
    m=load(manifest_path);cfg=load(ROOT/'config.json');dest=ROOT/'workers'/job
    assert m['config_sha256']==sha(ROOT/'config.json')
    for p,h in cfg['source_sha256'].items():assert sha(p)==h,p
    authorize_manifest(m)
    arm_cfg=cfg['arms'][m['arm']]
    tasks=[]
    for task in m['rows']:
        assert task['arm']==m['arm'] and task['cap']==arm_cfg['cap']
        folder=ROOT/'generations'/task['task_id']
        if (folder/'result.json').exists():
            r=load(folder/'result.json');assert r['task_sha256']==fingerprint(task) and r['generation_sha256']==sha(folder/'generation.json')
        else:
            assert not folder.exists(),'Preserve partial attempt before explicit repair'
            tasks.append(task)
    assert tasks
    info=arm_cfg['model']
    for name,h in info['files_sha256'].items():assert sha(Path(info['checkpoint'])/name)==h,name
    try:
        import torch
        from vllm import LLM,SamplingParams
        from transformers import AutoProcessor
        assert torch.cuda.device_count()==1
        sys.path.insert(0,str(Path('outputs/qwen3vl_official_eval/v1/sources/qwen/evaluation/MathVision').resolve()))
        from run_mathv import build_mathv_prompt,prepare_inputs_for_vllm
        save(dest/'environment.json',dict(at=now(),job=job,node=node,gpu=torch.cuda.get_device_name(0),
            total_gpu_memory=torch.cuda.get_device_properties(0).total_memory,cuda=torch.version.cuda,
            packages={p:importlib.metadata.version(p) for p in cfg['environment']},model=info,
            manifest_path=manifest_path,manifest_sha256=manifest_sha,config_sha256=sha(ROOT/'config.json')))
        proc=AutoProcessor.from_pretrained(info['checkpoint']);runtime=cfg['runtime']
        llm=LLM(model=info['checkpoint'],tensor_parallel_size=1,gpu_memory_utilization=runtime['gpu_memory_utilization'],
            trust_remote_code=True,max_model_len=runtime['max_model_len'],limit_mm_per_prompt={'image':10},seed=runtime['engine_seed'],max_num_seqs=runtime['batch_size'])
        assert str(llm.llm_engine.model_config.dtype)=='torch.bfloat16'
        save(dest/'engine_ready.json',dict(at=now(),dtype=str(llm.llm_engine.model_config.dtype),
            runtime=runtime,expected_calls=len(tasks)))
        original_step=llm.llm_engine.step;mapping={};batch_start=0
        def step(*args,**kwargs):
            result=original_step(*args,**kwargs)
            for out in result:
                if not out.finished:continue
                task=mapping[out.request_id];folder=ROOT/'generations'/task['task_id'];o=out.outputs[0]
                ids=list(o.token_ids);assert o.finish_reason in ['stop','length']
                assert o.finish_reason!='length' or len(ids)==task['cap']
                g=dict(at=now(),task_id=task['task_id'],item_id=task['item_id'],family_id=task['family_id'],arm=task['arm'],
                    prompt_version=task['prompt_version'],raw_decoded_response=o.text,generated_token_ids=ids,tokens=len(ids),
                    prompt_tokens=len(out.prompt_token_ids),visual_tokens=sum(x==151655 for x in out.prompt_token_ids),
                    finish_reason=o.finish_reason,stop_reason=o.stop_reason,cap_hit=o.finish_reason=='length',
                    normal_stop=o.finish_reason=='stop',request_latency_seconds=time.monotonic()-batch_start,
                    task_sha256=fingerprint(task),config_sha256=sha(ROOT/'config.json'),manifest_sha256=manifest_sha,
                    job=job,node=node,seed=task['seed'],sampling=dict(arm_cfg['recipe'],max_tokens=task['cap']))
                assert g['visual_tokens']>0
                assert g['prompt_tokens']+g['tokens']<runtime['max_model_len']
                save(folder/'generation.json',g)
                save(folder/'result.json',dict(at=now(),task_id=task['task_id'],job=job,task_sha256=fingerprint(task),
                    generation_sha256=sha(folder/'generation.json'),input_sha256=sha(folder/'input.json')))
                print('COMPLETE',task['task_id'],'tokens',len(ids),o.finish_reason,flush=True)
            return result
        llm.llm_engine.step=step;request_counter=0;timings=[]
        for offset in range(0,len(tasks),runtime['batch_size']):
            batch=tasks[offset:offset+runtime['batch_size']];inputs=[];params=[]
            for i,task in enumerate(batch):
                assert sha(task['image'])==task['image_sha256']
                messages=build_mathv_prompt(dict(question=task['prompt']),lambda row:task['image'],'MathVision')
                inp=prepare_inputs_for_vllm(messages,proc)
                expected='<|im_start|>assistant\n' + ('<think>\n' if task['arm']=='T' else '')
                assert inp['prompt'].endswith(expected)
                param=SamplingParams(**arm_cfg['recipe'],max_tokens=task['cap'],seed=task['seed'],stop_token_ids=[])
                save(ROOT/'generations'/task['task_id']/'input.json',dict(at=now(),task=task,
                    chat_prompt=inp['prompt'],image_sha256=task['image_sha256'],image_present=True,messages=messages,
                    prepared_image_pixel_sha256=[hashlib.sha256(im.tobytes()).hexdigest() for im in inp.get('multi_modal_data',{}).get('image',[])],
                    sampling=repr(param),task_sha256=fingerprint(task)))
                inputs.append(inp);params.append(param);mapping[str(request_counter+i)]=task
            batch_start=time.monotonic()
            save(dest/f'batch_{offset}_started.json',dict(at=now(),tasks=[t['task_id'] for t in batch]))
            outputs=llm.generate(inputs,sampling_params=params)
            for task,out in zip(batch,outputs):
                assert load(ROOT/'generations'/task['task_id']/'generation.json')['raw_decoded_response']==out.outputs[0].text
            timings.append(dict(n=len(batch),seconds=time.monotonic()-batch_start));request_counter+=len(batch)
        save(dest/'exit.json',dict(at=now(),complete=True,calls=len(tasks),batches=timings,seconds=time.monotonic()-start))
    except BaseException as exc:
        save(dest/'failure.json',dict(at=now(),error=repr(exc),traceback=traceback.format_exc()))
        raise

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('manifest');p.add_argument('--manifest-sha256',required=True)
    a=p.parse_args();main(a.manifest,a.manifest_sha256)
