"""Four independent A6000 ranks; native generation and mechanics replay only."""
import argparse
import gc
import hashlib
import json
import os
from pathlib import Path
from datetime import datetime, timezone
import torch
from visual_reasoning.stage0.modeling import load_runtime, runtime_environment, generate_once
from visual_reasoning.stage1.protocol import protocol_parameters, transformers_generation_kwargs
from visual_reasoning.stage6a.runtime import prepare_condition

ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs/stage6a'


def dump(path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--manifest',required=True);parser.add_argument('--run',required=True)
    parser.add_argument('--replay-baselines',action='store_true');args=parser.parse_args()
    config=json.loads((OUT/'config/stage6a_config.json').read_text())
    rank=int(os.environ['LOCAL_RANK']);world=int(os.environ['WORLD_SIZE'])
    if world!=4 or torch.cuda.device_count()!=4:raise RuntimeError('Exactly four assigned GPUs required')
    if os.environ.get('SLURM_JOB_ID')!=config['runtime']['slurm_allocation']:raise RuntimeError('Use existing user allocation')
    torch.cuda.set_device(rank)
    if 'A6000' not in torch.cuda.get_device_name(rank):raise RuntimeError('A6000 only')
    path=ROOT/args.manifest;raw=path.read_bytes();manifest=[json.loads(l) for l in raw.decode().splitlines()]
    manifest_sha=hashlib.sha256(raw).hexdigest()
    dest=OUT/'native'/args.run/f'shard_{rank:02d}'
    signature=dict(manifest=str(path),manifest_sha256=manifest_sha,config=config,rank=rank,world=world,
        replay_baselines=args.replay_baselines,slurm_job_id=os.environ['SLURM_JOB_ID'])
    if (dest/'config.json').exists():
        if json.loads((dest/'config.json').read_text())!=signature:raise RuntimeError('Resume signature mismatch')
    else:dump(dest/'config.json',signature)
    processor,model=load_runtime(Path(config['model_checkpoint']),device=f'cuda:{rank}')
    dump(dest/'environment.json',{**runtime_environment(Path(config['model_checkpoint']),model,40960),
        'local_rank':rank,'parameter_dtype':str(next(model.parameters()).dtype),
        'observed_node':os.uname().nodename,'created_at':datetime.now(timezone.utc).isoformat()})
    protocol=config['locked_generation_protocol'];seed=protocol['seed'];cap=protocol['max_new_tokens']
    parameters=protocol_parameters('official',cap,seed)
    assert all(parameters[k]==protocol[k] for k in protocol if k!='name')
    kwargs=transformers_generation_kwargs(parameters)
    eos=model.generation_config.eos_token_id;eos=[eos] if isinstance(eos,int) else eos
    results=[]
    for i,row in enumerate(manifest[rank::world]):
        example=dest/'examples'/row['event_id'];result_path=example/'result.json'
        if result_path.exists():results.append(json.loads(result_path.read_text()));continue
        prepared,metadata=prepare_condition(processor,row,f'cuda:{rank}')
        dump(example/'input.json',metadata);dump(example/'manifest_row.json',row)
        generation=generate_once(model,processor,prepared,cap,recorder=None,generation_kwargs=kwargs,seed=seed,collect_predictive_metrics=False)
        tokens=generation.pop('token_rows');generation.pop('attention_arrays',None)
        dump(example/'generation.json',generation)
        (example/'tokens.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in tokens))
        ids=generation['generated_token_ids'];ended=bool(ids and ids[-1] in eos)
        replay=None
        if args.replay_baselines and row['condition'] in ('intact','AR'):
            # Identical native cached execution, seed, input and GPU. No cross-shape
            # absolute-score parity claim is made.
            repeated=generate_once(model,processor,prepared,cap,recorder=None,generation_kwargs=kwargs,seed=seed,collect_predictive_metrics=False)
            replay=dict(token_ids_exact=ids==repeated['generated_token_ids'],
                raw_text_exact=generation['raw_decoded_response']==repeated['raw_decoded_response'],
                repeated_token_count=repeated['generated_token_count'],runtime=repeated['runtime'])
            dump(example/'deterministic_replay.json',replay)
            if not replay['token_ids_exact'] or not replay['raw_text_exact']:raise RuntimeError('Native replay mismatch')
            del repeated
        result=dict(event_id=row['event_id'],base_id=row['base_id'],cohort=row['cohort'],condition=row['condition'],
            phase=row.get('phase'),ended_with_eos=ended,truncated=len(ids)>=cap and not ended,
            complete=ended and '</think>' in generation['raw_decoded_response'],
            token_count=len(ids),runtime=generation['runtime'],native_replay=replay,
            artifact_dir=str(example.relative_to(ROOT)),manifest_sha256=manifest_sha,
            token_decode_exact=''.join(r['decoded_token'] for r in tokens)==generation['raw_decoded_response'],
            membership_used_attention=False,membership_used_causal_scores=False)
        dump(result_path,result);results.append(result)
        print(f"rank={rank} {i+1}/{len(manifest[rank::world])} {row['event_id']} tokens={len(ids)} eos={ended} seconds={generation['runtime']['elapsed_seconds']:.1f}",flush=True)
        del prepared,generation,tokens
        gc.collect();torch.cuda.empty_cache()
    dump(dest/'result.json',dict(rank=rank,complete=True,results=results))
    print(f'rank={rank} COMPLETE {len(results)}',flush=True)


if __name__=='__main__':main()
