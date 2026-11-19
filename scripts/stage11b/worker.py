"""Finite batch queue; no scoring, follow-on experiments or automatic retries."""
import argparse,os,socket,time,traceback
from pathlib import Path
import torch
from scripts.stage11b.common import ROOT,load,save,sha,now
from scripts.stage11b.generation import runtime,prepare,generate
from visual_reasoning.stage0.modeling import runtime_environment

def main(model_key,queue,max_seconds):
    started=time.monotonic();job=os.environ['SLURM_JOB_ID']
    assert torch.cuda.device_count()==1 and socket.gethostname().split('.')[0] in ['node02','node03','node06','node07']
    cfg=load(ROOT/'config.json');manifest=load(ROOT/f'{queue}_tasks.json')
    assert load(ROOT/'audit/technical_preflight.json')['passed']
    assert sha(ROOT/f'{queue}_tasks.json')==cfg['manifest_sha256'][queue]
    for p,h in cfg['source_sha256'].items():assert sha(p)==h,p
    torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
    info=cfg['models'][model_key]
    for name,h in info['files_sha256'].items():assert sha(Path(info['checkpoint'])/name)==h,name
    proc,model=runtime(info)
    save(ROOT/queue/'workers'/job/'environment.json',dict(at=now(),slurm_job_id=job,node=socket.gethostname(),tf32=False,
        config_sha256=sha(ROOT/'config.json'),**runtime_environment(Path(info['checkpoint']),model,cfg['max_new_tokens'])))
    rows=[r for r in manifest['rows'] if r['model_key']==model_key]
    for start in range(0,len(rows),cfg['batch_size']):
        if time.monotonic()-started>max_seconds-600:
            print('SAFE_BUDGET_STOP',flush=True);break
        batch_rows=rows[start:start+cfg['batch_size']]
        claimed=[]
        for row in batch_rows:
            dest=ROOT/queue/'results'/row['task_id']
            assert not dest.exists(),'No overwrite/repeat of any complete or partial record'
            lock=ROOT/queue/'claims'/row['task_id']
            lock.mkdir(parents=False,exist_ok=False)
            save(lock/'owner.json',dict(at=now(),slurm_job_id=job))
            assert sha(row['image'])==row['image_sha256']
            claimed.append(row)
        try:
            batch,metas=prepare(proc,claimed)
            for row,meta in zip(claimed,metas):save(ROOT/queue/'results'/row['task_id']/'input.json',meta)
            outputs=generate(proc,model,batch,cfg['max_new_tokens'],max_time=max(1,max_seconds-(time.monotonic()-started)-45))
            for row,out in zip(claimed,outputs):
                dest=ROOT/queue/'results'/row['task_id']
                save(dest/'generation.json',out)
                receipt={k:v for k,v in out.items() if k not in ['raw_decoded_response','generated_token_ids']}
                save(dest/'result.json',dict(receipt,at=now(),task_id=row['task_id'],family_id=row['family_id'],item_id=row['item_id'],
                    arm=row['arm'],condition=row['condition'],slurm_job_id=job,
                    generation_sha256=sha(dest/'generation.json'),input_sha256=sha(dest/'input.json'),config_sha256=sha(ROOT/'config.json')))
                print('COMPLETE',row['task_id'],'tokens',out['tokens'],'seconds_per_batch',round(out['batch_seconds'],2),flush=True)
            del batch,outputs
        except Exception as exc:
            save(ROOT/queue/'workers'/job/'failure.json',dict(at=now(),error=repr(exc),traceback=traceback.format_exc(),task_ids=[r['task_id'] for r in claimed]))
            raise
    save(ROOT/queue/'workers'/job/'exit.json',dict(at=now(),elapsed_seconds=time.monotonic()-started,finite_queue=True))
    print('WORKER_EXIT',flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--model',choices=['instruct','thinking'],required=True)
    parser.add_argument('--queue',default='discovery');parser.add_argument('--max-seconds',type=int,default=5300)
    args=parser.parse_args();main(args.model,args.queue,args.max_seconds)
