"""One finite technical engine; CUDA execution requires a registered Slurm job."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import socket
import sys
import time
import traceback
from scripts.stage14d.prepare_technical_v1 import ROOT,save,sha
from scripts.stage14d.technical_core_v1 import admit_call,exact_prefix
from scripts.stage14d.transport_v2 import control_message


def run(model,engine_index,deadline):
    started=time.monotonic();job=os.environ['SLURM_JOB_ID'];node=socket.gethostname().split('.')[0]
    assert model in 'IT' and engine_index in (0,1) and node in {'node02','node03','node06','node07'}
    release=json.loads((ROOT/'spec/technical_release_approved_v1.json').read_text())
    assert release['technical_calibration'] and release['max_allocated_gpu_hours']==2
    launch=json.loads((ROOT/'audit/technical_launches_v2'/f'job_{job}.json').read_text())
    assert launch['model']==model and launch['reserved_GPUh']==55/60
    seal=json.loads((ROOT/'audit/technical_execution_seal_v2.json').read_text())
    for p,h in seal['files'].items():assert sha(p)==h,p
    manifest=json.loads((ROOT/'spec/technical_calls_v1.json').read_text())
    for p,h in manifest['originals'].items():assert sha(p)==h,p
    rows=[r for r in manifest['rows'] if r['model']==model and ((r['repeat']=='repeat0')==(engine_index==0))]
    rows.sort(key=lambda t:(t['repeat']!='repeat1',t['role'],t['arm'],t['image_access']))
    dest=ROOT/'audit/technical_workers_v2'/job/f'engine_{engine_index}'
    active=None;phase='startup';done=0
    try:
        import torch
        from transformers import AutoProcessor
        from vllm import LLM,SamplingParams
        sys.path.insert(0,str(Path('outputs/qwen3vl_official_eval/v1/sources/qwen/evaluation/MathVision').resolve()))
        from run_mathv import build_mathv_prompt,prepare_inputs_for_vllm
        assert torch.cuda.device_count()==1
        cfg=json.loads((ROOT/'spec/pinned_model_revisions_and_recipes.json').read_text());mc=cfg['models'][model]
        packages={p:importlib.metadata.version(p) for p in cfg['environment']}
        assert packages==cfg['environment']
        for name,h in mc['model']['files_sha256'].items():assert sha(Path(mc['model']['checkpoint'])/name)==h,name
        save(dest/'environment.json',dict(job=job,node=node,model=model,packages=packages,
            GPU=torch.cuda.get_device_name(0),cuda=torch.version.cuda,model_revision=mc['model']['revision'],
            compiled_graphs=False,prefix_caching=False,max_num_seqs=18,active_requests=1,
            explanation='Eager execution instruments each attention call. Disable prefix-cache reuse so each matched input is freshly prefetched. Pinned vLLM/FlashAttention2 kernels, model, BF16, context and sampling remain. Not a historical hidden-state replay.'))
        proc=AutoProcessor.from_pretrained(mc['model']['checkpoint'],local_files_only=True)
        llm=LLM(model=mc['model']['checkpoint'],tensor_parallel_size=1,gpu_memory_utilization=.9,
            trust_remote_code=True,max_model_len=128000,limit_mm_per_prompt={'image':10},seed=42,
            max_num_seqs=18,dtype='bfloat16',enforce_eager=True,enable_prefix_caching=False,
            worker_extension_cls='scripts.stage14d.transport_v2.TechnicalExtension')
        save(dest/'ready.json',dict(job=job,startup_seconds=time.monotonic()-started,expected_calls=len(rows)))
        engine=llm.llm_engine
        for task in rows:
            if (ROOT/'audit/TECHNICAL_HOLD_v2.json').exists():
                raise RuntimeError('Peer technical failure: no further calls admitted')
            active=task['task_id'];phase='prepare'
            admitted={p.stem for p in (ROOT/'audit/technical_admissions_v1').glob('*.json')}
            admit_call(active,admitted,{r['task_id'] for r in manifest['rows']},24,deadline-time.time())
            parent=json.loads(Path(task['parent_input']).read_text());native=json.loads(Path(task['parent_generation']).read_text())
            question=parent['task']['prompt'];image=task['image']
            messages=build_mathv_prompt(dict(question=question),lambda _:image,'MathVision')
            prepared=prepare_inputs_for_vllm(messages,proc)
            assert prepared['prompt']==parent['chat_prompt'] and messages==parent['messages']
            sizes=[list(im.size) for im in prepared['multi_modal_data']['image']]
            pixels=[hashlib.sha256(im.tobytes()).hexdigest() for im in prepared['multi_modal_data']['image']]
            assert sizes==parent['prepared_image_sizes'] and pixels==parent['prepared_image_pixel_sha256']
            raw_chat_ids=proc.tokenizer.encode(prepared['prompt'],add_special_tokens=False)
            assert proc.tokenizer.decode(task['prefix_generated_token_ids'],skip_special_tokens=True)==task['prefix_text']
            assert proc.tokenizer.encode(task['directive'],add_special_tokens=False)==task['directive_ids']
            n=len(task['prefix_generated_token_ids'])
            assert task['prefix_generated_token_ids']==native['generated_token_ids'][:n]
            expected=exact_prefix(native['prompt_token_ids'],native['generated_token_ids'],n,task['directive_ids'])
            inp=dict(prompt_token_ids=exact_prefix(raw_chat_ids,native['generated_token_ids'],n,task['directive_ids']),
                multi_modal_data=prepared['multi_modal_data'],mm_processor_kwargs=prepared['mm_processor_kwargs'])
            image_positions=[i for i,v in enumerate(expected) if v==151655]
            assert image_positions and max(image_positions)<len(native['prompt_token_ids'])
            config=dict(task_id=active,prompt_len=len(expected),image_positions=image_positions,
                        off=task['image_access']=='OFF_FUTURE',expected_text_layers=36,
                        semantics='All36 language layers; only generated token queries. Full assistant directive prefill remains image-enabled; first sampled token uses unmasked final-prefill query.')
            rpc_method,rpc_args=control_message(config)
            llm.collective_rpc(rpc_method,args=rpc_args)
            outdir=ROOT/'raw/technical_v1'/active
            param=SamplingParams(**mc['recipe'],max_tokens=512,seed=task['seed'],stop_token_ids=[],ignore_eos=False)
            save(outdir/'input.json',dict(task=task,messages=messages,original_chat_prompt=prepared['prompt'],
                 unexpanded_input_ids=inp['prompt_token_ids'],expected_processed_input_ids=expected,
                 prepared_image_sizes=sizes,prepared_image_pixel_sha256=pixels,sampling=repr(param),
                 model_visible_metadata='None of stratum, gold, source reference or annotations supplied.',job=job))
            save(ROOT/'audit/technical_admissions_v1'/f'{active}.json',dict(task_id=active,job=job,at_epoch=time.time(),
                input_sha256=sha(outdir/'input.json'),manifest_sha256=sha(ROOT/'spec/technical_calls_v1.json')))
            phase='generation';call_start=time.monotonic();engine.add_request(active,inp,param)
            output=None
            while engine.has_unfinished_requests():
                for part in engine.step():
                    assert part.request_id==active
                    if part.finished:output=part
                if time.time()>deadline-60:raise TimeoutError('Technical allocation deadline guard')
            assert output is not None
            o=output.outputs[0];ids=list(o.token_ids)
            # Preserve raw evidence before any validation exception.
            save(outdir/'generation.json',dict(task_id=active,raw_decoded_response=o.text,
                generated_token_ids=ids,tokens=len(ids),prompt_token_ids=list(output.prompt_token_ids),
                prompt_tokens=len(output.prompt_token_ids),finish_reason=o.finish_reason,stop_reason=o.stop_reason,
                cap_hit=o.finish_reason=='length',seed=task['seed'],sampling=dict(mc['recipe'],max_tokens=512),
                request_seconds=time.monotonic()-call_start,job=job,node=node))
            audit=llm.collective_rpc('stage14d_collect')[0]
            save(outdir/'attention_audit.json',audit)
            assert list(output.prompt_token_ids)==expected,'Processed image/prefix/directive IDs differ'
            assert len(audit['layers'])==36 and o.finish_reason in ('length','stop')
            for record in audit['layers'].values():
                assert record['prefill_complete']
                if len(ids)>1:assert record.get('tested_dense_reference') and record['old_KV_preserved']
                if task['image_access']=='OFF_FUTURE' and len(ids)>1:
                    assert record['masked_queries']==len(ids)-1
                    assert record['first_masked_absolute_query']==len(expected)
                    assert record['image_attention_mass_max_head']==0
            if task['repeat']=='repeat1':
                previous=ROOT/'raw/technical_v1'/active.replace('repeat1','repeat0')/'generation.json'
                old=json.loads(previous.read_text());old_ids=old['generated_token_ids']
                exact=ids[:128]==old_ids[:128] and (min(len(ids),len(old_ids))>=128 or ids==old_ids)
                save(outdir/'repeat_validation.json',dict(first128_or_whole_short_exact=exact,whole_sequence_exact=ids==old_ids,
                    tokens=[len(old_ids),len(ids)],previous=str(previous)))
                assert exact,'Fixed-context fresh-engine replay failed; hold, do not retune'
            save(outdir/'result.json',dict(task_id=active,job=job,technical_checks_pass=True,
                 input_sha256=sha(outdir/'input.json'),generation_sha256=sha(outdir/'generation.json'),
                 attention_audit_sha256=sha(outdir/'attention_audit.json'),correctness_inspected=False))
            done+=1;print('COMPLETE',active,'tokens',len(ids),'seconds',round(time.monotonic()-call_start,2),flush=True)
            active=None
        save(dest/'exit.json',dict(calls=done,complete=True,seconds=time.monotonic()-started))
    except BaseException as exc:
        save(dest/'failure.json',dict(error=repr(exc),traceback=traceback.format_exc(),task_id=active,phase=phase,
             complete_calls=done,seconds=time.monotonic()-started))
        try:
            save(ROOT/'audit/TECHNICAL_HOLD_v2.json',dict(job=job,error=repr(exc),task_id=active,phase=phase))
        except FileExistsError:pass
        raise


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('model',choices=['I','T']);p.add_argument('engine',type=int)
    p.add_argument('--deadline',required=True,type=float);a=p.parse_args();run(a.model,a.engine,a.deadline)
