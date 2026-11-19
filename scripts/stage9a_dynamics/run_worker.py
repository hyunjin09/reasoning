"""Slurm worker: native-cache branches, complete masked continuations, receipts."""
import argparse
import gc
import json
import os
import socket
import time
import traceback
from collections import defaultdict
from pathlib import Path

import torch
from scripts.stage8c.prepare import save, sha
from scripts.stage9a.run_native import inputs, now
from visual_reasoning.stage0.modeling import load_runtime, runtime_environment, _incremental_decode_pieces
from visual_reasoning.stage8a.protocol import termination_status
from visual_reasoning.stage8b.single_execution import NativeProgress
from visual_reasoning.stage8b.v2_protocol import generation_parameters
from visual_reasoning.stage9a.protocol import ARMS, reasoning_span
from visual_reasoning.stage9a_dynamics.access import TemporalAccessMask
from visual_reasoning.stage9a_dynamics.generation import start, resume

ROOT=Path('outputs/stage9a_dynamics/v1')


class GracefulStop(Exception):
    """Requested stop at a completed-rollout boundary, never inside generation."""


def claim(rows, arm, worker):
    if (ROOT/'audit/STOP_WORKERS').exists():return None
    for row in rows:
        if row['arm']!=arm:continue
        dest=ROOT/'rollouts/claims'/row['task_id']
        try:dest.mkdir(parents=False)
        except FileExistsError:continue
        save(dest/'owner.json',dict(worker=worker,slurm_job_id=os.environ['SLURM_JOB_ID'],at=now()))
        return row
    return None


def run_task(model, processor, row, conditions, cfg, worker):
    task=row['task_id'];task_dir=ROOT/'rollouts/tasks'/task
    native=json.loads((Path(row['native_dir'])/'generation.json').read_text())['generated_token_ids']
    prepared,meta=inputs(processor,{k:v for k,v in row.items() if k not in ['native_dir']})
    native_meta=json.loads((Path(row['native_dir'])/'input.json').read_text())
    for key in ['prompt_token_count','visual_token_indices','pixel_values_sha256']:
        assert meta[key]==native_meta[key],key
    # A scheduler-timeout continuation may already have a verified input receipt.
    # Completed conditions remain immutable and are skipped below.
    if (task_dir/'input.json').exists():
        assert json.loads((task_dir/'input.json').read_text())==meta
    else:
        save(task_dir/'input.json',meta)
    p=meta['prompt_token_count'];visual=meta['visual_token_indices'];base=None
    unique={c['result_key']:c for c in conditions if c['execution']=='run'}
    pending=[c for c in unique.values() if not (ROOT/'rollouts/results'/c['result_key']/'result.json').exists()]
    pending.sort(key=lambda c:(min(lo for lo,hi in c['intervals']),c['result_key']))
    base_seconds=0.;eos=model.generation_config.eos_token_id;eos=[eos] if isinstance(eos,int) else list(eos)
    for c in pending:
        if (ROOT/'audit/STOP_WORKERS').exists():raise GracefulStop()
        dest=ROOT/'rollouts/results'/c['result_key'];begin=min(max(1,lo) for lo,hi in c['intervals'])
        assert 1<=begin<len(native)
        began=time.perf_counter()
        if base is None:
            with NativeProgress(model,task+':native_prefix'):
                base,out=start(model,prepared,row['seed'],begin)
            del out
        else:
            have=base.sequences.shape[1]-p
            assert have<=begin
            if have<begin:
                with NativeProgress(model,task+':native_prefix'):
                    base,out=resume(model,base,begin-have,copy_cache=False)
                del out
        base_seconds+=time.perf_counter()-began
        assert base.sequences[0,p:].tolist()==native[:begin],f'native prefix mismatch at {task}:{begin}'
        print(json.dumps(dict(event='condition_start',task_id=task,condition=c['condition_id'],result_key=c['result_key'],prefix_tokens=begin,at=now())),flush=True)
        torch.cuda.reset_peak_memory_stats();began=time.perf_counter()
        with TemporalAccessMask(visual=visual,prompt_length=p,intervals=c['intervals'],mode=c['mode']),NativeProgress(model,task+':'+c['condition_id']):
            branch,out=resume(model,base,cfg['max_new_tokens']-begin)
        seconds=time.perf_counter()-began;ids=branch.sequences[0,p:].tolist()
        assert ids[:begin]==native[:begin]
        status=termination_status(ids,eos_ids=eos,cap=cfg['max_new_tokens'])
        pieces,raw,aligned=_incremental_decode_pieces(processor.tokenizer,ids);assert aligned
        token_rows=[dict(token_index=i,token_id=token,decoded_token=piece,generation_position=p+i) for i,(token,piece) in enumerate(zip(ids,pieces))]
        span=reasoning_span(token_rows,row['arm'])
        completion=('normal completed' if status['normal_eos'] and (row['arm']!='thinking' or '</think>' in raw)
                    else 'capped' if status['at_length_cap'] else 'other abnormal stop')
        first=next((i for i,(a,b) in enumerate(zip(native,ids)) if a!=b),min(len(native),len(ids)) if len(native)!=len(ids) else None)
        save(dest/'generation.json',dict(generated_token_ids=ids,raw_decoded_response=raw,
            full_generated_response=processor.tokenizer.decode(ids,skip_special_tokens=True,clean_up_tokenization_spaces=False),
            reasoning_span=span,completion=completion,**status))
        result=dict(task_id=task,family_id=row['family_id'],arm=row['arm'],result_key=c['result_key'],
            representative_condition=c,worker=worker,at=now(),runtime_seconds=seconds,generated_suffix_tokens=len(ids)-begin,
            prefix_tokens=begin,prefix_identity_verified=True,first_divergence_token=first,identical_native=ids==native,
            reasoning_span=span,completion=completion,**status,peak_gpu_allocated_bytes=torch.cuda.max_memory_allocated(),
            generation_sha256=sha(dest/'generation.json'),config_sha256=sha(ROOT/'config.json'))
        save(dest/'result.json',result)
        with (ROOT/'rollouts/workers'/worker/'progress.jsonl').open('a') as stream:stream.write(json.dumps(result)+'\n')
        print(json.dumps(dict(event='condition_complete',task_id=task,condition=c['condition_id'],tokens=len(ids),seconds=seconds,at=now())),flush=True)
        del branch,out,ids,pieces,token_rows;gc.collect();torch.cuda.empty_cache()
    save(task_dir/'complete.json',dict(at=now(),task_id=task,worker=worker,conditions=len(conditions),unique_results=len(unique),
        shared_prefix_seconds=base_seconds,result_sha256={key:sha(ROOT/'rollouts/results'/key/'result.json') for key in unique},
        identity_conditions=[c['condition_id'] for c in conditions if c['execution']=='identity_native']))


def main():
    global ROOT
    ap=argparse.ArgumentParser();ap.add_argument('--preferred',choices=ARMS,default='thinking')
    ap.add_argument('--root',default=str(ROOT));args=ap.parse_args();ROOT=Path(args.root)
    assert os.environ.get('SLURM_JOB_ID') and torch.cuda.device_count()==1
    cfg=json.loads((ROOT/'config.json').read_text());assert socket.gethostname().split('.')[0] in cfg['allowed_nodes']
    gate=json.loads((ROOT/'stage9a_mask_backend_validation.json').read_text());assert gate['pass_all'] and gate['examples']==12
    for path,expected in gate['source_sha256'].items():assert sha(path)==expected,path
    for path,expected in cfg['source_sha256'].items():assert sha(path)==expected,path
    assert sha(ROOT/'audit/interventions.json')==cfg['manifest_sha256']
    assert sha(ROOT/'audit/tasks.json')==cfg['tasks_sha256'] and cfg['generation_parameters']==generation_parameters()
    for reuse in cfg.get('reused_results',[]):
        assert sha(reuse['receipt'])==reuse['receipt_sha256']
        assert sha(reuse['generation'])==reuse['generation_sha256']
    tasks=json.loads((ROOT/'audit/tasks.json').read_text())['rows'];conditions=defaultdict(list)
    for row in json.loads((ROOT/'audit/interventions.json').read_text())['rows']:conditions[row['task_id']].append(row)
    worker='slurm_'+os.environ['SLURM_JOB_ID'];wd=ROOT/'rollouts/workers'/worker;wd.mkdir(parents=True,exist_ok=True)
    (ROOT/'rollouts/claims').mkdir(parents=True,exist_ok=True)
    save(wd/'source.json',dict(at=now(),source_sha256={str(p):sha(p) for d in ['code/visual_reasoning/stage9a_dynamics','scripts/stage9a_dynamics'] for p in Path(d).glob('*.py')}))
    model=processor=None;current=None;completed=[]
    for arm in [args.preferred]+[a for a in ARMS if a!=args.preferred]:
        row=claim(tasks,arm,worker)
        if row is None:continue
        key='thinking' if arm=='thinking' else 'instruct'
        if current!=key:
            if model is not None:del model,processor;gc.collect();torch.cuda.empty_cache()
            checkpoint=Path(cfg['models'][key]['checkpoint'])
            for filename,expected in cfg['models'][key]['files_sha256'].items():assert sha(checkpoint/filename)==expected,filename
            processor,model=load_runtime(checkpoint,'cuda:0');current=key
            save(wd/(key+'_environment.json'),dict(runtime_environment(checkpoint,model,cfg['max_new_tokens']),
                at=now(),slurm_job_id=os.environ['SLURM_JOB_ID'],hostname=socket.gethostname(),config_sha256=sha(ROOT/'config.json')))
        while row is not None:
            try:run_task(model,processor,row,conditions[row['task_id']],cfg,worker)
            except GracefulStop:
                save(wd/'graceful_stop.json',dict(at=now(),task_id=row['task_id'],completed=completed,boundary='after durable rollout receipt, before next generation'))
                return
            except Exception as exc:
                save(wd/'failure.json',dict(at=now(),task_id=row['task_id'],error=repr(exc),traceback=traceback.format_exc()))
                raise
            completed.append(row['task_id']);row=claim(tasks,arm,worker)
    save(wd/'completed.json',dict(at=now(),completed=completed))


if __name__=='__main__':main()
