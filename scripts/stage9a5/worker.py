"""Finite immutable scientific queues; technical/baseline gates enforced."""
import argparse,os,gc,traceback
import torch
from scripts.stage9a5.common import ROOT,load,save,sha,now,tasks
from scripts.stage9a5.runtime import load_runtime,inputs,generate,environment
from visual_reasoning.stage9a3.access import AccessMask


def run(stage):
    manifest_path=ROOT/f'audit/{stage}_manifest.json';manifest=load(manifest_path)
    assert manifest['frozen'] and manifest['config_sha256']==sha(ROOT/'config.json')
    for p,d in manifest['source_sha256'].items():assert sha(p)==d,p
    noop=load(ROOT/'audit/full_noop_validation.json');assert noop['pass_all'] and noop['config_sha256']==sha(ROOT/'config.json')
    if stage!='full':
        assert load(ROOT/'stage9a5_thinking_full_baseline.json')['gates']['pass']
        validation=load(ROOT/'stage9a5_thinking_mask_validation.json');assert validation['pass_all']
        for p,d in validation['source_sha256'].items():assert sha(p)==d,p
    cfg,processor,model=load_runtime();root=ROOT/stage;sid=os.environ['SLURM_JOB_ID']
    save(root/'workers'/sid/'environment.json',environment(model))
    lookup={r['query_id']:r for split in ('primary','reserve') for r in tasks(split)};done=[]
    for r in manifest['rows']:
        if r['execution']!='run':continue
        task=r['query_id']+'_'+r['policy'];claim=root/'claims'/task
        claim.parent.mkdir(parents=True,exist_ok=True)
        try:claim.mkdir()
        except FileExistsError:continue
        save(claim/'owner.json',dict(at=now(),slurm_job_id=sid))
        prepared,meta=inputs(processor,model,lookup[r['query_id']]);dest=root/'results'/task
        print('START',task,now(),flush=True);torch.cuda.reset_peak_memory_stats()
        with AccessMask(backend='qwen3',visual=meta['visual'],prompt_length=meta['prompt_length'],layers=36,layer_cutoff=36,
                        token_cutoff=r['cutoff'],mode=r['mode']):
            g=generate(model,processor,prepared,cfg['max_new_tokens'],cfg['seed'])
        save(dest/'generation.json',g)
        save(dest/'result.json',dict(at=now(),query_id=r['query_id'],policy=r['policy'],slurm_job_id=sid,
            generation_sha256=sha(dest/'generation.json'),input=meta,manifest_sha256=sha(manifest_path),
            peak_allocated_bytes=torch.cuda.max_memory_allocated(),peak_reserved_bytes=torch.cuda.max_memory_reserved(),
            config_sha256=sha(ROOT/'config.json'),runtime_seconds=g['runtime_seconds']))
        done.append(task);print('COMPLETE',task,g['tokens'],round(g['runtime_seconds'],3),flush=True)
        del prepared;gc.collect();torch.cuda.empty_cache()
    save(root/'workers'/sid/'complete.json',dict(at=now(),tasks=done,stage=stage))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage');a=p.parse_args()
    try:run(a.stage)
    except Exception as e:
        save(ROOT/f'audit/worker_failure_{os.environ.get("SLURM_JOB_ID","local")}.json',dict(at=now(),error=repr(e),traceback=traceback.format_exc()));raise
