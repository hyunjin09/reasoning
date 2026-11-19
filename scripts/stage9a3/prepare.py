"""Freeze external synthetic images, public model identities and common prompts."""
import argparse,hashlib,json,os,shutil
from pathlib import Path
from datetime import datetime,timezone
from visual_reasoning.stage9a3.dataset import scene,render,prompt,SEED

ROOT=Path('outputs/stage9a3/v1')


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
    return h.hexdigest()


def save(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as f:json.dump(value,f,indent=2,ensure_ascii=False);f.write('\n')


def load(path):return json.loads(Path(path).read_text())


def now():return datetime.now(timezone.utc).isoformat()


def main():
    assert os.environ.get('SLURM_JOB_ID'),'Model hashing is scheduled CPU work'
    ap=argparse.ArgumentParser();ap.add_argument('--dataset-root',required=True);ap.add_argument('--model-root',required=True);args=ap.parse_args()
    data=Path(args.dataset_root);data.mkdir(parents=True,exist_ok=False)
    models={}
    for key,name,revision in [('qwen25','Qwen2.5-VL-3B-Instruct','66285546d2b821cf421d4f5eb2576359d3770cd3'),
                              ('qwen3','Qwen3-VL-2B-Instruct','89644892e4d85e24eaac8bacfd4f463576704203')]:
        path=Path(args.model_root)/('models--Qwen--'+name)/'snapshots'/revision
        files=[f for f in path.iterdir() if f.is_file() and f.suffix in ('.json','.safetensors','.txt','.jinja')]
        models[key]=dict(repo='Qwen/'+name,revision=revision,checkpoint=str(path),files_sha256={f.name:sha(f) for f in sorted(files)})
    rows=[];queries=[]
    for i in range(52):
        row=scene(i);path=data/(row['image_id']+'.png');render(row,path)
        row.update(image_path=str(path),image_sha256=sha(path))
        for q in row['queries']:
            q.update(image_path=str(path),image_sha256=row['image_sha256'],split=row['split'],prompt=prompt(q));queries.append(q)
        rows.append(row)
    assert len({r['image_sha256'] for r in rows})==52
    manifest=dict(at=now(),seed=SEED,rows=rows,queries=queries,counts=dict(primary_images=32,reserve_images=16,technical_images=4,primary_queries=64,reserve_queries=32,technical_queries=8),
                  generator_sha256=sha('code/visual_reasoning/stage9a3/dataset.py'),external_root=str(data),frozen=True)
    save(ROOT/'stage9a3_synthetic_dataset_manifest.json',manifest)
    save(ROOT/'stage9a3_prompt_manifest.json',dict(at=now(),rows=[{k:q[k] for k in ['query_id','image_id','split','prompt','options']} for q in queries],
        cot_instruction='Think step by step. You must write intermediate steps.',same_body_across_models=True,native_chat_templates=True,frozen=True))
    save(ROOT/'audit/inference_tasks.json',dict(rows=[{k:v for k,v in q.items() if k not in ['answer','count']} for q in queries],gold_omitted=True))
    save(ROOT/'config.json',dict(at=now(),root=str(ROOT),models=models,seed=SEED,bootstrap_draws=4000,
        min_pixels=224**2,max_pixels=256**2,layer_fractions=[0,.5,.75,1],generation=dict(do_sample=False,use_cache=True),
        allowed_nodes=['node02','node03','node06','node07'],max_stage_gpus=4,
        protocol_sha256=sha('plan/stage9a3_execution_protocol_v1.md'),dataset_sha256=sha(ROOT/'stage9a3_synthetic_dataset_manifest.json'),
        prompts_sha256=sha(ROOT/'stage9a3_prompt_manifest.json'),tasks_sha256=sha(ROOT/'audit/inference_tasks.json')))
    shutil.copyfile('plan/stage9a3_execution_protocol_v1.md',ROOT/'stage9a3_vab_calibration_spec.md')
    save(ROOT/'audit/input_freeze.json',dict(at=now(),slurm_job_id=os.environ['SLURM_JOB_ID'],config_sha256=sha(ROOT/'config.json'),files_sha256={str(p):sha(p) for p in ROOT.glob('stage9a3_*') if p.is_file()}))
    print(json.dumps(dict(images=52,queries=104,models=list(models),frozen_at=now())))


if __name__=='__main__':main()
