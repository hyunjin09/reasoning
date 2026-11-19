"""Finite immutable query queues; FULL is gated by technical validation only."""
import argparse,gc,os,socket,traceback
from collections import defaultdict
from pathlib import Path
from scripts.stage9a3.prepare import ROOT,load,save,sha,now
from scripts.stage9a3.runtime import load_runtime,inputs,generate
from visual_reasoning.stage9a3.access import AccessMask,depth_count
import torch


def run_queue(key,cfg,processor,model,stage='full',split='primary'):
    gate=load(ROOT/f'stage9a3_mask_validation_{key}.json');assert gate['pass_all']
    assert gate['config_sha256']==sha(ROOT/'config.json')
    for path,digest in gate['source_sha256'].items():assert sha(path)==digest
    if stage!='full':
        baseline=load(ROOT/f'stage9a3_{key}_full_access.json');assert baseline['gates']['pass']
        manifest=load(ROOT/f'audit/{key}_{stage}_{split}_manifest.json');assert manifest['frozen']
        assert manifest['config_sha256']==sha(ROOT/'config.json')
        for path,digest in manifest['source_sha256'].items():assert sha(path)==digest
        condition_rows=manifest['rows']
    else:
        condition_rows=[dict(query_id=r['query_id'],policy_id='full',fraction=1,token_cutoff=None,mode='standard',execution='run')
                        for r in load(ROOT/'audit/inference_tasks.json')['rows'] if r['split']==split]
    tasks={r['query_id']:r for r in load(ROOT/'audit/inference_tasks.json')['rows'] if r['split']==split}
    grouped=defaultdict(list)
    for r in condition_rows:
        if r['execution']=='run':grouped[r['query_id']].append(r)
    root=ROOT/key/f'{stage}_{split}';claims=root/'claims';claims.mkdir(parents=True,exist_ok=True)
    worker='slurm_'+os.environ['SLURM_JOB_ID'];done=[]
    import transformers
    save(root/'workers'/worker/'environment.json',dict(at=now(),node=socket.gethostname(),slurm_job_id=os.environ['SLURM_JOB_ID'],
        torch_version=torch.__version__,transformers_version=transformers.__version__,gpu=torch.cuda.get_device_name(0),
        dtype=str(next(model.parameters()).dtype),source_sha256=sha(__file__),config_sha256=sha(ROOT/'config.json')))
    for query,conditions in grouped.items():
        try:(claims/query).mkdir()
        except FileExistsError:continue
        save(claims/query/'owner.json',dict(worker=worker,at=now()))
        prepared,meta=inputs(processor,model,tasks[query]);layers=model.config.text_config.num_hidden_layers
        for c in conditions:
            dest=root/'results'/query/c['policy_id']
            assert not (dest/'result.json').exists()
            print('START',key,stage,query,c['policy_id'],now(),flush=True)
            with AccessMask(backend=key,visual=meta['visual'],prompt_length=meta['prompt_length'],layers=layers,
                            layer_cutoff=depth_count(c['fraction'],layers),token_cutoff=c['token_cutoff'],mode=c['mode']):
                output=generate(model,processor,prepared,gate['scientific_cap'],cfg['seed'])
            save(dest/'generation.json',output)
            save(dest/'result.json',dict(at=now(),query_id=query,image_id=tasks[query]['image_id'],model=key,stage=stage,split=split,
                policy=c,worker=worker,generation_sha256=sha(dest/'generation.json'),input=meta,tokens=output['tokens'],
                normal_eos=output['normal_eos'],at_length_cap=output['at_length_cap'],runtime_seconds=output['runtime_seconds'],
                peak_allocated_bytes=torch.cuda.max_memory_allocated(),peak_reserved_bytes=torch.cuda.max_memory_reserved(),
                scientific_cap=gate['scientific_cap'],config_sha256=sha(ROOT/'config.json')))
            print('COMPLETE',query,c['policy_id'],output['tokens'],round(output['runtime_seconds'],3),flush=True)
        save(root/'tasks'/query/'complete.json',dict(at=now(),worker=worker,query_id=query,conditions=len(conditions)))
        done.append(query);del prepared;gc.collect();torch.cuda.empty_cache()
    save(root/'workers'/worker/'complete.json',dict(at=now(),queries=done,stage=stage,split=split))


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--model',choices=['qwen25','qwen3'],required=True)
    ap.add_argument('--stage',choices=['full','grid','sink'],default='full');ap.add_argument('--split',choices=['primary','reserve'],default='primary');args=ap.parse_args()
    cfg,processor,model=load_runtime(args.model);run_queue(args.model,cfg,processor,model,args.stage,args.split)


if __name__=='__main__':
    try:main()
    except Exception as exc:
        save(ROOT/f'audit/worker_failure_{os.environ.get("SLURM_JOB_ID","local")}.json',dict(at=now(),error=repr(exc),traceback=traceback.format_exc()))
        raise
