"""One finite, hash-checked text-only queue per Slurm GPU; no retries."""
import argparse
import importlib.metadata
import os
import socket
import time
import traceback
from pathlib import Path
from scripts.stage12us.common import ROOT, ALLOWED_NODES, load, save, sha, now
from scripts.stage12us.protocol import authorize, render
from scripts.stage12ts.worker import fingerprint


def main(manifest_path, manifest_sha):
    start=time.monotonic(); job=os.environ['SLURM_JOB_ID']; node=socket.gethostname().split('.')[0]
    assert node in ALLOWED_NODES and sha(manifest_path)==manifest_sha
    manifest=load(manifest_path); authorize(manifest); cfg=load(ROOT/'config.json')
    for p,h in cfg['runtime_source_sha256'].items(): assert sha(p)==h,p
    arm=cfg['arms'][manifest['target']]; tasks=manifest['rows']; dest=ROOT/'workers'/job
    assert all(not (ROOT/'generations'/t['task_id']).exists() for t in tasks), 'No automatic retries'
    for name,h in arm['model']['files_sha256'].items():
        assert sha(Path(arm['model']['checkpoint'])/name)==h,name
    try:
        import torch
        from transformers import AutoProcessor
        from vllm import LLM, SamplingParams
        assert torch.cuda.device_count()==1
        save(dest/'environment.json',dict(at=now(),job=job,node=node,gpu=torch.cuda.get_device_name(0),
             total_gpu_memory=torch.cuda.get_device_properties(0).total_memory,cuda=torch.version.cuda,
             packages={p:importlib.metadata.version(p) for p in cfg['environment']},
             model=arm['model'],manifest=manifest_path,manifest_sha256=manifest_sha,config_sha256=sha(ROOT/'config.json')))
        proc=AutoProcessor.from_pretrained(arm['model']['checkpoint']); runtime=cfg['runtime']
        llm=LLM(model=arm['model']['checkpoint'],tensor_parallel_size=1,
                gpu_memory_utilization=runtime['gpu_memory_utilization'],trust_remote_code=True,
                max_model_len=runtime['max_model_len'],limit_mm_per_prompt={'image':0,'video':0},
                seed=runtime['engine_seed'],max_num_seqs=runtime['batch_size'])
        assert str(llm.llm_engine.model_config.dtype)=='torch.bfloat16'
        save(dest/'engine_ready.json',dict(at=now(),dtype=str(llm.llm_engine.model_config.dtype),runtime=runtime,calls=len(tasks)))
        original_step=llm.llm_engine.step; mapping={}; inputs_by_id={}; batch_start=0
        def step(*args,**kwargs):
            result=original_step(*args,**kwargs)
            for out in result:
                if not out.finished: continue
                task=mapping[out.request_id]; inp=inputs_by_id[task['task_id']]
                folder=ROOT/'generations'/task['task_id']; o=out.outputs[0]; ids=list(o.token_ids)
                assert list(out.prompt_token_ids)==inp['prompt_token_ids']
                assert o.finish_reason in ['stop','length']
                assert o.finish_reason!='length' or len(ids)==arm['cap']
                save(folder/'generation.json',dict(at=now(),task_id=task['task_id'],family_id=task['family_id'],
                     item_id=task['item_id'],target=task['target'],condition=task['condition'],replicate=task['replicate'],
                     raw_decoded_response=o.text,generated_token_ids=ids,tokens=len(ids),
                     prompt_tokens=len(out.prompt_token_ids),visual_tokens=0,
                     actual_prompt_token_ids=list(out.prompt_token_ids),
                     continuation_begins_at_token=len(out.prompt_token_ids),
                     finish_reason=o.finish_reason,stop_reason=o.stop_reason,cap_hit=o.finish_reason=='length',
                     request_latency_seconds=time.monotonic()-batch_start,job=job,node=node,seed=task['seed'],
                     sampling=dict(arm['recipe'],max_tokens=arm['cap']),task_sha256=fingerprint(task),
                     config_sha256=sha(ROOT/'config.json'),manifest_sha256=manifest_sha))
                save(folder/'result.json',dict(at=now(),task_id=task['task_id'],job=job,
                     task_sha256=fingerprint(task),generation_sha256=sha(folder/'generation.json'),input_sha256=sha(folder/'input.json')))
                print('COMPLETE',task['task_id'],'tokens',len(ids),o.finish_reason,flush=True)
            return result
        llm.llm_engine.step=step; count=0; timings=[]
        for offset in range(0,len(tasks),runtime['batch_size']):
            batch=tasks[offset:offset+runtime['batch_size']]; inputs=[]; params=[]
            for i,task in enumerate(batch):
                assert task['target']==manifest['target']
                text=Path(task['prefix_path']).read_text() if task['prefix_path'] else ''
                if task['prefix_path']: assert sha(task['prefix_path'])==task['prefix_sha256']
                inp=render(proc,task['question'],text,task['target'])
                assert len(inp['prompt_token_ids'])+arm['cap']<=runtime['max_model_len']
                param=SamplingParams(**arm['recipe'],max_tokens=arm['cap'],seed=task['seed'],stop_token_ids=[])
                save(ROOT/'generations'/task['task_id']/'input.json',dict(at=now(),task=task,**inp,sampling=repr(param)))
                inputs_by_id[task['task_id']]=inp;mapping[str(count+i)]=task
                inputs.append({'prompt_token_ids':inp['prompt_token_ids']});params.append(param)
            batch_start=time.monotonic()
            save(dest/f'batch_{offset}_started.json',dict(at=now(),tasks=[t['task_id'] for t in batch]))
            outputs=llm.generate(inputs,sampling_params=params)
            for task,out in zip(batch,outputs):
                assert load(ROOT/'generations'/task['task_id']/'generation.json')['raw_decoded_response']==out.outputs[0].text
            timings.append(dict(n=len(batch),seconds=time.monotonic()-batch_start));count+=len(batch)
        save(dest/'exit.json',dict(at=now(),complete=True,calls=count,batches=timings,seconds=time.monotonic()-start,
             peak_driver_memory_note='vLLM reserves90% VRAM; exact worker GPU name and capacity in environment receipt'))
    except BaseException as exc:
        save(dest/'failure.json',dict(at=now(),error=repr(exc),traceback=traceback.format_exc()));raise


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('manifest');p.add_argument('--manifest-sha256',required=True)
    a=p.parse_args();main(a.manifest,a.manifest_sha256)
