"""Finite, one-GPU evidence-probe queue; never launches additional experiments."""
import argparse, os, socket, time, traceback
from pathlib import Path
import torch
from scripts.stage11a.common import ROOT, OLD, load, save, sha, now
from visual_reasoning.stage0.modeling import load_runtime, runtime_environment, generate_once
from visual_reasoning.stage8b.v2_protocol import prepared_input, generation_parameters
from visual_reasoning.stage8a.protocol import termination_status

def claim(rows):
    for row in rows:
        p=ROOT/'probes/claims'/row['task_id']
        try:p.mkdir(parents=False)
        except FileExistsError:continue
        save(p/'owner.json',dict(at=now(),slurm_job_id=os.environ['SLURM_JOB_ID']))
        return row
    return None

def main(model_key,max_seconds):
    worker_started=time.monotonic()
    assert os.environ.get('SLURM_JOB_ID') and torch.cuda.device_count()==1
    assert socket.gethostname().split('.')[0] in ['node02','node03','node06','node07']
    cfg=load(ROOT/'probe_config.json');manifest=load(ROOT/'stage11a_probe_manifest.json')
    assert sha(ROOT/'stage11a_probe_manifest.json')==cfg['manifest_sha256']
    for p,h in cfg['source_sha256'].items():assert sha(p)==h,p
    for p,h in cfg['frozen_artifact_sha256'].items():assert sha(p)==h,p
    rows=[r for r in manifest['rows'] if r['model_key']==model_key]
    row=claim(rows)
    if row is None:return
    torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
    info=cfg['models'][model_key]
    for name,h in info['files_sha256'].items():assert sha(Path(info['checkpoint'])/name)==h,name
    proc,model=load_runtime(Path(info['checkpoint']),'cuda:0')
    assert str(next(model.parameters()).dtype)=='torch.bfloat16'
    env=runtime_environment(Path(info['checkpoint']),model,cfg['max_new_tokens'])
    env.update(at=now(),slurm_job_id=os.environ['SLURM_JOB_ID'],node=socket.gethostname(),revision=info['revision'],tf32=False,config_sha256=sha(ROOT/'probe_config.json'))
    save(ROOT/'probes/workers'/os.environ['SLURM_JOB_ID']/'environment.json',env)
    eos=model.generation_config.eos_token_id;eos=[eos] if isinstance(eos,int) else list(eos)
    while row is not None:
        dest=ROOT/'probes/results'/row['task_id'];started=time.monotonic()
        try:
            assert not dest.exists(),'No overwrite of partial or complete attempts'
            prepared,meta=prepared_input(proc,dict(row,answer=None))
            meta.pop('ground_truth_answer')
            original=load(OLD/'native/examples'/f"{row['arm']}_{row['item_id']}"/'input.json')
            assert meta['pixel_values_sha256']==original['pixel_values_sha256']
            assert meta['image_grid_thw']==original['image_grid_thw']
            ending='<|im_start|>assistant\n<think>\n' if row['arm']=='thinking' else '<|im_start|>assistant\n'
            assert meta['chat_prompt'].endswith(ending)
            save(dest/'input.json',meta)
            generated=generate_once(model,proc,prepared,cfg['max_new_tokens'],recorder=None,
                generation_kwargs=generation_parameters(),seed=row['seed'],collect_predictive_metrics=False)
            assert generated['incremental_decode_alignment']
            generated.pop('attention_arrays',None)
            status=termination_status(generated['generated_token_ids'],eos_ids=eos,cap=cfg['max_new_tokens'])
            save(dest/'generation.json',dict(generated,**status))
            save(dest/'result.json',dict(at=now(),task_id=row['task_id'],item_id=row['item_id'],arm=row['arm'],**status,
                seconds=time.monotonic()-started,config_sha256=sha(ROOT/'probe_config.json'),manifest_sha256=sha(ROOT/'stage11a_probe_manifest.json'),
                slurm_job_id=os.environ['SLURM_JOB_ID'],runtime=generated['runtime'],preprocessing_matches_native=True,
                generation_sha256=sha(dest/'generation.json'),input_sha256=sha(dest/'input.json')))
            print('COMPLETE',row['task_id'],'tokens',status['tokens'],'seconds',round(time.monotonic()-started,2),flush=True)
            del prepared,generated
        except Exception as exc:
            save(dest/'failure.json',dict(at=now(),error=repr(exc),traceback=traceback.format_exc(),slurm_job_id=os.environ['SLURM_JOB_ID']));raise
        if time.monotonic()-worker_started>=max_seconds:
            print('SAFE_WORKER_BUDGET_STOP',model_key,flush=True);return
        row=claim(rows)
    print('QUEUE_EXHAUSTED',model_key,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--model',required=True,choices=['instruct','thinking']);p.add_argument('--max-seconds',type=int,default=1200)
    args=p.parse_args();main(args.model,args.max_seconds)
