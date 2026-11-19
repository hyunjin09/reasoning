#!/usr/bin/env python3
"""Run one authorized Stage3C10 phase inside the existing four-GPU allocation."""
import argparse
import gc
import os
import platform
import sys
import time
from pathlib import Path
import torch
from visual_reasoning.stage0.data import load_mathverse_rows
from visual_reasoning.stage0.modeling import load_runtime, runtime_environment
from visual_reasoning.stage3a.runtime import prepare_custom_image
from visual_reasoning.stage3c8.protocol import distributed_process_info
from visual_reasoning.stage3c9.streaming import (prefill_streaming_state, advance_streaming_state,
    clone_streaming_state, roll_streaming_prefix, score_preference_from_streaming_state)
from visual_reasoning.stage3c10.runtime import score_arm
from scripts.stage3c10.freeze_inputs import ROOT, OUT, read_json, read_jsonl, write_json, sha

PHASES=['validation','primary','temporal','layers','mediation','hpre','positions']

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--phase',choices=PHASES,required=True)
    parser.add_argument('--resume',action='store_true'); parser.add_argument('--max-bases',type=int,default=0)
    args=parser.parse_args(); phase=args.phase
    config=read_json(OUT/'config/stage3c10_config.json')
    if os.environ.get('SLURM_JOB_ID')!=config['runtime']['slurm_allocation']: raise RuntimeError('Existing frozen allocation required')
    world,rank,device=distributed_process_info(os.environ,visible_device_count=torch.cuda.device_count())
    if world!=4 or torch.cuda.device_count()!=4: raise RuntimeError('Exactly four assigned GPUs/ranks required')
    torch.cuda.set_device(device)
    if 'A6000' not in torch.cuda.get_device_name(device): raise RuntimeError('A6000 required')
    if phase!='validation' and not read_json(OUT/'audit/mechanical_validation.json')['passed']: raise RuntimeError('Validation gate closed')
    if phase not in ['validation','primary']: read_json(OUT/'phase_b_primary/primary_freeze.json')
    tasks=None
    if phase in ['temporal','layers','hpre']:
        tasks=read_json(OUT/f'analysis/{phase}_tasks.json')['tasks']
    role='validation' if phase=='validation' else 'primary'
    assets=[x for x in read_jsonl(OUT/'config/assets.jsonl') if x['cohort_role']==role][rank::world]
    if args.max_bases: assets=assets[:args.max_bases]
    shard=OUT/f'raw/{phase}/shard_{rank}'
    hashes={str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'code/visual_reasoning/stage3c10/runtime.py',
        ROOT/'code/visual_reasoning/stage3c10/protocol.py',Path(__file__).resolve(),ROOT/'code/visual_reasoning/stage3c3/metrics.py',
        ROOT/'code/visual_reasoning/stage3c4/runtime.py',ROOT/'code/visual_reasoning/stage3c9/streaming.py']}
    cfg={'phase':phase,'rank':rank,'world_size':world,'slurm_job_id':os.environ['SLURM_JOB_ID'],
        'node':platform.node(),'command':sys.argv,'code_sha256':hashes,
        'config_sha256':sha(OUT/'config/stage3c10_config.json'),'max_bases':args.max_bases}
    if (shard/'run_config.json').exists():
        prior=read_json(shard/'run_config.json')
        if prior['code_sha256']!=hashes or prior['config_sha256']!=cfg['config_sha256']: raise RuntimeError('Resume code/config changed')
    write_json(shard/'run_config.json',cfg)
    dataset={str(x['sample_index']):x for x in load_mathverse_rows(Path(config['dataset_root']))}
    processor,model=load_runtime(Path(config['model_checkpoint']),device='cuda')
    assert next(model.parameters()).dtype==torch.bfloat16
    assert model.config.text_config.num_hidden_layers==36 and model.config.text_config.num_attention_heads==32
    write_json(shard/'environment.json',{**runtime_environment(Path(config['model_checkpoint']),model,40960),**cfg,
        'CUDA_VISIBLE_DEVICES':os.environ.get('CUDA_VISIBLE_DEVICES'),'local_device':device})
    start=time.perf_counter(); completed=0
    for item in assets:
        base=item['base_problem_id']; context=item['context']; partition=item['partition']
        pending=[]
        for tid in ['target_a','target_b']:
            for state_name in (['M','T'] if phase in ['validation','primary','positions'] else ['T']):
                applicable=None if tasks is None else [x for x in tasks if x['target_id']==tid]
                if tasks is not None and not applicable: continue
                path=shard/base/tid/f'{state_name}.json'
                if path.exists():
                    if not args.resume: raise FileExistsError(path)
                    continue
                pending.append((tid,state_name,applicable,path))
        if not pending: continue
        prepared,meta=prepare_custom_image(processor,dataset[item['example_id']],ROOT/item['image_path'],device='cuda')
        assert meta['prompt_token_ids']==item['prompt_token_ids'] and meta['image_grid_thw']==item['image_grid_thw']
        assert meta['visual_token_indices']==item['visual_positions']
        prefill,prefill_audit=prefill_streaming_state(model=model,prepared=prepared,seed=1234); del prepared
        roots={}; needed={item['states'][tid][s]['current_zero_based_index'] for tid,s,_,_ in pending}
        current=clone_streaming_state(prefill)
        for left,right in partition:
            if left in needed: roots[left]=clone_streaming_state(current)
            advance_streaming_state(model=model,state=current,token_ids=context[left:right],seed=1234,
                                    chunk_size=2048,release_allocator_cache=True)
        del current,prefill
        for tid,state_name,applicable,path in pending:
            t0=time.perf_counter(); target=config['targets'][tid]; st=item['states'][tid][state_name]
            current_index=st['current_zero_based_index']; root=roots[current_index]; windows=st['source_windows_generated_zero_based']
            upstream=list(range(target['layer_index'])); groups=item['routing_groups']
            arms={}; donors={}
            def run(name,trigger,scope,rois=('none','T','I'),rescue=None,gain=0.):
                result={}
                for roi in rois:
                    output,donor=score_arm(model=model,root=root,context=context,partition=partition,
                        target=target,groups=groups,trigger_positions=trigger,trigger_layers=scope,
                        roi_positions=groups[roi] if roi!='none' else [],
                        donor_q=donors['N']['q'] if rescue in ['all','selected','self'] else None,
                        rescue_heads=list(range(32)) if rescue in ['all','self'] else target['causal_heads'] if rescue=='selected' else [],
                        donor_hpre=donors['N']['hpre'] if rescue=='hpre' else None,gain=gain,
                        original_suffix=item['original_suffix'],counterfactual_suffix=item['counterfactual_suffix'],
                        validate=phase=='validation')
                    result[roi]=output
                    if roi=='none': donors[name]=donor
                arms[name]=result
            run('N',[],[],rois=('none','T','I') if phase in ['validation','primary'] else ('none','T'))
            r16=[root.prompt_length+i for i in windows['R16']]
            if phase in ['validation','primary','mediation','hpre']:
                run('R16',r16,upstream,rois=('none','T','I') if phase in ['validation','primary'] else ('none','T'))
            if phase in ['validation','primary']:
                if windows['E16'] is not None: run('E16',[root.prompt_length+i for i in windows['E16']],upstream)
                run('Q',item['Q_positions'],upstream)
            checks={}
            if phase=='validation':
                run('noop_R16',r16,upstream,rois=('none',),gain=1.)
                run('replay_R16',r16,upstream,rois=('none',))
                run('self_Q',[],[],rois=('none',),rescue='self')
                run('Q_all',r16,upstream,rois=('none','T'),rescue='all')
                run('Q_selected',r16,upstream,rois=('none','T'),rescue='selected')
                checks['noop_exact']=arms['N']['none']['D']==arms['noop_R16']['none']['D'] and arms['N']['none']['routing']==arms['noop_R16']['none']['routing']
                checks['replay_exact']=arms['R16']['none']==arms['replay_R16']['none']
                checks['self_Q_exact']=arms['N']['none']['D']==arms['self_Q']['none']['D'] and arms['N']['none']['routing']==arms['self_Q']['none']['routing']
                barriers=[right for _,right in partition if current_index<right<len(context)]
                for roi in ['none','T']:
                    rolled,audit=roll_streaming_prefix(model=model,prefill=root,prefix_token_ids=context,
                        end_generated_index=len(context),seed=1234,layers=list(range(36)) if roi=='T' else [],
                        selected_heads=list(range(32)) if roi=='T' else [],source_positions=groups['T'] if roi=='T' else [],
                        suppressed_generated_indices=[current_index] if roi=='T' else [],chunk_size=2048,
                        forced_generated_boundaries=barriers,release_allocator_cache=True)
                    score=score_preference_from_streaming_state(model=model,state=rolled,original_suffix_ids=item['original_suffix'],counterfactual_suffix_ids=item['counterfactual_suffix'],seed=1234)
                    checks[f'inherited_{roi}_exact']=all(score[k]==arms['N'][roi][k] for k in ['D','L_o','L_c','original_candidate','counterfactual_candidate'])
                    checks[f'inherited_{roi}_audit']=audit
                    del rolled
            elif phase=='temporal':
                for k in [1,2,4,8,16]: run(f'R{k}',[root.prompt_length+i for i in windows[f'R{k}']],upstream,rois=('none','T'))
            elif phase=='layers':
                for task in applicable:
                    run(task['arm'],[root.prompt_length+i for i in windows[f"R{task['k']}"]],task['layers'],rois=('none','T'))
            elif phase=='mediation':
                run('Q_all',r16,upstream,rois=('none','T'),rescue='all')
                run('Q_selected',r16,upstream,rois=('none','T'),rescue='selected')
            elif phase=='hpre': run('hpre',r16,upstream,rois=('none','T'),rescue='hpre')
            elif phase=='positions':
                for distance in range(1,9):
                    positions=windows[f'P{distance}']
                    if positions is not None: run(f'P{distance}',[root.prompt_length+i for i in positions],upstream,rois=('none','T'))
            if phase not in ['validation','primary']:
                original=next((OUT/'raw/primary').glob(f'shard_*/{base}/{tid}/{state_name}.json'))
                old=read_json(original)
                checks['primary_baseline_exact']=all(arms[a][r]['D']==old['arms'][a][r]['D'] and arms[a][r]['rds']==old['arms'][a][r]['rds'] for a in ['N','R16'] if a in arms for r in ['none','T'])
                if not checks['primary_baseline_exact']: raise RuntimeError('Same-path primary baseline replay failed')
            result={'base_problem_id':base,'target_id':tid,'state':state_name,'phase':phase,
                'frozen_state':st,'routing_layer':target['layer_index'],'partition':partition,
                'arms':arms,'validation_checks':checks,'prefill_audit':prefill_audit,
                'config_sha256':cfg['config_sha256'],'code_sha256':hashes,
                'runtime_seconds':time.perf_counter()-t0,'peak_gpu_allocated_bytes':torch.cuda.max_memory_allocated(),
                'peak_gpu_reserved_bytes':torch.cuda.max_memory_reserved()}
            partial=path.with_suffix('.part'); write_json(partial,result); partial.replace(path)
            completed+=1
            print(f'rank={rank} phase={phase} base={base} target={tid} state={state_name} arms={len(arms)} seconds={time.perf_counter()-t0:.1f}',flush=True)
            del arms,donors
        del roots
        gc.collect();torch.cuda.empty_cache()
    write_json(shard/'run_summary.json',{'phase':phase,'rank':rank,'completed':completed,'runtime_seconds':time.perf_counter()-start})
    print(f'rank={rank} COMPLETE {phase} new={completed}',flush=True)

if __name__=='__main__': main()
