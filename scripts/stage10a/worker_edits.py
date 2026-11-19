"""Finite fresh text-only counterfactual/deletion/sham queue."""
import os,traceback
import torch
from scripts.stage10a.common import ROOT,load,save,sha,now
from scripts.stage10a.runtime import load_runtime,fresh,environment


@torch.inference_mode()
def main():
    mp=ROOT/'audit/gate_b_manifest.json';manifest=load(mp)
    assert manifest['frozen'] and manifest['config_sha256']==sha(ROOT/'config.json')
    assert manifest['gate_a_sha256']==sha(ROOT/'audit/gate_a_inference.json')
    assert load(ROOT/'audit/gate_a_inference.json')['gate_a_pass']
    for p,d in manifest['source_sha256'].items():assert sha(p)==d,p
    cfg,processor,model=load_runtime();sid=os.environ['SLURM_JOB_ID'];root=ROOT/'gate_b'
    env=environment(model);env['stage10a_config_sha256']=sha(ROOT/'config.json')
    save(root/'workers'/sid/'environment.json',env)
    events={r['query_id']:r for r in load(ROOT/'stage10a_event_selection.json')['rows']};done=[]
    for row in manifest['rows']:
        if row['reused']:
            assert sha(row['generation_path'])==row['reused_generation_sha256']
            assert sha(row['result_path'])==row['reused_result_sha256']
            continue
        claim=root/'claims'/row['task_id'];claim.parent.mkdir(parents=True,exist_ok=True)
        try:claim.mkdir()
        except FileExistsError:continue
        save(claim/'owner.json',dict(at=now(),slurm_job_id=sid));print('START',row['task_id'],now(),flush=True)
        torch.cuda.reset_peak_memory_stats()
        g,details=fresh(processor,model,events[row['query_id']]['task'],row['prefix_ids'],cfg['seed'])
        assert g['tokens']<=512
        save(row['generation_path'],g)
        save(row['result_path'],dict(at=now(),query_id=row['query_id'],condition=row['condition'],anchor='emit',
            slurm_job_id=sid,generation_sha256=sha(row['generation_path']),manifest_sha256=sha(mp),
            config_sha256=sha(ROOT/'config.json'),prefix_tokens=row['prefix_tokens'],remaining_tokens=row['remaining_tokens'],input=details,
            runtime_seconds=g['runtime_seconds'],peak_allocated_bytes=torch.cuda.max_memory_allocated(),
            peak_reserved_bytes=torch.cuda.max_memory_reserved()))
        done.append(row['task_id']);print('COMPLETE',row['task_id'],g['continuation_tokens'],round(g['runtime_seconds'],3),flush=True)
    save(root/'workers'/sid/'complete.json',dict(at=now(),tasks=done))


if __name__=='__main__':
    try:main()
    except Exception as e:
        save(ROOT/f'audit/worker_failure_{os.environ.get("SLURM_JOB_ID","local")}.json',dict(at=now(),error=repr(e),traceback=traceback.format_exc()));raise
