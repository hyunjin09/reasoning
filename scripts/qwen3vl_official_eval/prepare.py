"""Preserve exact12 identities; use canonical questions and official image dump."""
import hashlib
import importlib.metadata
import sys
from pathlib import Path
import pandas as pd
from transformers import AutoProcessor
from scripts.qwen3vl_official_eval.common import ROOT, OLD, load, save, sha, now

def main():
    freeze=load(ROOT/'audit/audit_freeze.json')
    for p,d in freeze['files'].items():assert sha(p)==d,p
    src=ROOT/'sources/qwen/evaluation/MathVision';sys.path.insert(0,str(src.resolve()))
    from dataset_utils import dump_image
    provenance=load(ROOT/'audit/dataset_download.json');assert sha(provenance['path'])==provenance['sha256']
    df=pd.read_csv(provenance['path'],sep='\t').set_index('index')
    original=load(OLD/'nonprimary_cases.json');models=load(OLD/'config.json')['models']
    image_root=Path(provenance['path']).parent/'images/MathVision'
    rows=[]
    for old in original['rows']:
        source=df.loc[int(old['item_id'])].to_dict();source['index']=int(old['item_id'])
        path,=dump_image(source,str(image_root))
        assert sha(old['image'])==old['image_sha256']
        rows.append(dict(item_id=old['item_id'],family_id=old['family_id'],index=int(old['item_id']),
            question=source['question'],image=path,image_sha256=sha(path),
            prior_image=old['image'],prior_image_sha256=old['image_sha256']))
    assert len(rows)==12 and len({r['family_id'] for r in rows})==12
    # Execute the exact official pure prompt functions, without importing vLLM/CUDA.
    import ast
    tree=ast.parse((src/'run_mathv.py').read_text());names={'build_mathv_prompt','prepare_inputs_for_vllm'}
    module=ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[])
    from qwen_vl_utils import process_vision_info
    ns={'process_vision_info':process_vision_info};exec(compile(module,str(src/'run_mathv.py'),'exec'),ns)
    prompt_records=[]
    for arm,key in [('instruct_direct','instruct'),('thinking','thinking')]:
        proc=AutoProcessor.from_pretrained(models[key]['checkpoint'],local_files_only=True)
        for r in rows:
            messages=ns['build_mathv_prompt'](r,lambda line:[line['image']],'MathVision')
            prepared=ns['prepare_inputs_for_vllm'](messages,proc)
            text=prepared['prompt'];assert r['question'] in text
            expected='<|im_start|>assistant\n<think>\n' if arm=='thinking' else '<|im_start|>assistant\n'
            assert text.endswith(expected)
            prompt_records.append(dict(arm=arm,item_id=r['item_id'],messages=messages,chat_prompt=text,
                chat_prompt_sha256=hashlib.sha256(text.encode()).hexdigest(),
                prepared_image_sizes=[im.size for im in prepared['multi_modal_data']['image']],
                prepared_image_pixel_sha256=[hashlib.sha256(im.tobytes()).hexdigest() for im in prepared['multi_modal_data']['image']]))
    save(ROOT/'audit/frozen_official_inputs.json',dict(at=now(),rows=prompt_records))
    diff=load(ROOT/'qwen3vl_mathvision_protocol_diff.json')
    env={p:importlib.metadata.version(p) for p in ['vllm','torch','transformers','qwen-vl-utils','pillow']}
    source_paths=list(Path('scripts/qwen3vl_official_eval').glob('*.py'))+[Path('scripts/qwen3vl_official_eval/run.sh')]+list(src.glob('*.py'))
    manifest=dict(at=now(),frozen=True,scope='Technical official-protocol sanity, no Claim3',n_cases=12,n_sanity_calls=24,
        cases=rows,case_source=str(OLD/'nonprimary_cases.json'),case_source_sha256=sha(OLD/'nonprimary_cases.json'),
        audit_freeze_sha256=sha(ROOT/'audit/audit_freeze.json'),models=models,environment=env,
        recipes=diff['official'],runtime=dict(tensor_parallel_size=1,gpu_memory_utilization=.9,max_model_len=128000,
            max_images_per_prompt=10,trust_remote_code=True,seed=42,attention_backend='vLLM default',
            runtime='Official run_mathv.run_inference with dataset-only filtering and observational output capture',
            model_revisions='Local pinned variants; official evaluation does not publish exact revisions'),
        gate=dict(committed_final_min=10,cap_hits_max=1,pathologies_max=1,required_calls=12),
        review_protocol='Literal terminal commitment; Thinking final after think terminator. Cap and commitment separately reviewed. Same repeated32gram descriptors plus semantic pathology review as Stage11CR. No accuracy.',
        ablations=diff['prospective_ablation'],ablation_condition='Only after Instruct gate PASS, all12 each, no new variants, hard3GPUh',
        resource=dict(sanity_target_gpu_hours=1.5,additional_ablation_target_gpu_hours=1.5,hard_gpu_hours=3,
            prospective_sanity_allocation='Two finite40minute one-GPU jobs =1.3333GPUh maximum including startup',
            stop_rule='No new wave whose full allocation commitments exceed hard3GPUh'),
        source_sha256={str(p):sha(p) for p in source_paths},
        no_accuracy_selection=True,no_primary_oracle_cot_reserve=True)
    save(ROOT/'qwen3vl_official_sanity_manifest.json',manifest)
    print('FROZEN_OFFICIAL_SANITY',len(rows),env)

if __name__=='__main__':main()
