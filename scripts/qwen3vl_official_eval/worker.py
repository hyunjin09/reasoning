"""Run pinned official inference; wrappers only filter cases and record evidence."""
import argparse
import hashlib
import importlib.metadata
import os
import socket
import subprocess
import sys
import time
import traceback
from pathlib import Path
from types import SimpleNamespace
from scripts.qwen3vl_official_eval.common import ROOT, ALLOWED_NODES, load, save, sha, now

def main(condition,manifest_sha):
    start=time.monotonic();job=os.environ['SLURM_JOB_ID'];host=socket.gethostname().split('.')[0]
    assert host in ALLOWED_NODES
    manifest_path=ROOT/'qwen3vl_official_sanity_manifest.json';assert sha(manifest_path)==manifest_sha
    m=load(manifest_path);assert m['frozen']
    for p,d in m['source_sha256'].items():assert sha(p)==d,p
    arm='thinking' if condition=='official_thinking' else 'instruct_direct'
    allowed={'official_instruct_direct','official_thinking'}|{x['name'] for x in m['ablations']}
    assert condition in allowed
    if not condition.startswith('official_'):
        assert load(ROOT/'audit/sanity_technical_gate.json')['instruct_gate_pass']
    info=m['models']['thinking' if arm=='thinking' else 'instruct']
    for name,d in info['files_sha256'].items():assert sha(Path(info['checkpoint'])/name)==d,name
    dest=ROOT/'workers'/job;outdir=ROOT/'results'/condition
    try:
        import torch
        assert torch.cuda.device_count()==1
        import vllm
        source=ROOT/'sources/qwen/evaluation/MathVision';sys.path.insert(0,str(source.resolve()))
        import run_mathv as official
        import pandas as pd
        rows=m['cases'];index={str(i):r for i,r in enumerate(rows)}
        # Bypass only full-dataset iteration/download. Questions and image paths are frozen canonical inputs.
        official.load_dataset=lambda dataset:pd.DataFrame([dict(index=r['index'],question=r['question'],image_path=r['image']) for r in rows])
        expected={(r['arm'],r['item_id']):r for r in load(ROOT/'audit/frozen_official_inputs.json')['rows']}
        recipe=dict(m['recipes'][arm])
        for variant in m['ablations']:
            if variant['name']==condition:recipe.update(variant['changes'])
        original_llm=official.LLM
        class RecordingLLM(original_llm):
            def __init__(self,**kwargs):
                save(dest/'llm_requested.json',dict(at=now(),kwargs=kwargs))
                super().__init__(**kwargs)
                config=self.llm_engine.model_config
                save(dest/'engine_ready.json',dict(at=now(),model=str(config.model),dtype=str(config.dtype),
                    max_model_len=config.max_model_len,engine_class=type(self.llm_engine).__name__,
                    vllm_version=vllm.__version__,cuda=torch.version.cuda))
            def generate(self,prompts,sampling_params,**kwargs):
                assert len(prompts)==12
                for r,p in zip(rows,prompts):
                    e=expected[(arm,r['item_id'])]
                    assert p['prompt']==e['chat_prompt']
                    assert [hashlib.sha256(im.tobytes()).hexdigest() for im in p['multi_modal_data']['image']]==e['prepared_image_pixel_sha256']
                    save(outdir/r['item_id']/'input.json',dict(at=now(),item_id=r['item_id'],family_id=r['family_id'],
                        prompt=p['prompt'],image_path=r['image'],image_sha256=sha(r['image']),
                        prepared_image_pixel_sha256=e['prepared_image_pixel_sha256'],recipe=recipe,
                        sampling_params_before_engine=repr(sampling_params),manifest_sha256=manifest_sha))
                save(dest/'generation_started.json',dict(at=now(),conditions=condition,calls=12))
                began=time.monotonic();original_step=self.llm_engine.step
                def recording_step(*args,**step_kwargs):
                    result=original_step(*args,**step_kwargs)
                    for out in result:
                        if not out.finished:continue
                        r=index[out.request_id];o=out.outputs[0];ids=list(o.token_ids)
                        receipt_path=outdir/r['item_id']/'result.json'
                        if receipt_path.exists():continue
                        record=dict(at=now(),condition=condition,arm=arm,item_id=r['item_id'],family_id=r['family_id'],
                            generated_token_ids=ids,raw_decoded_response=o.text,
                            official_final_response=str(o.text).split('</think>')[-1].strip(),tokens=len(ids),
                            prompt_token_count=len(out.prompt_token_ids),visual_tokens=sum(t==151655 for t in out.prompt_token_ids),
                            finish_reason=o.finish_reason,stop_reason=o.stop_reason,normal_eos_or_official_stop=o.finish_reason=='stop',
                            at_length_cap=o.finish_reason=='length' and len(ids)>=recipe['max_new_tokens'],
                            budget_interrupted=o.finish_reason not in ['stop','length'],
                            batch_request_latency_seconds=time.monotonic()-began,
                            request_metrics=vars(out.metrics) if out.metrics is not None else None,
                            slurm_job_id=job,node=host,manifest_sha256=manifest_sha,recipe=recipe)
                        assert record['visual_tokens']>0
                        save(outdir/r['item_id']/'generation.json',record)
                        save(receipt_path,dict(at=now(),generation_sha256=sha(outdir/r['item_id']/'generation.json'),
                            input_sha256=sha(outdir/r['item_id']/'input.json'),item_id=r['item_id'],condition=condition))
                        print('RECORDED',condition,r['item_id'],len(ids),o.finish_reason,flush=True)
                    return result
                self.llm_engine.step=recording_step
                outputs=super().generate(prompts,sampling_params=sampling_params,**kwargs)
                save(dest/'batch_timing.json',dict(at=now(),batch_seconds=time.monotonic()-began,n_calls=12))
                assert all((outdir/r['item_id']/'result.json').exists() for r in rows)
                return outputs
        official.LLM=RecordingLLM
        os.environ['LMUData']=str(Path(rows[0]['image']).parents[2])
        cfg=m['runtime']
        save(dest/'environment.json',dict(at=now(),condition=condition,node=host,slurm_job_id=job,
            packages={p:importlib.metadata.version(p) for p in m['environment']},cuda=torch.version.cuda,
            gpu=torch.cuda.get_device_name(0),gpu_total_memory=torch.cuda.get_device_properties(0).total_memory,
            nvidia_smi=subprocess.run(['nvidia-smi','--query-gpu=name,driver_version','--format=csv,noheader'],capture_output=True,text=True).stdout,
            manifest_sha256=manifest_sha))
        args=SimpleNamespace(model_path=info['checkpoint'],dataset='MathVision',num_samples=None,use_cot=False,cot_prompt='',
            output_file=str(dest/'official_predictions.jsonl'),tensor_parallel_size=1,
            gpu_memory_utilization=cfg['gpu_memory_utilization'],max_model_len=cfg['max_model_len'],
            max_images_per_prompt=cfg['max_images_per_prompt'],**recipe)
        official.run_inference(args)
        save(dest/'exit.json',dict(at=now(),complete=True,n_calls=12,condition=condition,elapsed_seconds=time.monotonic()-start))
    except BaseException as exc:
        save(dest/'failure.json',dict(at=now(),error=repr(exc),traceback=traceback.format_exc(),elapsed_seconds=time.monotonic()-start))
        raise

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('condition');p.add_argument('--manifest-sha256',required=True)
    a=p.parse_args();main(a.condition,a.manifest_sha256)
