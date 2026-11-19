"""One bounded old-item cache/throughput diagnostic, no scientific outcomes."""
import os,torch
from scripts.stage11b.common import ROOT,load,save,sha,now
from scripts.stage11b.generation import runtime,prepare,generate

assert os.environ.get('SLURM_JOB_ID') and torch.cuda.device_count()==1
torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
cfg=load(ROOT/'config.json');proc,model=runtime(cfg['models']['instruct'])
old=load('outputs/stage9a/v1/stage9a_cohort_manifest.json')['rows'][:4]
rows=[dict(r,arm='instruct_cot',task_id=f'cache_check_{r["item_id"]}',condition='native') for r in old]
batch,meta=prepare(proc,rows);calls=[]
def observe(module,args,kwargs):
    cache=kwargs.get('past_key_values')
    calls.append(dict(input_shape=list(kwargs['input_ids'].shape),cache_length=cache.get_seq_length() if cache is not None else None,
        pixels_present=kwargs.get('pixel_values') is not None,use_cache=kwargs.get('use_cache')))
hook=model.register_forward_pre_hook(observe,with_kwargs=True)
out=generate(proc,model,batch,256,max_time=180);hook.remove()
result=dict(at=now(),slurm_job_id=os.environ['SLURM_JOB_ID'],calls=calls,
    tokens=[r['tokens'] for r in out],batch_seconds=out[0]['batch_seconds'],
    peak_gpu_reserved_bytes=out[0]['peak_gpu_reserved_bytes'],
    incremental_cache_correct=len(calls)>1 and all(r['input_shape'][1]==1 and r['cache_length']>0 and not r['pixels_present'] for r in calls[1:]),
    no_discovery_outputs_opened=True,source_sha256=sha(__file__))
save(ROOT/'audit/cache_diagnostic.json',result)
print('CACHE_DIAGNOSTIC',result['incremental_cache_correct'],'seconds',result['batch_seconds'],'calls',len(calls),flush=True)
