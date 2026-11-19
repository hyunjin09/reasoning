"""Verify existing inputs and hash the pinned checkpoint on scheduled CPU."""
import argparse,os,shutil
from pathlib import Path
from scripts.stage9a4.common import ROOT,OLD,PROTOCOL,load,save,sha,now


def main():
    assert os.environ.get('SLURM_JOB_ID')
    p=argparse.ArgumentParser();p.add_argument('--checkpoint',required=True);a=p.parse_args()
    model=Path(a.checkpoint);mc=load(model/'config.json');assert mc['text_config']['num_hidden_layers']==36
    assert 'Qwen3VLForConditionalGeneration' in mc['architectures']
    prior=load(OLD/'config.json')
    inputs=[OLD/'audit/inference_tasks.json',OLD/'stage9a3_synthetic_dataset_manifest.json',OLD/'stage9a3_prompt_manifest.json',
            OLD/'stage9a3_qwen25_positive_control.json',OLD/'stage9a3_summary.md',OLD/'stage9a3_qwen25_coarse_grid.parquet',
            OLD/'stage9a3_qwen25_coarse_grid_extended.parquet',OLD/'stage9a3_qwen25_full_access.json',
            Path('code/visual_reasoning/stage9a3/access.py'),Path('code/visual_reasoning/stage9a_dynamics/generation.py'),
            Path('scripts/stage9a3/runtime.py'),Path('scripts/stage9a3/literal_review.py')]
    for r in load(OLD/'stage9a3_synthetic_dataset_manifest.json')['rows']:
        assert sha(r['image_path'])==r['image_sha256'];inputs.append(Path(r['image_path']))
    files=[f for f in model.iterdir() if f.is_file() and f.suffix in ('.json','.safetensors','.txt','.jinja')]
    cfg=dict(at=now(),model='Qwen/Qwen3-VL-4B-Instruct',revision=model.name,checkpoint=str(model),
        files_sha256={f.name:sha(f) for f in sorted(files)},inputs_sha256={str(p):sha(p) for p in inputs},
        protocol_sha256=sha(PROTOCOL),seed=prior['seed'],bootstrap_draws=4000,max_new_tokens=512,layers=36,
        min_pixels=prior['min_pixels'],max_pixels=prior['max_pixels'],allowed_nodes=prior['allowed_nodes'],max_stage_gpus=4,
        decoding=dict(do_sample=False,dtype='bfloat16',TF32=False,language_backend='eager',vision_backend='sdpa'))
    save(ROOT/'config.json',cfg);shutil.copyfile(PROTOCOL,ROOT/'stage9a4_qwen3_4b_repair_spec.md')
    counts=dict(R0_full=64,R1_masked=128,R2_worst=128,reserve_optional=96,null_sink_new_max=128)
    estimate={k:dict(max_generations=n,all_cap_gpu_hours=n*512*.06/3600) for k,n in counts.items()}
    save(ROOT/'audit/prelaunch_resource_estimate.json',dict(at=now(),phases=estimate,seconds_per_token=.06,
        basis='Conservative >4x prior Qwen3-2B measured .0134s/token; update from4B observed throughput.',
        primary_worst_gpu_hours=sum(estimate[k]['all_cap_gpu_hours'] for k in ['R0_full','R1_masked','R2_worst']),
        startup_validation_allowance_gpu_hours=1,within_15h_target=True,hard_stop_projected_primary_gpu_hours=25))
    save(ROOT/'audit/input_freeze.json',dict(at=now(),slurm_job_id=os.environ['SLURM_JOB_ID'],config_sha256=sha(ROOT/'config.json'),
        no_download=True,prior_outputs_unchanged=True))
    print('FROZEN',cfg['model'],cfg['revision'],flush=True)


if __name__=='__main__':main()
