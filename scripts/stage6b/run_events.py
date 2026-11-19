"""Exactly two independent A6000 ranks inside the existing user allocation."""
import argparse
import gc
import os
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import torch

from scripts.stage6b.common import ROOT, OUT, read_json, read_jsonl, sha, write_json
from visual_reasoning.stage0.modeling import load_runtime, runtime_environment
from visual_reasoning.stage6a.runtime import prepare_condition
from visual_reasoning.stage3c9.streaming import prefill_streaming_state
from visual_reasoning.stage4a.runtime import make_event_root, score_event_arm
from visual_reasoning.stage6b.protocol import assigned_rank
from visual_reasoning.stage6b.runtime import collect_passive, score_equal
from visual_reasoning.stage6b.text_interface import prefill_condition, validate_text_replay


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--split', choices=['discovery','confirmation'])
    parser.add_argument('--mechanics', action='store_true')
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--audit-tag', required=True)
    parser.add_argument('--confirmation-freeze', required=True)
    args = parser.parse_args()
    config = read_json(OUT/'config/stage6b_config.json')
    rank = assigned_rank(os.environ, torch.cuda.device_count(), config['slurm_allocation'])
    torch.cuda.set_device(rank)
    if 'A6000' not in torch.cuda.get_device_name(rank):
        raise RuntimeError('Canonical A6000 hardware required')
    if not args.run_id.replace('_','').isalnum():
        raise ValueError('Unsafe run id')
    manifest = ROOT/args.manifest
    rows = read_jsonl(manifest)
    if args.split:
        rows = [r for r in rows if r['split']==args.split]
    families = list(dict.fromkeys(r['base_id'] for r in rows))
    if args.mechanics:
        # First two discovery families, retaining every frozen condition per family.
        families = families[:2]
        if any(r['split']!='discovery' for r in rows if r['base_id'] in families):
            raise RuntimeError('Mechanics may not expose confirmation effects')
    selected = {base for i,base in enumerate(families) if i%2==rank}
    rows = [r for r in rows if r['base_id'] in selected]
    if not args.mechanics and not (OUT/'audit'/f'{args.audit_tag}_mechanics.json').is_file():
        raise RuntimeError('Mechanics acceptance must precede primary scoring')
    if args.split=='confirmation' and not (ROOT/args.confirmation_freeze).is_file():
        raise RuntimeError('Discovery rules must be frozen before confirmation scoring')
    code = ['scripts/stage6b/run_events.py','code/visual_reasoning/stage6b/text_interface.py','code/visual_reasoning/stage6b/runtime.py',
        'code/visual_reasoning/stage6b/protocol.py','code/visual_reasoning/stage6a/runtime.py',
        'code/visual_reasoning/stage4a/runtime.py','code/visual_reasoning/stage5a/passive.py',
        'code/visual_reasoning/stage3c9/streaming.py','code/visual_reasoning/stage3c10/runtime.py']
    signature = {'run_id':args.run_id,'rank':rank,'world_size':2,
        'slurm_job_id':config['slurm_allocation'],'node':platform.node(),
        'manifest_sha256':sha(manifest),'config_sha256':sha(OUT/'config/stage6b_config.json'),
        'code_sha256':{p:sha(ROOT/p) for p in code},'event_ids':[r['id'] for r in rows],
        'mechanics':args.mechanics,'split':args.split,'audit_tag':args.audit_tag,
        'confirmation_freeze_sha256':sha(ROOT/args.confirmation_freeze) if args.split=='confirmation' else None}
    shard = OUT/'raw'/args.run_id/f'shard_{rank:02d}'
    if (shard/'signature.json').exists():
        if not args.resume or read_json(shard/'signature.json')!=signature:
            raise RuntimeError('Resume signature mismatch')
    write_json(shard/'signature.json',signature,freeze=True)
    write_json(shard/'command.json',{'argv':sys.argv,'started_at':datetime.now(timezone.utc).isoformat()})
    processor, model = load_runtime(Path(config['model_checkpoint']), device=f'cuda:{rank}')
    assert next(model.parameters()).dtype==torch.bfloat16
    assert len(model.model.language_model.layers)==36
    write_json(shard/'environment.json',{**runtime_environment(Path(config['model_checkpoint']),model,40960),
        'dtype':str(next(model.parameters()).dtype),'node':platform.node(),
        'slurm_job_id':config['slurm_allocation'],'rank':rank,'gpu_name':torch.cuda.get_device_name(rank)})
    started=time.perf_counter();count=0
    for entry in rows:
        path=shard/(entry['id']+'.json')
        if path.exists():
            if not args.resume:raise RuntimeError('Existing output without resume')
            continue
        t0=time.perf_counter();torch.cuda.reset_peak_memory_stats()
        prepared, input_meta=prepare_condition(processor,entry['row'],f'cuda:{rank}')
        original=read_json(entry['native_input_path'])
        for field in ('prompt_token_ids','visual_token_indices','image_grid_thw','decoded_image_sha256'):
            if input_meta[field]!=original[field]:raise RuntimeError('Native input differs: '+field)
        prefill,prefill_audit=prefill_condition(model,prepared,entry['row'].get('no_image',False))
        del prepared
        if args.mechanics and entry['row'].get('no_image'):
            prefill_audit['implicit_position_replay']=validate_text_replay(model,prefill,entry['event'])
        root=make_event_root(model,prefill,entry['event'])
        meta={'source_groups':entry['source_groups'],'irrelevant_controls_validated':False}
        arms={'N':score_event_arm(model,root,meta,entry['event'],validate=args.mechanics)}
        for window in (2,8):
            for source in entry[f'w{window}_sources']:
                arms[f'{source}_W{window}']=score_event_arm(model,root,meta,entry['event'],
                    roi=source,window=window,validate=args.mechanics)
        passive,logp=collect_passive(model,root,entry,input_meta)
        checks={'passive_native_exact':score_equal(arms['N'],passive),'native_input_exact':True}
        if args.mechanics:
            arms['unhooked']=score_event_arm(model,root,meta,entry['event'],hooked=False)
            checks['unhooked_exact']=score_equal(arms['N'],arms['unhooked'])
            if entry['w2_sources']:
                first=entry['w2_sources'][0]
                arms['noop_W8']=score_event_arm(model,root,meta,entry['event'],roi=first,window=8,gain=1.,validate=True)
                arms['replay_W2']=score_event_arm(model,root,meta,entry['event'],roi=first,window=2,validate=True)
                checks.update(noop_exact=score_equal(arms['N'],arms['noop_W8']),
                    suppression_replay_exact=arms[first+'_W2']==arms['replay_W2'])
            else:
                arms['replay_N']=score_event_arm(model,root,meta,entry['event'],validate=True)
                checks['native_replay_exact']=arms['N']==arms['replay_N']
        if not all(checks.values()):
            write_json(shard/(entry['id']+'_failure.json'),{'checks':checks,'arms':arms,'passive':passive})
            raise RuntimeError('Canonical mechanics/replay failed: '+entry['id'])
        np.savez_compressed(shard/(entry['id']+'_distribution.npz'),log_probabilities=logp)
        result={'id':entry['id'],'base_id':entry['base_id'],'split':entry['split'],
            'cohort':entry['cohort'],'condition':entry['condition'],'roles':entry.get('roles'),
            'arms':arms,'passive':passive,'checks':checks,'prefill_audit':prefill_audit,
            'runtime_seconds':time.perf_counter()-t0,'peak_gpu_allocated_bytes':torch.cuda.max_memory_allocated(),
            'peak_gpu_reserved_bytes':torch.cuda.max_memory_reserved(),
            'current_query_zero_based':entry['event']['current_query_zero_based'],
            'manifest_sha256':signature['manifest_sha256'],'scientific_split':entry['split']}
        write_json(path,result);count+=1
        print(f'rank={rank} {entry["id"]} arms={len(arms)} exact=True seconds={result["runtime_seconds"]:.1f}',flush=True)
        del root,prefill,arms,passive,logp;gc.collect();torch.cuda.empty_cache()
    write_json(shard/'run_summary.json',{'completed':True,'expected_events':len(rows),'new_events':count,
        'runtime_seconds':time.perf_counter()-started,'rank':rank})
    print(f'rank={rank} COMPLETE {args.run_id}',flush=True)


if __name__=='__main__':
    main()
