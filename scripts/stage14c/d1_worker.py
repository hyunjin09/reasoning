"""Approved D1 adapter, gated after primary seal; parent scientific worker unchanged."""
import argparse
from PIL import Image
from scripts.stage14c.common import *
from scripts.stage14c import worker,oom_runner
from scripts.stage14c.input_adapter import prepare as prepare_parquet


def authorize(manifest):
    assert manifest['mode']=='D1'
    assert manifest['config_sha256']==sha(ROOT/'spec/model_and_recipe_identity.json')
    primary=load(ROOT/'audit/primary_analysis_seal.json')
    for p,h in primary['files'].items():assert sha(p)==h,p
    assert load(ROOT/'audit/preflight_validation.json')['pass']
    for name in ['D1_materialization_seal_v1.json','D1_execution_seal_v1.json']:
        for p,h in load(ROOT/'audit'/name)['files'].items():assert sha(p)==h,p
    expected={t['task_id']:t for t in all_tasks('D1')}
    assert len({t['task_id'] for t in manifest['rows']})==len(manifest['rows'])
    assert all(t==expected.get(t['task_id']) for t in manifest['rows'])
    assert {t['model_key'] for t in manifest['rows']}=={manifest['model_key']}


def prepare(task,processor,build_prompt,prepare_inputs):
    ref=task['image_reference']
    if 'path' not in ref:return prepare_parquet(task,processor,build_prompt,prepare_inputs)
    assert sha(ref['path'])==task['image_sha256']
    image=Image.open(ref['path']);image.load()
    messages=build_prompt({'question':task['prompt']},lambda row:image,'MathVision')
    inp=prepare_inputs(messages,processor)
    receipt=[dict(role='user',content=[dict(type='image',source=ref,sha256=task['image_sha256'],min_pixels=602112,max_pixels=4014080),dict(type='text',text=task['prompt'])])]
    return inp,receipt

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('manifest');p.add_argument('--manifest-sha256',required=True);p.add_argument('--child',action='store_true');a=p.parse_args()
    if a.child:
        worker.authorize=authorize;worker.prepare=prepare;worker.run(a.manifest,a.manifest_sha256)
    else:
        import sys
        oom_runner.authorize=authorize
        oom_runner.run(a.manifest,a.manifest_sha256,worker_command=[sys.executable,'-m','scripts.stage14c.d1_worker','--child'])
