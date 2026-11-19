"""Disjoint technical checks for multimodal forced-prefix recomputation."""
import os
import torch
from scripts.stage10a.common import ROOT,DATA,load,save,sha,now
from scripts.stage10a.runtime import load_runtime,inputs,start,resume,environment
from scripts.stage10a.image_text import fresh_image


@torch.inference_mode()
def main():
    mp=ROOT/'audit/dominance_manifest.json';m=load(mp)
    for p,d in m['source_sha256'].items():assert sha(p)==d,p
    cfg,processor,model=load_runtime();rows=[]
    source={r['query_id']:r for r in load(DATA/'stage9a3_synthetic_dataset_manifest.json')['queries']}
    for query in ('image048_color','image049_shape'):
        task={k:v for k,v in source[query].items() if k not in ('answer','count')}
        task['prompt']=task['prompt'].replace('Think step by step. You must write intermediate steps.\n','')
        prepared,meta=inputs(processor,model,task);native,_=start(model,prepared,cfg['seed'],16,sample=False)
        prefix=native.sequences[0,meta['prompt_length']:].tolist()
        branch,_=resume(model,native,16,sample=False)
        expected=branch.sequences[0,meta['prompt_length']:].tolist()
        g,details=fresh_image(processor,model,task,prefix,cfg['seed'],count=16)
        assert g['generated_token_ids']==expected,'Fresh image+native prefix differs from cached native continuation'
        assert native.cache.get_seq_length()==meta['prompt_length']+15
        assert details['input']['pixel_values_sha256']==meta['pixel_values_sha256']
        assert not details['original_cache_copied'] and details['image_state_recomputed_from_current_image']
        rows.append(dict(query_id=query,prefix_tokens=16,continuation_tokens=16,native_cache_unchanged=True,
            fresh_cached_tokens_exact=True,pixel_input_exact=True,generation=g,input=details))
    save(ROOT/'audit/dominance_validation.json',dict(at=now(),pass_all=True,examples=2,rows=rows,
        manifest_sha256=sha(mp),environment=environment(model),slurm_job_id=os.environ['SLURM_JOB_ID']))
    print('DOMINANCE_TECHNICAL_PASS',len(rows),flush=True)


if __name__=='__main__':main()
