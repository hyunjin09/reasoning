#!/usr/bin/env python3
"""Freeze historical identities and all prospective Stage3C10 interpretation rules."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from transformers import AutoProcessor
from visual_reasoning.stage0.data import load_mathverse_rows
from visual_reasoning.stage3a.runtime import prepare_custom_image
from visual_reasoning.stage3b0.layout import build_token_groups
from visual_reasoning.stage3c9.streaming import fixed_chunk_ranges
from visual_reasoning.stage3c10.protocol import source_windows, PRIMARY

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'outputs/stage3c10'
def read_json(p): return json.loads(Path(p).read_text())
def read_jsonl(p): return [json.loads(x) for x in Path(p).read_text().splitlines() if x.strip()]
def write_json(p,x):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def write_jsonl(p,x):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(''.join(json.dumps(r,allow_nan=False)+'\n' for r in x))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def token_hash(ids): return hashlib.sha256(json.dumps(ids,separators=(',',':')).encode()).hexdigest()


def main():
    if OUT.exists(): raise FileExistsError('Prospective Stage3C10 freeze already exists')
    old=read_json(ROOT/'outputs/stage3c3/config/stage3c3_config.json')
    processor=AutoProcessor.from_pretrained(old['model_checkpoint'],local_files_only=True)
    data={str(x['sample_index']):x for x in load_mathverse_rows(Path(old['dataset_root']))}
    event_path=ROOT/'outputs/stage3b2/annotations/discriminative_event_annotations.jsonl'
    roi_path=ROOT/'outputs/stage3b7/roi_audit/roi_token_mapping.jsonl'
    mention_path=ROOT/'outputs/stage3c2/annotations/mention_roi_annotations.jsonl'
    events={str(x['base_problem_id']):x for x in read_jsonl(event_path)}
    rois={str(x['base_problem_id']):x for x in read_jsonl(roi_path)}
    mentions={str(x['base_problem_id']):x for x in read_jsonl(mention_path)}
    input_paths=[event_path,roi_path,mention_path,ROOT/'plan/stage3c10_retrieval_trigger_plan.md',
        ROOT/'workspace/stage3c10_implementation_plan.md',ROOT/'outputs/stage3c3/config/stage3c3_config.json',
        ROOT/'code/visual_reasoning/stage3c3/metrics.py',ROOT/'code/visual_reasoning/stage3c4/runtime.py',
        ROOT/'code/visual_reasoning/stage3c9/streaming.py']
    allrows=[]; mt=[]; sources=[]; ids={}
    for role,count in [('validation',7),('primary',24)]:
        p=ROOT/f'outputs/stage3c3/cohort/{role}_manifest.jsonl'; input_paths.append(p)
        rows=read_jsonl(p); assert len(rows)==count
        dst=OUT/f'cohort/{role}_manifest.jsonl'; dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(p.read_bytes())
        ids[role]=[str(r['base_problem_id']) for r in rows]
        for item in rows:
            base=str(item['base_problem_id']); event=events[base]; roi=rois[base]
            edit_path=ROOT/f'outputs/stage3b3_redesign/counterfactual_shams/{base}/edit_metadata.json'
            edit=read_json(edit_path); input_paths += [edit_path,ROOT/edit['paths']['O']]
            row=data[str(item['example_id'])]
            prepared,meta=prepare_custom_image(processor,row,ROOT/edit['paths']['O'],device='cpu'); del prepared
            assert meta['visual_token_indices']==roi['absolute_source_groups']['V_all']
            qids=processor.tokenizer.encode(str(row.get('query_cot') or row.get('question') or ''),add_special_tokens=False)
            groups=build_token_groups(prompt_token_ids=meta['prompt_token_ids'],visual_token_indices=meta['visual_token_indices'],question_token_ids=qids)
            assert not set(groups['Q']) & set(meta['visual_token_indices'])
            assert all(processor.tokenizer.convert_ids_to_tokens(meta['prompt_token_ids'][i])!='<|im_start|>' for i in groups['Q'])
            context=list(map(int,event['history_before_ed_token_ids'])); assert len(context)==int(event['ed_generated_index'])
            states={}
            for pair in item['state_pairs']:
                target=pair['target_id']; states[target]={}
                for name,oldname in [('M','state_M'),('T','state_R')]:
                    index=int(pair[oldname]['generated_index']); assert token_hash(context[:index])==pair[oldname]['prefix_sha256']
                    windows=source_windows(index)
                    record={'base_problem_id':base,'target_id':target,'state':name,
                        'historical_one_based_index':index,'current_zero_based_index':index-1,
                        'absolute_query_position':meta['prompt_token_count']+index-1,
                        'prefix_sha256':token_hash(context[:index]),'source_windows_generated_zero_based':windows,
                        'r16_available_count':len(windows['R16']),'r16_complete':len(windows['R16'])==16,
                        'e16_available':windows['E16'] is not None}
                    states[target][name]=record; mt.append(record)
            barriers=sorted({i for pair in states.values() for r in pair.values() for i in [r['current_zero_based_index'],r['historical_one_based_index']] if 0<i<len(context)})
            partition=fixed_chunk_ranges(start=0,end=len(context),chunk_size=2048,mandatory_boundaries=barriers)
            routing={'T':roi['absolute_source_groups']['V_target'], 'I':roi['absolute_source_groups']['V_irrelevant'],
                'M':mentions[base]['mention_absolute_source_positions'],'sink':[0]}
            assert all(not set(a)&set(b) for j,a in enumerate(routing.values()) for b in list(routing.values())[j+1:])
            record={'base_problem_id':base,'cohort_role':role,'example_id':str(item['example_id']),
                'image_path':edit['paths']['O'],'context':context,
                'original_suffix':event['original_divergent_suffix_ids'],
                'counterfactual_suffix':event['counterfactual_divergent_suffix_ids'],
                'states':states,'routing_groups':routing,'Q_positions':groups['Q'],
                'prompt_token_ids':meta['prompt_token_ids'],'prompt_length':meta['prompt_token_count'],
                'image_grid_thw':meta['image_grid_thw'],'visual_positions':meta['visual_token_indices'],
                'partition':partition,'evidence_type':item['evidence_type']}
            allrows.append(record); sources.append({'base_problem_id':base,'Q':groups['Q'],'routing_groups':routing,
                'states':states,'Q_definition':'historical exact question-text span; excludes special/control tokens'})
    assert len(set(ids['validation'])|set(ids['primary']))==31
    config={'created_at':datetime.now(timezone.utc).isoformat(),'plan':'plan/stage3c10_retrieval_trigger_plan.md',
        'model_checkpoint':old['model_checkpoint'],'dataset_root':old['dataset_root'],'seed':1234,'condition':'O',
        'architecture_expected':old['architecture_expected'],'targets':old['targets'],
        'runtime':{'slurm_allocation':'108548','tmux_session':'9','node':'node07','gpus':4,
            'dtype':'bfloat16','language_attention':'eager','vision_attention':'sdpa','max_chunk':2048,
            'partition':'shared union of before/after all M/T query boundaries per base; current steps one token',
            'release_unused_allocator_at_boundary':True},'cohort_ids':ids,
        'partition_fp32_tolerance':1e-5,'selection_used_attention':False,'sink_manipulated':False,
        'recent_window_shortfall':'intersect with generated history; retain and flag base, never spill into prompt',
        'E16_shortfall':'unavailable without 32 preceding tokens; no shifted replacement',
        'phase_f_gate':'primary results frozen; all bases/states last8 available positions',
        'phase_e_gate':'ungated same-state Q rescue for both targets',
        'hpre_gate':'R16 VSD robust AND Q routing rescue robust AND Q VSD rescue not robust',
        'prompt_dominance_ratio':1.5}
    write_json(OUT/'config/stage3c10_config.json',config)
    write_json(OUT/'config/frozen_targets.json',old['targets'])
    write_json(OUT/'config/frozen_mt_states.json',mt)
    write_json(OUT/'config/trigger_source_groups.json',sources)
    write_json(OUT/'config/routing_readout.json',{'function':'visual_reasoning.stage3c3.metrics.summarize_routing_state',
        'source_sha256':sha(ROOT/'code/visual_reasoning/stage3c3/metrics.py'),'primary':'RDS_T_vs_M',
        'definition':'causal-head mean scaled target logit minus causal-head mean scaled mention-ROI logit',
        'noncausal_heads':{t:r['noncausal_heads'] for t,r in old['targets'].items()}})
    write_json(OUT/'config/vsd_definition.json',{'D':'O-candidate minus C-candidate mean divergent-suffix log probability on O image',
        'VSD':'D(no ROI suppression)-D(current-only all36layer all32head ROI suppression)',
        'TE_VSD':'VSD_N-VSD_triggerKD','DiD':'TE(T)-TE(M)','current_query_zero_based':'historical_index-1'})
    write_json(OUT/'config/primary_family.json',{'contrasts':PRIMARY,'unit':'base_problem_id','correction':'Holm, eight tests separately per target',
        'test':'two-sided paired Wilcoxon','bootstrap_seed':12348,'bootstrap_samples':10000,
        'robust_positive':'Holm p<.05 AND bootstrap mean CI lower>0 AND median>0 AND positive fraction>=.75',
        'unrun_slots_p':1.,'gate_freeze':'B gates computed with mediation p=1; never loosen after mediation',
        'trigger_gate':PRIMARY[:5],'phase_c_gate':'robust rds_T OR robust vsd_T',
        'phase_d_gate':'complete trigger gate','temporal_windows':[1,2,4,8,16],
        'layer_bins':{'L0':list(range(8)),'L1':list(range(8,16)),'L2':list(range(16,24)),
                      'L3':list(range(24,28)),'L4A':[28]}})
    write_jsonl(OUT/'config/assets.jsonl',allrows)
    write_json(OUT/'config/immutable_inputs.json',{'sha256':{str(p.relative_to(ROOT)):sha(p) for p in input_paths}})
    print(json.dumps({'cohort':ids,'state_count':len(mt),'short_R16':[(x['base_problem_id'],x['target_id'],x['state'],x['r16_available_count']) for x in mt if not x['r16_complete']],
        'E16_missing':sum(not x['e16_available'] for x in mt)}))

if __name__=='__main__': main()
