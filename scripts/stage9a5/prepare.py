"""Freeze unchanged images/CoT evidence and native Thinking prompts/checkpoint."""
import argparse,os,shutil
from pathlib import Path
from scripts.stage9a5.common import ROOT,OLD,COT,PROTOCOL,load,save,sha,now
from scripts.stage9a5.native import thinking_prompt


def main():
    assert os.environ.get('SLURM_JOB_ID')
    ap=argparse.ArgumentParser();ap.add_argument('--checkpoint',required=True);args=ap.parse_args()
    model=Path(args.checkpoint);mc=load(model/'config.json');assert mc['text_config']['num_hidden_layers']==36
    old=load(OLD/'audit/inference_tasks.json')['rows'];rows=[]
    for r in old:rows.append(dict(r,prompt=thinking_prompt(r['prompt'])))
    assert len(rows)==104 and all('answer' not in r and 'count' not in r for r in rows)
    save(ROOT/'audit/inference_tasks.json',dict(at=now(),rows=rows,gold_omitted=True,changed_only='Removed exact prompted-CoT instruction.'))
    base=load(OLD/'config.json');inputs=[OLD/'audit/inference_tasks.json',OLD/'stage9a3_synthetic_dataset_manifest.json',
        ROOT/'audit/inference_tasks.json',Path('code/visual_reasoning/stage9a3/access.py'),Path('code/visual_reasoning/stage9a_dynamics/generation.py'),
        Path('scripts/stage9a3/runtime.py'),Path('scripts/stage9a3/literal_review.py'),Path('scripts/stage9a4/decisions.py')]
    for p,r in load(COT/'stage9a4_artifact_index.json')['artifacts'].items():
        if r['status']=='complete':assert sha(COT/p)==r['sha256'];inputs.append(COT/p)
    inputs += [COT/'config.json',COT/'stage9a4_artifact_index.json',COT/'audit/t128_decision.json',COT/'audit/r1_scored.json',COT/'audit/t128_scored.json']
    inputs += sorted(COT.glob('*/results/*/*.json'))
    for r in load(OLD/'stage9a3_synthetic_dataset_manifest.json')['rows']:
        assert sha(r['image_path'])==r['image_sha256'];inputs.append(Path(r['image_path']))
    files=[p for p in model.iterdir() if p.is_file() and p.suffix in ('.json','.safetensors','.txt','.jinja')]
    tokens=load(model/'tokenizer_config.json')['added_tokens_decoder'];assert tokens['151668']['content']=='</think>'
    cfg=dict(at=now(),model='Qwen/Qwen3-VL-4B-Thinking',revision=model.name,checkpoint=str(model),
        files_sha256={p.name:sha(p) for p in sorted(files)},inputs_sha256={str(p):sha(p) for p in inputs},
        protocol_sha256=sha(PROTOCOL),seed=base['seed'],bootstrap_draws=4000,max_new_tokens=512,layers=36,
        think_close_token_id=151668,min_pixels=base['min_pixels'],max_pixels=base['max_pixels'],allowed_nodes=base['allowed_nodes'],
        max_stage_gpus=4,decoding=dict(do_sample=False,dtype='bfloat16',TF32=False,language_backend='eager',vision_backend='sdpa'))
    save(ROOT/'config.json',cfg);shutil.copyfile(PROTOCOL,ROOT/'stage9a5_qwen3_4b_thinking_spec.md')
    sources=['scripts/stage9a5/common.py','scripts/stage9a5/runtime.py','scripts/stage9a5/worker.py','scripts/stage9a5/native.py',
        'code/visual_reasoning/stage9a3/access.py']
    manifest=[]
    for q in rows:
        if q['split']!='primary':continue
        dest=ROOT/'full/results'/(q['query_id']+'_full')
        manifest.append(dict(query_id=q['query_id'],image_id=q['image_id'],policy='full',cutoff=None,mode='standard',split='primary',execution='run',
            generation_path=str(dest/'generation.json'),result_path=str(dest/'result.json')))
    save(ROOT/'audit/full_manifest.json',dict(at=now(),frozen=True,stage='full',rows=manifest,logical_rows=64,new_generations=64,
        config_sha256=sha(ROOT/'config.json'),source_sha256={p:sha(p) for p in sources}))
    counts=dict(T0_full=64,T1=192,T256_optional=64,null_sink_new_max=128,relative_optional_both_arms=256,reserve_optional_both_arms=192)
    estimates={k:dict(max_generations=n,all_cap_gpu_hours=n*512*.06/3600) for k,n in counts.items()}
    save(ROOT/'audit/prelaunch_resource_estimate.json',dict(at=now(),phases=estimates,seconds_per_token=.06,
        basis='Conservative versus measured4B Stage9A.4 throughput;512 fixed cap bounds total work.',
        primary_plus_control_max_gpu_hours=sum(estimates[k]['all_cap_gpu_hours'] for k in ['T0_full','T1','T256_optional','null_sink_new_max']),
        overhead_allowance_gpu_hours=1,target_gpu_hours=10,hard_stop_projected_before_optional_gpu_hours=15))
    save(ROOT/'audit/input_freeze.json',dict(at=now(),config_sha256=sha(ROOT/'config.json'),source_sha256={p:sha(p) for p in sources},
        slurm_job_id=os.environ['SLURM_JOB_ID'],no_download=True,reference_files_verified=len(inputs),prior_evidence_preserved=True))
    print('FROZEN',cfg['model'],cfg['revision'],len(manifest),flush=True)


if __name__=='__main__':main()
