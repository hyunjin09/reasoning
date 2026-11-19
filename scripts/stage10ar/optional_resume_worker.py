"""Finite image-free A3 edits from the prospectively sealed12-image inventory."""
import os,traceback
import torch
from scripts.stage10ar.common import ROOT,load,save,sha,now
from scripts.stage10ar.runtime import load_runtime,fresh,environment


@torch.inference_mode()
def main():
    mp=ROOT/'audit/optional_resume_manifest.json';m=load(mp)
    assert m['frozen'] and m['config_sha256']==sha(ROOT/'config.json')
    assert load(ROOT/'stage10ar_primary_inference.json')['optional_a3_edit_gate_pass']
    for p,d in m['source_sha256'].items():assert sha(p)==d,p
    cfg,processor,model=load_runtime();sid=os.environ['SLURM_JOB_ID'];root=ROOT/'optional';done=[]
    env=environment(model);env['stage10ar_config_sha256']=sha(ROOT/'config.json')
    save(root/'workers'/sid/'environment.json',env)
    events={r['query_id']:r for r in load(ROOT/'stage10ar_anchor_annotations.json')['rows']}
    for q in m['query_order']:
        claim=root/'claims_resume_v1'/q;claim.parent.mkdir(parents=True,exist_ok=True)
        try:claim.mkdir()
        except FileExistsError:continue
        save(claim/'owner.json',dict(at=now(),slurm_job_id=sid))
        for r in m['rows']:
            if r['query_id']!=q or r['execution']!='run':continue
            ids=r['prefix_ids'];n=len(ids);torch.cuda.reset_peak_memory_stats()
            assert processor.tokenizer.decode(ids,skip_special_tokens=False,clean_up_tokenization_spaces=False)==r['prefix_text']
            g,details=fresh(processor,model,events[q]['task'],ids,cfg['seed'])
            save(r['generation_path'],g)
            save(r['result_path'],dict(at=now(),query_id=q,condition=r['condition'],anchor='A3',slurm_job_id=sid,
                generation_sha256=sha(r['generation_path']),manifest_sha256=m['parent_manifest_sha256'],resume_manifest_sha256=sha(mp),config_sha256=sha(ROOT/'config.json'),
                prefix_tokens=n,remaining_tokens=512-n,input=details,runtime_seconds=g['runtime_seconds'],
                peak_allocated_bytes=torch.cuda.max_memory_allocated(),peak_reserved_bytes=torch.cuda.max_memory_reserved()))
            done.append(r['task_id']);print('COMPLETE',r['task_id'],g['continuation_tokens'],round(g['runtime_seconds'],3),flush=True)
    save(root/'workers'/sid/'complete.json',dict(at=now(),tasks=done))


if __name__=='__main__':
    try:main()
    except Exception as e:
        save(ROOT/f'audit/optional_worker_failure_{os.environ.get("SLURM_JOB_ID","local")}.json',dict(at=now(),error=repr(e),traceback=traceback.format_exc()));raise
