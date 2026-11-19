"""Frozen Stage5A source/trigger/semantic scoring on exactly four assigned A6000s."""
import argparse,gc,os,platform,re,sys,time
from pathlib import Path
import torch
from scripts.stage5a.prepare import ROOT,OUT,read_json,read_jsonl,write_json,sha
from visual_reasoning.stage0.data import load_mathverse_rows
from visual_reasoning.stage0.modeling import load_runtime,runtime_environment
from visual_reasoning.stage3a.runtime import prepare_custom_image
from visual_reasoning.stage3c8.protocol import distributed_process_info
from visual_reasoning.stage3c9.streaming import prefill_streaming_state
from visual_reasoning.stage4a.runtime import make_event_root,score_event_arm


def score_equal(a,b):
    return all(a[k]==b[k] for k in ('D','L_o','L_c','current_logits_sha256','original_candidate','counterfactual_candidate'))


def verify_freeze():
    frozen=read_json(OUT/'cohort/cohort_freeze_complete.json')
    for p,h in {**frozen['sha256'],**frozen['asset_metadata_sha256'],**frozen['native_provenance_sha256']}.items():
        if sha(ROOT/p)!=h:raise RuntimeError('Frozen input changed: '+p)
    if sha(ROOT/'code/visual_reasoning/stage5a/protocol.py')!=frozen['stage5a_protocol_sha256']:
        raise RuntimeError('Frozen classification implementation changed')
    return frozen


def atomic_json(path,value):
    temporary=path.with_suffix('.part');write_json(temporary,value);temporary.replace(path)


def validation_events(meta):
    result=[]
    for name,old in meta['events'].items():
        source=old['fact'];other='B' if source=='A' else 'A'
        g={'T':meta['source_groups'][source],'X':meta['source_groups'][other],
           'joint':sorted(set(meta['source_groups']['A'])|set(meta['source_groups']['B']))}
        if meta.get('irrelevant_controls_validated'):g['I']=meta['source_groups']['I_'+source]
        result.append({**old,'event':name,'event_id':meta['base_problem_id']+'_'+name,'source_groups':g})
    return result


def main():
    p=argparse.ArgumentParser();p.add_argument('--phase',choices=['validation','causal','semantic'],required=True)
    p.add_argument('--run-id',required=True);p.add_argument('--resume',action='store_true')
    p.add_argument('--allocation-id',default='108548');args=p.parse_args()
    if not re.fullmatch(args.phase+r'_\d{2}',args.run_id):raise ValueError('Use phase_NN run ID')
    config=read_json(OUT/'config/stage5a_config.json');freeze=verify_freeze()
    if os.environ.get('SLURM_JOB_ID')!=args.allocation_id:raise RuntimeError('Recorded user-authorized interactive allocation required')
    world,rank,device=distributed_process_info(os.environ,visible_device_count=torch.cuda.device_count())
    if world!=4 or torch.cuda.device_count()!=4:raise RuntimeError('Exactly four assigned GPUs/ranks required')
    torch.cuda.set_device(device)
    if 'A6000' not in torch.cuda.get_device_name(device):raise RuntimeError('Frozen A6000 path required')
    if args.phase!='validation' and not read_json(OUT/'audit/mechanical_validation.json')['passed']:
        raise RuntimeError('Mechanical gate closed')
    if args.phase=='semantic' and not read_json(OUT/'phase_b_causal/causal_run_complete.json')['passed']:
        raise RuntimeError('Complete source run required for exact native denominator comparison')
    manifest={'validation':'cohort/validation_manifest.jsonl','causal':'cohort/causal_atlas_manifest.jsonl',
              'semantic':'phase_c_counterfactual/subset_manifest.jsonl'}[args.phase]
    items=read_jsonl(OUT/manifest)[rank::world];shard=OUT/'raw'/args.run_id/f'shard_{rank:02d}'
    code=['scripts/stage5a/run_scores.py','code/visual_reasoning/stage4a/runtime.py',
          'code/visual_reasoning/stage3c10/runtime.py','code/visual_reasoning/stage3c9/streaming.py',
          'code/visual_reasoning/stage3c4/runtime.py','code/visual_reasoning/stage3c3/runtime.py',
          'code/visual_reasoning/stage0/modeling.py']
    signature={'phase':args.phase,'run_id':args.run_id,'rank':rank,'world_size':world,'slurm_job_id':args.allocation_id,
               'node':platform.node(),'command':sys.argv,'code_sha256':{s:sha(ROOT/s) for s in code},
               'cohort_freeze_sha256':sha(OUT/'cohort/cohort_freeze_complete.json'),'manifest_sha256':sha(OUT/manifest),
               'passive_telemetry_enabled':False,'source_windows':[2,8],'trigger_R':16,'trigger_layers':list(range(16,24))}
    if (shard/'run_config.json').exists():
        old=read_json(shard/'run_config.json')
        for key in ('code_sha256','cohort_freeze_sha256','manifest_sha256','slurm_job_id'):
            if old[key]!=signature[key]:raise RuntimeError('Resume signature changed; preserve attempt and use a new run ID')
        if not args.resume:raise FileExistsError(shard)
    write_json(shard/'run_config.json',signature)
    dataset={str(r['sample_index']):r for r in load_mathverse_rows(Path(config['dataset_root']))}
    processor,model=load_runtime(Path(config['model_checkpoint']),device='cuda')
    if next(model.parameters()).dtype!=torch.bfloat16:raise RuntimeError('BF16 required')
    if model.config.text_config.num_hidden_layers!=36 or model.config.text_config.num_attention_heads!=32:
        raise RuntimeError('Frozen architecture mismatch')
    write_json(shard/'environment.json',{**runtime_environment(Path(config['model_checkpoint']),model,40960),**signature,
               'local_device':device,'slurm_visible_devices':os.environ.get('CUDA_VISIBLE_DEVICES')})
    started=time.perf_counter();completed=0
    for item in items:
        base=item['base_problem_id'];meta=read_json(ROOT/item['asset_metadata'])
        if sha(ROOT/item['asset_metadata'])!=item['asset_metadata_sha256']:raise RuntimeError('Metadata hash mismatch')
        validation=args.phase=='validation';events=validation_events(meta) if validation else meta['events']
        if args.phase=='semantic':events=[e for e in events if e['cf_validated']]
        conditions=['OO'] if validation else list(dict.fromkeys(c for e in events for c in e['cf_conditions'])) if args.phase=='semantic' else ['O']
        for condition in conditions:
            pending=[e for e in events if (args.phase!='semantic' or condition in e['cf_conditions']) and not (shard/base/condition/(e['event']+'.json')).exists()]
            if not pending:continue
            inputs,observed=prepare_custom_image(processor,dataset[item['example_id']],ROOT/meta['paths'][condition],device='cuda')
            for key in ('prompt_token_ids','visual_token_indices','image_grid_thw'):
                if observed[key]!=meta['prompt_metadata'][key]:raise RuntimeError(f'Layout changed: {base}/{condition}/{key}')
            if processor.tokenizer.decode([observed['prompt_token_ids'][0]])!='<|im_start|>':raise RuntimeError('Unexpected sink token')
            prefill,prefill_audit=prefill_streaming_state(model=model,prepared=inputs,seed=1234);del inputs
            for event in pending:
                t0=time.perf_counter();root=make_event_root(model,prefill,event);arms={};checks={}
                event_meta={'source_groups':event['source_groups']}
                def run(name,**kw):
                    result=score_event_arm(model,root,event_meta,event,validate=validation,telemetry=False,**kw)
                    # PhaseE is the only passive-feature extraction phase.
                    result.pop('predictive_entropy',None);arms[name]=result
                run('N')
                if validation or args.phase=='causal':
                    for role in ('T','M','X','I','joint'):
                        if role in event['source_groups']:run(role+'_W2',roi=role)
                    run('T_W8',roi='T',window=8)
                    if validation or meta.get('trigger_selected'):
                        run('R16',trigger=True);run('R16_T_W2',trigger=True,roi='T')
                        alt='X' if 'X' in event['source_groups'] else 'M' if 'M' in event['source_groups'] else None
                        if alt:run('R16_'+alt+'_W2',trigger=True,roi=alt)
                if validation:
                    joint='joint' if 'joint' in event['source_groups'] else 'T'
                    run('noop_joint_W8',roi=joint,window=8,gain=1.)
                    run('noop_R16_joint_W2',roi=joint,trigger=True,gain=1.)
                    run('unhooked',hooked=False);run('replay_T_W2',roi='T')
                    checks={'noop_joint_exact':score_equal(arms['N'],arms['noop_joint_W8']),
                            'noop_trigger_exact':score_equal(arms['N'],arms['noop_R16_joint_W2']),
                            'unhooked_exact':score_equal(arms['N'],arms['unhooked']),
                            'replay_exact':arms['T_W2']==arms['replay_T_W2']}
                    if not all(checks.values()):raise RuntimeError(f'Mechanical check failed: {base}/{event["event"]}/{checks}')
                if args.phase=='semantic' and condition=='O':
                    primary=read_json(OUT/'phase_b_causal/causal_run_complete.json')
                    paths=list((OUT/'raw'/primary['run_id']).glob(f'shard_*/{base}/O/{event["event"]}.json'))
                    if len(paths)!=1:raise RuntimeError('Missing unique primary denominator')
                    checks['primary_native_exact']=score_equal(arms['N'],read_json(paths[0])['arms']['N'])
                    if not checks['primary_native_exact']:raise RuntimeError('Canonical native denominator replay mismatch')
                result={'base_problem_id':base,'example_id':item['example_id'],'event':event['event'],'event_id':event['event_id'],
                        'condition':condition,'phase':args.phase,'run_id':args.run_id,'cohort_split':item['split'],
                        'asset_metadata_sha256':item['asset_metadata_sha256'],'event_history_sha256':event['history_before_ed_sha256'],
                        'arms':arms,'validation_checks':checks,'prefill_audit':prefill_audit,'image_layout_exact':True,
                        'final_correct':item['final_correct'],'local_correctness':event.get('local_correctness','CORRECT'),
                        'runtime_seconds':time.perf_counter()-t0,'peak_gpu_allocated_bytes':torch.cuda.max_memory_allocated(),
                        'peak_gpu_reserved_bytes':torch.cuda.max_memory_reserved(),'passive_features_extracted':False}
                atomic_json(shard/base/condition/(event['event']+'.json'),result);completed+=1
                print(f'rank={rank} phase={args.phase} base={base} image={condition} event={event["event"]} arms={len(arms)} seconds={result["runtime_seconds"]:.1f}',flush=True)
                del root,arms
            del prefill;gc.collect();torch.cuda.empty_cache()
    write_json(shard/'run_summary.json',{'phase':args.phase,'run_id':args.run_id,'rank':rank,'new_event_files':completed,
               'runtime_seconds':time.perf_counter()-started,'completed':True})
    print(f'rank={rank} COMPLETE {args.run_id} new={completed}',flush=True)


if __name__=='__main__':main()
