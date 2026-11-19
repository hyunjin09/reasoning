"""Versioned recovery worker: identical generation, per-task attempts and OOM context."""
import argparse
import hashlib
import importlib.metadata
import os
import socket
import time
import traceback
from pathlib import Path
from scripts.stage14c.common import *
from scripts.stage14c.oom_policy import verify_recovery, missing_path, mark_missing
from scripts.stage14c.input_adapter import prepare


def authorize(manifest):
    mode=manifest['mode'];assert mode in ('preflight','main')
    assert manifest['config_sha256']==sha(ROOT/'spec/model_and_recipe_identity.json')
    assert load(ROOT/'audit/g1_final_source_seal_v1.json')['status']=='G1_PASS'
    assert (ROOT/'audit/g0_user_approval_v1.json').exists()
    for p,h in load(ROOT/'audit/g2_execution_seal_v1.json')['files'].items():assert sha(p)==h,p
    expected={t['task_id']:t for t in all_tasks(mode)}
    assert len({t['task_id'] for t in manifest['rows']})==len(manifest['rows'])
    assert all(t==expected.get(t['task_id']) for t in manifest['rows'])
    assert {t['model_key'] for t in manifest['rows']}=={manifest['model_key']}
    if mode=='main':assert load(ROOT/'audit/preflight_validation.json')['pass']


def run(path,manifest_sha):
    start=time.monotonic();job=os.environ['SLURM_JOB_ID'];node=socket.gethostname().split('.')[0]
    assert node in ALLOWED_NODES and sha(path)==manifest_sha
    verify_recovery()
    m=load(path);authorize(m);cfg=load(ROOT/'spec/model_and_recipe_identity.json')
    dest=ROOT/'audit/workers'/job/'engines'/m['engine_id'];model=m['model_key'];model_cfg=cfg['models'][model]
    tasks=[t for t in m['rows'] if checked_result(t) is None and not missing_path(t).exists()]
    if not tasks:
        save(dest/'exit.json',dict(at=now(),complete=True,calls=0,seconds=time.monotonic()-start));return
    def attempt(t):
        value=m['attempts'][t['task_id']];assert value in (0,1)
        return value
    for t in tasks:assert not result_dir(t,attempt(t)).exists(),('partial attempt requires versioned retry',t['task_id'])
    for name,h in model_cfg['model']['files_sha256'].items():assert sha(Path(model_cfg['model']['checkpoint'])/name)==h,name
    active={};completed=0;failures=0;cursor=0;last_heartbeat=0;heartbeat_index=0;pending_id=None;phase='startup'
    try:
        import sys
        import torch
        from vllm import LLM,SamplingParams
        from transformers import AutoProcessor
        sys.path.insert(0,str(Path('outputs/qwen3vl_official_eval/v1/sources/qwen/evaluation/MathVision').resolve()))
        from run_mathv import build_mathv_prompt,prepare_inputs_for_vllm
        assert torch.cuda.device_count()==1
        packages={p:importlib.metadata.version(p) for p in cfg['environment']}
        assert packages==cfg['environment'],packages
        save(dest/'environment.json',dict(at=now(),job=job,node=node,gpu=torch.cuda.get_device_name(0),
            total_gpu_memory=torch.cuda.get_device_properties(0).total_memory,cuda=torch.version.cuda,packages=packages,
            manifest=str(path),manifest_sha256=manifest_sha,config_sha256=sha(ROOT/'spec/model_and_recipe_identity.json'),model=model_cfg['model']))
        proc=AutoProcessor.from_pretrained(model_cfg['model']['checkpoint']);runtime=cfg['runtime']
        batch_size=m.get('batch_size',runtime['batch_size']);assert batch_size in (1,18)
        llm=LLM(model=model_cfg['model']['checkpoint'],tensor_parallel_size=1,gpu_memory_utilization=runtime['gpu_memory_utilization'],
            trust_remote_code=True,max_model_len=runtime['max_model_len'],limit_mm_per_prompt={'image':10},
            seed=runtime['engine_seed'],max_num_seqs=batch_size,dtype='bfloat16')
        engine=llm.llm_engine
        assert str(engine.model_config.dtype)=='torch.bfloat16'
        save(dest/'engine_ready.json',dict(at=now(),dtype=str(engine.model_config.dtype),batch_size=batch_size,
            runtime=runtime,expected_calls=len(tasks),scheduling='Continuously refill at most18 requests; native vLLM add_request/step, per-request fixed seed.'))
        while cursor<len(tasks) or active:
            while len(active)<batch_size and cursor<len(tasks):
                t=tasks[cursor];cursor+=1;pending_id=t['task_id'];phase='prepare';folder=result_dir(t,attempt(t))
                inp,messages=prepare(t,proc,build_mathv_prompt,prepare_inputs_for_vllm)
                assert inp['prompt'].endswith('<|im_start|>assistant\n'+('<think>\n' if model=='T' else ''))
                param=SamplingParams(**model_cfg['recipe'],max_tokens=t['cap'],seed=t['seed'],stop_token_ids=[],ignore_eos=False)
                save(folder/'input.json',dict(at=now(),task=t,task_sha256=fingerprint(t),chat_prompt=inp['prompt'],messages=messages,
                    image_present=bool(t['image_reference']),image_sha256=t['image_sha256'],sampling=repr(param),
                    prepared_image_pixel_sha256=[hashlib.sha256(im.tobytes()).hexdigest() for im in inp.get('multi_modal_data',{}).get('image',[])],
                    prepared_image_sizes=[im.size for im in inp.get('multi_modal_data',{}).get('image',[])],job=job))
                phase='add_request'
                engine.add_request(t['task_id'],inp,param)
                active[t['task_id']]=dict(task=t,started=time.monotonic(),latest=None)
                pending_id=None
            phase='step'
            for out in engine.step():
                a=active[out.request_id];a['latest']=out
                if not out.finished:continue
                t=a['task'];folder=result_dir(t,attempt(t));o=out.outputs[0];ids=list(o.token_ids)
                assert o.finish_reason in ('stop','length')
                assert o.finish_reason!='length' or len(ids)==t['cap']
                g=dict(at=now(),task_id=t['task_id'],raw_decoded_response=o.text,generated_token_ids=ids,tokens=len(ids),
                    prompt_token_ids=list(out.prompt_token_ids),prompt_tokens=len(out.prompt_token_ids),
                    visual_tokens=sum(i==151655 for i in out.prompt_token_ids),finish_reason=o.finish_reason,stop_reason=o.stop_reason,
                    cap_hit=o.finish_reason=='length',request_latency_seconds=time.monotonic()-a['started'],job=job,node=node,
                    seed=t['seed'],sampling=dict(model_cfg['recipe'],max_tokens=t['cap']),task_sha256=fingerprint(t),
                    config_sha256=sha(ROOT/'spec/model_and_recipe_identity.json'),manifest_sha256=manifest_sha)
                assert (g['visual_tokens']>0)==bool(t['image_reference'])
                assert g['prompt_tokens']+g['tokens']<=runtime['max_model_len']
                save(folder/'generation.json',g)
                save(folder/'result.json',dict(at=now(),task_id=t['task_id'],job=job,task_sha256=fingerprint(t),
                    generation_sha256=sha(folder/'generation.json'),input_sha256=sha(folder/'input.json')))
                del active[out.request_id];completed+=1
                print('COMPLETE',t['task_id'],'tokens',len(ids),o.finish_reason,flush=True)
            expired=[rid for rid,a in active.items() if time.monotonic()-a['started']>=cfg['request_wall_seconds']]
            if expired:
                engine.abort_request(expired)
                for rid in expired:
                    a=active.pop(rid);o=a['latest'].outputs[0] if a['latest'] else None
                    save(result_dir(a['task'],attempt(a['task']))/'technical_failure.json',dict(at=now(),reason='REQUEST_TIMEOUT',
                        job=job,task_sha256=fingerprint(a['task']),seconds=time.monotonic()-a['started'],
                        partial_response=o.text if o else None,partial_token_ids=list(o.token_ids) if o else []))
                    mark_missing(a['task'],'REQUEST_TIMEOUT',dict(job=job,attempt=attempt(a['task'])))
                    failures+=1
            if time.monotonic()-last_heartbeat>=60:
                snapshot=dict(at=now(),job=job,completed=completed,technical_failures=failures,total=len(tasks),submitted=cursor,
                    active=[dict(task_id=rid,seconds=time.monotonic()-a['started'],tokens=len(a['latest'].outputs[0].token_ids) if a['latest'] else 0) for rid,a in active.items()],
                    seconds=time.monotonic()-start)
                save(dest/f'heartbeat_{heartbeat_index:05d}.json',snapshot);heartbeat_index+=1;last_heartbeat=time.monotonic()
                print('PROGRESS',completed,'/',len(tasks),'active',len(active),flush=True)
        save(dest/'exit.json',dict(at=now(),complete=failures==0,calls=completed,technical_failures=failures,
            seconds=time.monotonic()-start,peak_cuda_allocated=torch.cuda.max_memory_allocated(),peak_cuda_reserved=torch.cuda.max_memory_reserved()))
    except BaseException as exc:
        save(dest/'failure.json',dict(at=now(),error=repr(exc),traceback=traceback.format_exc(),completed=completed,
            active_ids=list(active),pending_id=pending_id,phase=phase,seconds=time.monotonic()-start))
        raise

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('manifest');p.add_argument('--manifest-sha256',required=True)
    a=p.parse_args();run(a.manifest,a.manifest_sha256)
