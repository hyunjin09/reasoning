"""Eight technical FULL-only same-backend comparisons, before scientific R0."""
import os,traceback,gc
import torch
from scripts.stage9a5.common import ROOT,save,sha,now,tasks
from scripts.stage9a5.runtime import load_runtime,inputs,start,environment
from visual_reasoning.stage9a3.access import AccessMask


@torch.inference_mode()
def main():
    cfg,processor,model=load_runtime();save(ROOT/'audit/noop_environment.json',environment(model));paths=[]
    for row in tasks('technical'):
        prepared,meta=inputs(processor,model,row)
        a,oa=start(model,prepared,cfg['seed'],24,sample=False,logits=True)
        with AccessMask(backend='qwen3',visual=meta['visual'],prompt_length=meta['prompt_length'],layers=36,layer_cutoff=36,token_cutoff=None):
            b,ob=start(model,prepared,cfg['seed'],24,sample=False,logits=True)
        assert torch.equal(a.sequences,b.sequences)
        assert len(oa.logits)==len(ob.logits) and all(torch.equal(x,y) for x,y in zip(oa.logits,ob.logits))
        path=ROOT/'audit/noop'/f"{row['query_id']}.json"
        save(path,dict(at=now(),query_id=row['query_id'],pass_all=True,exact_tokens=True,exact_logits=True,input=meta));paths.append(path)
        print('NOOP_PASS',row['query_id'],flush=True)
        del a,b,oa,ob,prepared;gc.collect();torch.cuda.empty_cache()
    save(ROOT/'audit/full_noop_validation.json',dict(at=now(),pass_all=True,examples=8,config_sha256=sha(ROOT/'config.json'),
        checks_sha256={str(p):sha(p) for p in paths},source_sha256={p:sha(p) for p in ['scripts/stage9a5/noop.py','scripts/stage9a5/runtime.py']},
        slurm_job_id=os.environ['SLURM_JOB_ID']))


if __name__=='__main__':
    try:main()
    except Exception as e:
        save(ROOT/f'audit/noop_failure_{os.environ.get("SLURM_JOB_ID","local")}.json',dict(at=now(),error=repr(e),traceback=traceback.format_exc()));raise
