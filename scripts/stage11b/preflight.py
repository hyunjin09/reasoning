"""Finite GPU technical validation on old families, no discovery outcomes."""
import os,socket,gc
import torch
from scripts.stage11b.common import ROOT,load,save,sha,now
from scripts.stage11b.generation import runtime,prepare,generate
from visual_reasoning.stage0.modeling import runtime_environment
from visual_reasoning.stage8b.v2_protocol import prepared_input
from visual_reasoning.stage9a.protocol import prompt
from scripts.stage11b.preflight_checks import text_only_fields

assert os.environ.get('SLURM_JOB_ID') and torch.cuda.device_count()==1
torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
config=load(ROOT/'config.json');old=load('outputs/stage9a/v1/stage9a_cohort_manifest.json')['rows'][:4]
checks=[]
for key,arm in [('instruct','instruct_cot'),('thinking','thinking')]:
    info=config['models'][key]
    for name,h in info['files_sha256'].items():assert sha(info['checkpoint']+'/'+name)==h,name
    proc,model=runtime(info)
    rows=[dict(r,arm=arm,task_id=f'technical_{arm}_{r["item_id"]}',condition='native') for r in old]
    batch,meta=prepare(proc,rows)
    grid_start=0
    for i,r in enumerate(rows):
        single,original=prepared_input(proc,dict(r,generation_query=prompt(r['generation_query'],arm)),device='cpu')
        ids=batch['input_ids'][i][batch['attention_mask'][i].bool()].cpu()
        assert torch.equal(ids,single['input_ids'][0])
        count=single['pixel_values'].shape[0]
        assert torch.equal(batch['pixel_values'][grid_start:grid_start+count].cpu(),single['pixel_values'])
        assert meta[i]['image_grid_thw']==original['image_grid_thw']
        grid_start+=count
    outputs=generate(proc,model,batch,32)
    assert all(r['tokens']>0 for r in outputs)
    del batch
    text_rows=[dict(r,condition='technical_text',generation_query='Task-relevant visual evidence:\nFact 1: AB = 6\n\nQuestion:\nWhat is the length of AB?') for r in rows]
    batch,text_meta=prepare(proc,text_rows)
    assert text_only_fields(batch,batch['mm_token_type_ids'].unique().tolist() if 'mm_token_type_ids' in batch else [])
    text_outputs=generate(proc,model,batch,32)
    checks.append(dict(model=key,native_preprocessing_matches_single=True,left_padding=True,
        native_generated_tokens=[r['tokens'] for r in outputs],text_generated_tokens=[r['tokens'] for r in text_outputs],
        text_image_tokens=[r['visual_token_count'] for r in text_meta],text_no_multimodal_cache=True,
        environment=runtime_environment(__import__('pathlib').Path(info['checkpoint']),model,config['max_new_tokens']),
        native_seconds=outputs[0]['batch_seconds'],text_seconds=text_outputs[0]['batch_seconds']))
    del batch,model,proc;gc.collect();torch.cuda.empty_cache()
save(ROOT/'audit/technical_preflight.json',dict(at=now(),passed=True,slurm_job_id=os.environ['SLURM_JOB_ID'],
    node=socket.gethostname(),checks=checks,config_sha256=sha(ROOT/'config.json'),discovery_outcomes_opened=False))
print('PREFLIGHT_PASS',flush=True)
