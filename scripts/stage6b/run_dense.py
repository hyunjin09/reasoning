"""Exactly two existing GPUs: dense passive extraction with canonical chunk reuse."""
import argparse,gc,os,platform,sys,time
from pathlib import Path
import torch
from scripts.stage6b.common import ROOT,OUT,read_json,read_jsonl,sha,write_json
from visual_reasoning.stage0.modeling import load_runtime,runtime_environment
from visual_reasoning.stage6a.runtime import prepare_condition
from visual_reasoning.stage3c9.streaming import advance_streaming_state,clone_streaming_state
from visual_reasoning.stage4a.runtime import make_event_root
from visual_reasoning.stage6b.protocol import assigned_rank
from visual_reasoning.stage6b.text_interface import prefill_condition
from visual_reasoning.stage6b.dense_partition import endpoint_partition
from visual_reasoning.stage6b.dense_runtime import endpoint_root,collect_endpoint,same_state


def main():
    p=argparse.ArgumentParser();p.add_argument('--manifest',required=True);p.add_argument('--run-id',required=True)
    p.add_argument('--split',choices=['discovery','confirmation']);p.add_argument('--mechanics',action='store_true');p.add_argument('--resume',action='store_true')
    args=p.parse_args();config=read_json(OUT/'config/stage6b_config.json')
    rank=assigned_rank(os.environ,torch.cuda.device_count(),config['slurm_allocation']);torch.cuda.set_device(rank)
    assert 'A6000' in torch.cuda.get_device_name(rank)
    rows=read_jsonl(ROOT/args.manifest)
    if args.split:rows=[r for r in rows if r['split']==args.split]
    bases=list(dict.fromkeys(r['base_id'] for r in rows))
    if args.mechanics:
        assert args.split=='discovery';bases=bases[:2]
    selected={b for i,b in enumerate(bases) if i%2==rank};rows=[r for r in rows if r['base_id'] in selected]
    if not args.mechanics:assert read_json(OUT/'audit/native_dense_mechanics.json')['status']=='PASS'
    assert args.run_id.replace('_','').isalnum()
    code=['scripts/stage6b/run_dense.py','code/visual_reasoning/stage6b/dense_runtime.py',
        'code/visual_reasoning/stage6b/dense_partition.py','code/visual_reasoning/stage6b/text_interface.py',
        'code/visual_reasoning/stage6b/runtime.py','code/visual_reasoning/stage5a/passive.py',
        'code/visual_reasoning/stage4a/runtime.py','code/visual_reasoning/stage3c9/streaming.py']
    sig={'run_id':args.run_id,'rank':rank,'world_size':2,'slurm_job_id':config['slurm_allocation'],'node':platform.node(),
        'manifest_sha256':sha(ROOT/args.manifest),'config_sha256':sha(OUT/'config/stage6b_config.json'),
        'code_sha256':{path:sha(ROOT/path) for path in code},'event_ids':[r['id'] for r in rows],'mechanics':args.mechanics,'split':args.split}
    shard=OUT/'raw'/args.run_id/f'shard_{rank:02d}'
    if (shard/'signature.json').exists():assert args.resume and read_json(shard/'signature.json')==sig
    write_json(shard/'signature.json',sig,freeze=True);write_json(shard/'command.json',{'argv':sys.argv})
    processor,model=load_runtime(Path(config['model_checkpoint']),device=f'cuda:{rank}')
    assert next(model.parameters()).dtype==torch.bfloat16
    write_json(shard/'environment.json',{**runtime_environment(Path(config['model_checkpoint']),model,40960),
        'dtype':str(next(model.parameters()).dtype),'node':platform.node(),'rank':rank,'gpu_name':torch.cuda.get_device_name(rank)})
    begin=time.perf_counter();nspans=0
    for entry in rows:
        path=shard/(entry['id']+'.json')
        if path.exists():
            assert args.resume;nspans+=len(read_json(path)['endpoints']);continue
        spans=entry['spans']
        if args.mechanics:spans=list({s['id']:s for s in spans[:3]+spans[-2:]}.values())
        spans=sorted(spans,key=lambda s:s['token_end'])
        start=time.perf_counter();torch.cuda.reset_peak_memory_stats();output=[];root_checks=[]
        if spans:
            prepared,meta=prepare_condition(processor,entry['row'],f'cuda:{rank}');original=read_json(entry['native_input_path'])
            for k in ['prompt_token_ids','visual_token_indices','image_grid_thw','decoded_image_sha256']:assert meta[k]==original[k],k
            prefill,pa=prefill_condition(model,prepared,entry['row'].get('no_image',False));del prepared
            checkpoint=clone_streaming_state(prefill)
            ids=read_json(entry['native_generation_path'])['generated_token_ids']
            for s in spans:
                end=s['token_end'];boundary,_,_=endpoint_partition(end)
                while checkpoint.generated_length<boundary:
                    left=checkpoint.generated_length
                    advance_streaming_state(model=model,state=checkpoint,token_ids=ids[left:left+2048],seed=1234,chunk_size=2048,release_allocator_cache=True)
                root=endpoint_root(model,checkpoint,ids,end)
                if args.mechanics:
                    event={'history_before_ed_token_ids':ids[:end],'candidate_start_token':end,'current_query_zero_based':end-1}
                    fresh=make_event_root(model,prefill,event);exact=same_state(root,fresh)
                    assert exact
                    root_checks.append({'id':s['id'],'checkpoint_length':boundary,'fresh_canonical_root_exact':exact});del fresh
                passive=collect_endpoint(model,root,ids,end,entry['source_groups'],meta,validate=args.mechanics)
                output.append({**s,'passive':passive});nspans+=1
                del root;torch.cuda.empty_cache()
            del prefill,checkpoint,ids
        record={'id':entry['id'],'base_id':entry['base_id'],'split':entry['split'],'condition':entry['condition'],
            'endpoints':output,'checks':{'all_native_passive_logits_exact':all(s['passive']['native_passive_logits_exact'] for s in output)},
            'fresh_root_mechanics':root_checks,'runtime_seconds':time.perf_counter()-start,
            'peak_allocated_bytes':torch.cuda.max_memory_allocated(),'peak_reserved_bytes':torch.cuda.max_memory_reserved(),
            'manifest_sha256':sig['manifest_sha256']}
        write_json(path,record)
        print(f'rank={rank} {entry["id"]} endpoints={len(output)} seconds={record["runtime_seconds"]:.1f} exact=True',flush=True)
        gc.collect();torch.cuda.empty_cache()
    write_json(shard/'run_summary.json',{'completed':True,'expected_events':len(rows),'endpoints':nspans,'rank':rank,'runtime_seconds':time.perf_counter()-begin})
    print(f'rank={rank} COMPLETE {args.run_id}',flush=True)


if __name__=='__main__':main()
