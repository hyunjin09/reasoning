"""One-GPU native generation, with exact input provenance and resumable outputs."""
import argparse
import gc
import os
import platform
import resource
import sys
import time
from pathlib import Path
import torch
from scripts.stage7a.common import ROOT, OUT, read_json, read_jsonl, sha, write_json, write_jsonl, configure_fresh_processor
from visual_reasoning.stage0.modeling import load_runtime, runtime_environment, generate_once
from visual_reasoning.stage1.protocol import protocol_parameters, transformers_generation_kwargs
from visual_reasoning.stage6a.runtime import prepare_condition


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--run-id', required=True)
    p.add_argument('--manifest', required=True)
    p.add_argument('--mechanics', action='store_true')
    p.add_argument('--resume', action='store_true')
    args = p.parse_args()
    config = read_json(OUT/'config/stage7a_config.json')
    assert os.environ['SLURM_JOB_ID'] == config['runtime']['slurm_allocation']
    assert platform.node().split('.')[0] == config['runtime']['node']
    assert torch.cuda.device_count() == 1 and 'A6000' in torch.cuda.get_device_name(0)
    path = ROOT/args.manifest
    entries = read_jsonl(path)
    if args.mechanics:
        assert all(r.get('stage7a_role') == 'historical mechanics only' and not r['fresh_confirmation'] for r in entries)
        rows = [r['row'] for r in entries]
    else:
        assert (OUT/'audit/native_generation_mechanics.json').is_file()
        assert (OUT/'cohort/discovery_confirmation_split.json').is_file()
        assert (OUT/'audit/cohort_freeze.json').is_file()
        frozen=read_json(OUT/'audit/cohort_freeze.json')
        assert sha(path) in frozen['native_manifest_sha256'].values()
        rows = entries
    cap = 128 if args.mechanics else config['locked_generation_protocol']['max_new_tokens']
    dependencies=['scripts/stage7a/run_generation.py','scripts/stage7a/common.py',
        'code/visual_reasoning/stage0/modeling.py','code/visual_reasoning/stage1/protocol.py',
        'code/visual_reasoning/stage6a/runtime.py']
    signature = dict(manifest_sha256=sha(path),config_sha256=sha(OUT/'config/stage7a_config.json'),
        code_sha256=sha(Path(__file__)),event_ids=[r['event_id'] for r in rows],
        slurm_job_id=os.environ['SLURM_JOB_ID'],mechanics=args.mechanics,max_new_tokens=cap,
        image_budget_sha256=None if args.mechanics else sha(OUT/'config/image_preprocessing.json'),
        dependency_sha256={p:sha(ROOT/p) for p in dependencies})
    dest = OUT/'native'/args.run_id
    if (dest/'signature.json').exists() and not args.resume:
        raise RuntimeError('Existing run requires explicit resume')
    write_json(dest/'signature.json',signature,freeze=True)
    for source in dependencies:
        target=dest/'source_snapshot'/source
        target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists():assert target.read_bytes()==(ROOT/source).read_bytes()
        else:target.write_bytes((ROOT/source).read_bytes())
    processor,model = load_runtime(Path(config['model_checkpoint']),device='cuda:0')
    if not args.mechanics:
        configure_fresh_processor(processor)
    write_json(dest/'environment.json',dict(
        **runtime_environment(Path(config['model_checkpoint']),model,cap),
        sys_prefix=sys.prefix,requested_python=str(ROOT/'.venv/bin/python'),
        parameter_dtype=str(next(model.parameters()).dtype),slurm_job_id=os.environ['SLURM_JOB_ID'],
        node=platform.node(),world_size=1))
    parameters = protocol_parameters('official',cap,config['locked_generation_protocol']['seed'])
    kwargs = transformers_generation_kwargs(parameters)
    eos = model.generation_config.eos_token_id
    eos = [eos] if isinstance(eos,int) else eos
    results=[]
    for i,row in enumerate(rows):
        example=dest/'examples'/row['event_id']
        if (example/'result.json').exists():
            results.append(read_json(example/'result.json'))
            continue
        start=time.perf_counter()
        if not args.mechanics and row.get('image_path'):
            assert sha(row['image_path'])==row['image_sha256']
        prepared,meta=prepare_condition(processor,row,'cuda:0')
        write_json(example/'input.json',meta,freeze=True)
        write_json(example/'manifest_row.json',row,freeze=True)
        generation=generate_once(model,processor,prepared,cap,recorder=None,
            generation_kwargs=kwargs,seed=parameters['seed'],collect_predictive_metrics=False)
        tokens=generation.pop('token_rows');generation.pop('attention_arrays',None)
        write_json(example/'generation.json',generation)
        write_jsonl(example/'tokens.jsonl',tokens)
        ids=generation['generated_token_ids'];ended=bool(ids and ids[-1] in eos)
        checks={}
        if args.mechanics:
            reference=read_json(entries[i]['native_generation_path'])['generated_token_ids']
            checks['historical_native_prefix_exact']=ids==reference[:len(ids)]
            repeated=generate_once(model,processor,prepared,cap,recorder=None,
                generation_kwargs=kwargs,seed=parameters['seed'],collect_predictive_metrics=False)
            checks['repeat_token_ids_exact']=ids==repeated['generated_token_ids']
            del repeated
        result=dict(event_id=row['event_id'],base_id=row['base_id'],cohort=row['cohort'],
            condition=row['condition'],split=row.get('split'),complete=ended and '</think>' in generation['raw_decoded_response'],
            ended_with_eos=ended,truncated=len(ids)>=cap and not ended,token_count=len(ids),
            mechanics_only=args.mechanics,checks=checks,runtime=generation['runtime'],
            elapsed_seconds=time.perf_counter()-start,peak_host_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            artifact_dir=str(example.relative_to(ROOT)),manifest_sha256=signature['manifest_sha256'])
        write_json(example/'result.json',result)
        if not all(checks.values()):raise RuntimeError('Native generation mechanics failed: '+row['event_id'])
        results.append(result)
        print(f"{i+1}/{len(rows)} {row['event_id']} tokens={len(ids)} eos={ended} seconds={result['elapsed_seconds']:.1f}",flush=True)
        del prepared,generation,tokens;gc.collect();torch.cuda.empty_cache()
    summary=dict(completed=True,mechanics_only=args.mechanics,results=results)
    write_json(dest/'run_summary.json',summary)
    write_json(OUT/'raw'/args.run_id/'run_summary.json',summary)
    if args.mechanics:
        write_json(OUT/'audit/native_generation_mechanics.json',dict(passed=True,evidence=str(dest.relative_to(ROOT)),
            max_new_tokens=128,scientific_use=False,checks=[r['checks'] for r in results]))


if __name__=='__main__':main()
