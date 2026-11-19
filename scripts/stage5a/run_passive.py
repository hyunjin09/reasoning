"""PhaseE current/prior telemetry, gated by frozen semantic and causal labels."""
import argparse,gc,os,platform,re,sys,time
from datetime import datetime,timezone
from pathlib import Path
import torch
from scripts.stage5a.prepare import ROOT,OUT,read_json,read_jsonl,write_json,sha
from scripts.stage5a.run_scores import verify_freeze,atomic_json,score_equal
from visual_reasoning.stage0.data import load_mathverse_rows
from visual_reasoning.stage0.modeling import load_runtime,runtime_environment
from visual_reasoning.stage3a.runtime import prepare_custom_image
from visual_reasoning.stage3c8.protocol import distributed_process_info
from visual_reasoning.stage3c9.streaming import prefill_streaming_state
from visual_reasoning.stage5a.passive import collect_event


def verify_labels():
    verify_freeze();f=read_json(OUT/'annotations/causal_label_freeze.json')
    for p,h in f['sha256'].items():assert sha(ROOT/p)==h,p
    assert f['protocol_sha256']==sha(ROOT/'code/visual_reasoning/stage5a/protocol.py')
    assert f['causal_gate_sha256']==sha(OUT/'phase_b_causal/causal_run_complete.json')
    assert f['semantic_gate_sha256']==sha(OUT/'phase_c_counterfactual/semantic_run_complete.json')
    return f


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run-id',required=True);parser.add_argument('--allocation-id',default='108548')
    parser.add_argument('--resume',action='store_true');a=parser.parse_args()
    assert re.fullmatch(r'passive_\d{2}',a.run_id)
    verify_labels();rules=read_json(OUT/'config/passive_extraction_rule.json')
    assert os.environ.get('SLURM_JOB_ID')==a.allocation_id
    world,rank,device=distributed_process_info(os.environ,visible_device_count=torch.cuda.device_count())
    assert world==torch.cuda.device_count()==4
    torch.cuda.set_device(device);assert 'A6000' in torch.cuda.get_device_name(device)
    primary=read_json(OUT/'phase_b_causal/causal_run_complete.json')
    originals={(r['base_problem_id'],r['event']):r for p in (OUT/'raw'/primary['run_id']).glob('shard_*/*/O/*.json') for r in [read_json(p)]}
    code=['scripts/stage5a/run_passive.py','code/visual_reasoning/stage5a/passive.py',*primary['code_sha256']]
    signature={'phase':'passive','run_id':a.run_id,'rank':rank,'world_size':world,'slurm_job_id':a.allocation_id,'node':platform.node(),
        'command':sys.argv,'started_at':datetime.now(timezone.utc).isoformat(),'labels_sha256':sha(OUT/'annotations/causal_label_freeze.json'),
        'code_sha256':{p:sha(ROOT/p) for p in code},'rules_sha256':sha(OUT/'config/passive_extraction_rule.json'),
        'passive_only':True,'source_interventions':False}
    shard=OUT/'raw'/a.run_id/f'shard_{rank:02d}'
    if (shard/'run_config.json').exists():
        old=read_json(shard/'run_config.json')
        assert a.resume and all(old[k]==signature[k] for k in ('labels_sha256','code_sha256','rules_sha256','slurm_job_id'))
    write_json(shard/'run_config.json',signature)
    config=read_json(OUT/'config/stage5a_config.json')
    rows={str(r['sample_index']):r for r in load_mathverse_rows(Path(config['dataset_root']))}
    processor,model=load_runtime(Path(config['model_checkpoint']),device='cuda');assert next(model.parameters()).dtype==torch.bfloat16
    write_json(shard/'environment.json',{**runtime_environment(Path(config['model_checkpoint']),model,40960),**signature,'local_device':device})
    start=time.perf_counter();count=0
    for item in read_jsonl(OUT/'cohort/causal_atlas_manifest.jsonl')[rank::world]:
        base=item['base_problem_id'];meta=read_json(ROOT/item['asset_metadata'])
        pending=[e for e in meta['events'] if not (shard/base/(e['event']+'.json')).exists()]
        if not pending:continue
        prepared,layout=prepare_custom_image(processor,rows[item['example_id']],ROOT/meta['paths']['O'],device='cuda')
        assert all(layout[k]==meta['prompt_metadata'][k] for k in ('prompt_token_ids','visual_token_indices','image_grid_thw'))
        prefill,prefill_audit=prefill_streaming_state(model=model,prepared=prepared,seed=1234);del prepared
        for e in pending:
            t=time.perf_counter();current=collect_event(model,processor,prefill,meta,e)
            assert score_equal(current,originals[base,e['event']]['arms']['N']),'Passive native replay differs'
            prior=collect_event(model,processor,prefill,meta,e,prior=True)
            result={'base_problem_id':base,'event':e['event'],'event_id':e['event_id'],'split':item['split'],
                'run_id':a.run_id,'current':current,'prior':prior,'native_causal_replay_exact':True,'prefill_audit':prefill_audit,
                'runtime_seconds':time.perf_counter()-t,'peak_gpu_allocated_bytes':torch.cuda.max_memory_allocated(),
                'peak_gpu_reserved_bytes':torch.cuda.max_memory_reserved(),'asset_metadata_sha256':item['asset_metadata_sha256']}
            atomic_json(shard/base/(e['event']+'.json'),result);count+=1
            print(f'rank={rank} passive base={base} event={e["event"]} exact=True seconds={result["runtime_seconds"]:.1f}',flush=True)
        del prefill;gc.collect();torch.cuda.empty_cache()
    write_json(shard/'run_summary.json',{'rank':rank,'completed':True,'new_events':count,'runtime_seconds':time.perf_counter()-start})
    print(f'rank={rank} COMPLETE {a.run_id} new={count}',flush=True)


if __name__=='__main__':main()
