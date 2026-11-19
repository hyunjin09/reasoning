"""Finite, matched-wave vLLM worker; only runs inside a registered Slurm job."""
import argparse
import hashlib
import importlib.metadata
import os
import socket
import sys
import time
import traceback
from scripts.stage14cv.common import *
from scripts.stage14cv.control import wave_groups
from scripts.stage14cv.operational_v2 import authorize_v2, output_folder, completed_receipt, admit_wave, slurm_deadline, approval
from scripts.stage14cv.call_budget import reserve
from scripts.stage14c.input_adapter import prepare


def run(path,expected):
    start=time.monotonic();job=os.environ['SLURM_JOB_ID'];node=socket.gethostname().split('.')[0]
    assert node in ALLOWED_NODES and sha(path)==expected
    m=load(path);authorize_v2(m);cfg=load(ROOT/'spec/frozen_model_recipe.json');model=m['model_key'];mc=cfg['models'][model]
    dest=ROOT/'audit/workers'/job/'engines'/m['engine_id']
    active={};pending_id=None;phase='startup';completed=0;last_beat=0;beat=0
    deadline,slurm_info=slurm_deadline();durations=[]
    save(dest/'slurm_deadline.json',dict(at=now(),deadline_epoch=deadline,scontrol=slurm_info))
    try:
        for name,h in mc['model']['files_sha256'].items():
            p=Path(mc['model']['checkpoint'])/name
            assert p.resolve().is_relative_to(Path('/data/dataset')) and sha(p)==h,name
        import torch
        from vllm import LLM,SamplingParams
        from transformers import AutoProcessor
        sys.path.insert(0,str(Path('outputs/qwen3vl_official_eval/v1/sources/qwen/evaluation/MathVision').resolve()))
        from run_mathv import build_mathv_prompt,prepare_inputs_for_vllm
        assert torch.cuda.device_count()==1
        packages={p:importlib.metadata.version(p) for p in cfg['environment']};assert packages==cfg['environment']
        save(dest/'environment.json',dict(at=now(),job=job,node=node,gpu=torch.cuda.get_device_name(0),
            packages=packages,cuda=torch.version.cuda,model=mc['model'],manifest=str(path),manifest_sha256=expected))
        runtime=cfg['runtime'];proc=AutoProcessor.from_pretrained(mc['model']['checkpoint'])
        llm=LLM(model=mc['model']['checkpoint'],tensor_parallel_size=1,gpu_memory_utilization=runtime['gpu_memory_utilization'],
            trust_remote_code=True,max_model_len=runtime['max_model_len'],limit_mm_per_prompt={'image':10},
            seed=runtime['engine_seed'],max_num_seqs=18,dtype='bfloat16')
        engine=llm.llm_engine;assert str(engine.model_config.dtype)=='torch.bfloat16'
        save(dest/'ready.json',dict(at=now(),runtime=runtime,fixed_max_num_seqs=18,
            scheduling='Frozen wave membership; no refill until every active request finishes.',singleton=m.get('singleton',False)))
        done={t['task_id'] for t in m['rows'] if completed_receipt(t,m)}
        missing={t['task_id'] for t in m['rows'] if missing_path(t).exists()}
        groups=wave_groups(m['rows'],done,missing)
        if m.get('singleton'):groups=[[t] for group in groups for t in group]
        for group in groups:
            if (ROOT/'audit/STOP_BETWEEN_WAVES').exists() or not admit_wave(deadline-time.time(),model,m['panel'],durations):
                save(dest/'exit.json',dict(at=now(),complete=False,checkpoint=True,calls=completed,seconds=time.monotonic()-start,remaining_seconds=deadline-time.time(),prior_wave_seconds=durations));return
            assert not active
            wave_start=time.monotonic()
            for t in group:
                attempt=m['attempts'][t['task_id']];folder_path=output_folder(t,attempt,m)
                assert not folder_path.exists(),('Attempt collision',str(folder_path))
                phase='prepare';pending_id=t['task_id'];inp,messages=prepare(t,proc,build_mathv_prompt,prepare_inputs_for_vllm)
                assert inp['prompt'].endswith('<|im_start|>assistant\n'+('<think>\n' if model=='T' else ''))
                param=SamplingParams(**mc['recipe'],max_tokens=t['cap'],seed=t['seed'],stop_token_ids=[],ignore_eos=False)
                call_receipt=reserve(ROOT/'audit/call_reservations',t['panel'],t['task_id'],attempt,total_limit=approval()['max_total_calls'])
                save(folder_path/'input.json',dict(at=now(),task=t,task_sha256=fingerprint(t),chat_prompt=inp['prompt'],messages=messages,
                    image_present=bool(t['image_reference']),image_sha256=t['image_sha256'],sampling=repr(param),job=job,call_budget_receipt=str(call_receipt),
                    prepared_image_pixel_sha256=[hashlib.sha256(im.tobytes()).hexdigest() for im in inp.get('multi_modal_data',{}).get('image',[])],
                    prepared_image_sizes=[im.size for im in inp.get('multi_modal_data',{}).get('image',[])]))
                phase='add_request';engine.add_request(t['task_id'],inp,param)
                active[t['task_id']]=dict(task=t,started=time.monotonic(),latest=None);pending_id=None
            while active:
                phase='step'
                for output in engine.step():
                    state=active[output.request_id];state['latest']=output
                    if not output.finished:continue
                    t=state['task'];o=output.outputs[0];ids=list(o.token_ids);outdir=output_folder(t,m['attempts'][t['task_id']],m)
                    assert o.finish_reason in ('stop','length')
                    assert o.finish_reason!='length' or len(ids)==t['cap']
                    prompt_ids=list(output.prompt_token_ids);visual=sum(i==151655 for i in prompt_ids)
                    assert (visual>0)==bool(t['image_reference'])
                    assert len(prompt_ids)+len(ids)<=runtime['max_model_len']
                    save(outdir/'generation.json',dict(at=now(),task_id=t['task_id'],raw_decoded_response=o.text,
                        generated_token_ids=ids,tokens=len(ids),prompt_token_ids=prompt_ids,prompt_tokens=len(prompt_ids),
                        visual_tokens=visual,finish_reason=o.finish_reason,stop_reason=o.stop_reason,cap_hit=o.finish_reason=='length',
                        request_latency_seconds=time.monotonic()-state['started'],job=job,node=node,seed=t['seed'],
                        sampling=dict(mc['recipe'],max_tokens=t['cap']),task_sha256=fingerprint(t),
                        config_sha256=sha(ROOT/'spec/frozen_model_recipe.json'),manifest_sha256=expected))
                    save(outdir/'result.json',dict(at=now(),task_id=t['task_id'],task_sha256=fingerprint(t),job=job,
                        technical_context_only=t['task_id'] in m.get('context_ids',[]),input_sha256=sha(outdir/'input.json'),generation_sha256=sha(outdir/'generation.json')))
                    del active[t['task_id']];completed+=1
                    print('COMPLETE',t['task_id'],len(ids),o.finish_reason,flush=True)
                expired=[rid for rid,s in active.items() if time.monotonic()-s['started']>cfg['request_wall_seconds']]
                if expired:raise TimeoutError('Request wall limit: '+','.join(expired))
                if time.monotonic()-last_beat>=60:
                    save(dest/f'heartbeat_{beat:05d}.json',dict(at=now(),job=job,completed=completed,total=len(m['rows']),
                        active=[dict(task_id=rid,seconds=time.monotonic()-s['started'],tokens=len(s['latest'].outputs[0].token_ids) if s['latest'] else 0) for rid,s in active.items()],seconds=time.monotonic()-start))
                    beat+=1;last_beat=time.monotonic()
                    print('PROGRESS',completed,'active',len(active),flush=True)
            durations.append(time.monotonic()-wave_start)
        save(dest/'exit.json',dict(at=now(),complete=True,calls=completed,seconds=time.monotonic()-start,
            frontend_peak_cuda_allocated=torch.cuda.max_memory_allocated(),frontend_peak_cuda_reserved=torch.cuda.max_memory_reserved()))
    except BaseException as exc:
        save(dest/'failure.json',dict(at=now(),error=repr(exc),traceback=traceback.format_exc(),phase=phase,
            active_ids=list(active),pending_id=pending_id,completed=completed,seconds=time.monotonic()-start))
        raise


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('manifest');p.add_argument('--manifest-sha256',required=True)
    a=p.parse_args();run(a.manifest,a.manifest_sha256)
