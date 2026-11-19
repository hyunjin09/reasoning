"""Finite post-anchor source×text intervention queue."""
import os,traceback
import torch
from scripts.stage10a.common import ROOT,load,save,sha,now
from scripts.stage10a.runtime import load_runtime,environment
from scripts.stage10a.image_text import fresh_image


@torch.inference_mode()
def main():
    mp=ROOT/'audit/dominance_manifest.json';m=load(mp);v=load(ROOT/'audit/dominance_validation.json')
    assert v['pass_all'] and v['manifest_sha256']==sha(mp)
    assert m['gate_b_sha256']==sha(ROOT/'audit/gate_b_inference.json') and load(ROOT/'audit/gate_b_inference.json')['gate_b_pass']
    for p,d in m['source_sha256'].items():assert sha(p)==d,p
    cfg,processor,model=load_runtime();sid=os.environ['SLURM_JOB_ID'];root=ROOT/'dominance';done=[]
    env=environment(model);env['stage10a_config_sha256']=sha(ROOT/'config.json');save(root/'workers'/sid/'environment.json',env)
    for r in m['rows']:
        claim=root/'claims'/r['task_id'];claim.parent.mkdir(parents=True,exist_ok=True)
        try:claim.mkdir()
        except FileExistsError:continue
        save(claim/'owner.json',dict(at=now(),slurm_job_id=sid));print('START',r['task_id'],flush=True)
        torch.cuda.reset_peak_memory_stats();g,details=fresh_image(processor,model,r['task'],r['prefix_ids'],cfg['seed'])
        assert g['tokens']<=512
        save(r['generation_path'],g)
        save(r['result_path'],dict(at=now(),query_id=r['query_id'],condition=r['condition'],anchor='post',slurm_job_id=sid,
            generation_sha256=sha(r['generation_path']),manifest_sha256=sha(mp),config_sha256=sha(ROOT/'config.json'),
            prefix_tokens=r['prefix_tokens'],remaining_tokens=r['remaining_tokens'],input=details,runtime_seconds=g['runtime_seconds'],
            peak_allocated_bytes=torch.cuda.max_memory_allocated(),peak_reserved_bytes=torch.cuda.max_memory_reserved()))
        done.append(r['task_id']);print('COMPLETE',r['task_id'],g['continuation_tokens'],round(g['runtime_seconds'],3),flush=True)
    save(root/'workers'/sid/'complete.json',dict(at=now(),tasks=done))


if __name__=='__main__':
    try:main()
    except Exception as e:
        save(ROOT/f'audit/worker_failure_{os.environ.get("SLURM_JOB_ID","local")}.json',dict(at=now(),error=repr(e),traceback=traceback.format_exc()));raise
