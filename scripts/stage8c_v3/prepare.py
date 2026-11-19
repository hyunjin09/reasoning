"""Freeze direct FP32 development using the untouched Stage8C cohorts."""
import json
from datetime import datetime, timezone
from pathlib import Path
from scripts.stage8c.prepare import save, sha

ROOT=Path('outputs/stage8c_v3/v1')


def main():
    old=Path('outputs/stage8c_v2/v1')
    assert not ROOT.exists(), 'Version outputs; never replace a previous freeze'
    seals=[old/'audit/completion_seal.json',old/'audit/technical_stop_freeze.json',
           Path('outputs/stage8c_repair/v1/audit/completion_seal.json')]
    verified={}
    for p in seals:
        data=json.loads(p.read_text())
        for key in ['hashes','artifacts_sha256','support_sha256']:
            for name,digest in data.get(key,{}).items():
                assert sha(name)==digest,name
                verified[name]=digest
    at=datetime.now(timezone.utc).isoformat()
    ROOT.mkdir(parents=True)
    for name in ['dev128','test512']:
        source=old/f'stage8c_v2_{name}_manifest.json'
        target=ROOT/f'stage8c_v3_{name}_manifest.json'
        target.write_bytes(source.read_bytes())
        assert sha(source)==sha(target)
    save(ROOT/'audit/subsets.json',json.loads((old/'audit/subsets.json').read_text()))
    dev=json.loads((ROOT/'stage8c_v3_dev128_manifest.json').read_text())['rows']
    test=json.loads((ROOT/'stage8c_v3_test512_manifest.json').read_text())['rows']
    assert len(dev)==128 and len(test)==512
    assert len({r['family_id'] for r in dev+test})==640
    families=json.loads((old/'stage8c_v2_family_manifest.json').read_text())
    assert not ({r['family_id'] for r in dev+test} & set(families['excluded_families']))
    for r in dev+test:assert sha(r['image'])==r['image_sha256'],r['item_id']
    cfg=json.loads((old/'audit/prepared_config.json').read_text())
    cfg={k:cfg[k] for k in ['model_checkpoint','model_revision','detector_freeze',
        'detector_freeze_sha256','max_new_tokens','generation_parameters','presence_penalty','min_pixels','max_pixels']}
    assert Path(cfg['model_checkpoint']).is_dir()
    assert sha(cfg['detector_freeze'])==cfg['detector_freeze_sha256']
    tasks=[]
    for r in dev:
        safe={k:r[k] for k in ['item_id','family_id','image','image_sha256','question','generation_query','seed']}
        for g in [1.,1.25,1.5,2.]:
            tasks.append(dict(task_id=f"{r['item_id']}_g{g:.2f}",input=safe,gain=g,policy='retrieval'))
    save(ROOT/'audit/dev_tasks.json',dict(at=at,tasks=tasks,paired_seeds=True,outcomes_used=False))
    sources=[p for p in Path('scripts/stage8c_v3').glob('*.py')]
    sources += list(Path('scripts/stage8c_v3').glob('*.sh'))
    sources += [Path(p) for p in ['code/visual_reasoning/stage8c/fp32_runtime.py',
        'code/visual_reasoning/stage8c/analysis_fp32.py','code/visual_reasoning/stage8c/gain.py',
        'code/visual_reasoning/stage8c/trigger.py','code/visual_reasoning/stage0/modeling.py',
        'code/visual_reasoning/stage8b/passive.py','code/visual_reasoning/stage8b/v2_protocol.py',
        'code/visual_reasoning/stage8b/v2_scoring.py',
        'plan/stage8c_v3_fp32_direct_retrieval_gain_plan.md','plan/stage8c_v3_execution_protocol_v1.md']]
    cfg.update(at=at,output_dir=str(ROOT),phase='dev',dtype='float32',tf32=False,
        node='node02',gpus=2,workers_per_gpu=1,mem='100G',cpus=8,time='5-00:00:00',
        task_manifest=str(ROOT/'audit/dev_tasks.json'),task_manifest_sha256=sha(ROOT/'audit/dev_tasks.json'),
        source_sha256={str(p):sha(p) for p in sorted(sources)},
        pre_efficacy_validation_required=False,detector_recalibrated=False,
        generation_count=512,gains=[1.,1.25,1.5,2.])
    save(ROOT/'audit/dev_config.json',cfg)
    save(ROOT/'stage8c_v3_fp32_execution_manifest.json',dict(at=at,config=cfg,
        config_sha256=sha(ROOT/'audit/dev_config.json'),
        canonical_comparison='FP32 baseline versus FP32 visual gain',
        prior_evidence_preserved={str(p):sha(p) for p in seals},
        cohort_sha256={str(ROOT/f'stage8c_v3_{n}_manifest.json'):sha(ROOT/f'stage8c_v3_{n}_manifest.json') for n in ['dev128','test512']},
        inherited_subsets_sha256=sha(ROOT/'audit/subsets.json'),
        runtime_dtype_observations='Per-worker environment and per-example precision.json from ordinary development; not a transfer validation',
        dataset_lookup='No project datasets link; frozen allowed external MathVision and pinned model reused. No download.',
        interpretation='Frozen retrieval-aware policy only; no BF16/FP32 equivalence or detector transfer claim'))
    save(ROOT/'audit/prior_preservation.json',dict(at=at,hashes=verified))
    print(json.dumps(dict(tasks=len(tasks),dev=128,test=512,prior_files_verified=len(verified),output_dir=str(ROOT))))


if __name__=='__main__':main()
