#!/usr/bin/env python3
"""Freeze fresh-base screen, provenance reuse, and complete Stage4A rules."""
import json,hashlib
from pathlib import Path
from datetime import datetime,timezone
from visual_reasoning.stage0.data import load_mathverse_rows,resolve_image_path
from visual_reasoning.stage3c8.fresh import infer_missing_numeric_facts

ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs/stage4a'
def read_json(p):return json.loads(Path(p).read_text())
def read_jsonl(p):return [json.loads(s) for s in Path(p).read_text().splitlines() if s.strip()]
def write_json(p,x):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def write_jsonl(p,x):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(''.join(json.dumps(r,allow_nan=False)+'\n' for r in x))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def text_question(r):return str(r.get('question_for_eval') or r.get('question') or '')


def main():
    if OUT.exists():raise FileExistsError('Stage4A freeze is create-once')
    old=read_json(ROOT/'outputs/stage3c9/config/stage3c9_config.json')
    paths=[ROOT/p for p in ['outputs/stage1/discovery/preparation/cohort_attempt_manifest.jsonl',
        'outputs/stage3a/cohort/primary_manifest.jsonl','outputs/stage3b7/validation/validation_manifest.jsonl',
        'outputs/stage3b8/discovery_cohort/discovery_manifest.jsonl','outputs/stage3b9/phase_b_local/cohort_manifest.jsonl',
        'outputs/stage3c8/cohort/validation_manifest.jsonl','outputs/stage3c8/cohort/historical_anchor_manifest.jsonl',
        'outputs/stage3c8/cohort/fresh_atlas_manifest.jsonl','outputs/stage3c9/cohort/primary_manifest.jsonl',
        'outputs/stage3c9/cohort/validation_manifest.jsonl','outputs/stage3c10/cohort/primary_manifest.jsonl',
        'outputs/stage3c10/cohort/validation_manifest.jsonl']]
    paths+=list((ROOT/'outputs/stage3b9/scoring/raw').glob('phase_a_*/manifest.jsonl'))
    excluded=set();sources={}
    for path in paths:
        if not path.is_file():raise FileNotFoundError(path)
        rs=read_jsonl(path);bs={str(r.get('base_problem_id',r.get('problem_index'))) for r in rs}
        assert 'None' not in bs
        excluded.update(bs);sources[str(path.relative_to(ROOT))]={'sha256':sha(path),'bases':sorted(bs,key=int)}
    split=ROOT/'outputs/stage3b9/config/cohort_split.json'
    for r in read_json(split).values():
        if isinstance(r,dict):excluded.update(r.get('base_problem_ids',[]))
    sources[str(split.relative_to(ROOT))]={'sha256':sha(split)}
    dataset=load_mathverse_rows(Path(old['dataset_root']));by={}
    for r in dataset:by.setdefault(str(r['problem_index']),{})[r['problem_version']]=r
    candidates=[]
    for priority,variant in enumerate(['Vision Dominant','Vision Intensive','Vision Only']):
        tier=[]
        for base,variants in by.items():
            if base in excluded:continue
            row=variants[variant];facts=infer_missing_numeric_facts(text_question(variants['Text Dominant']),text_question(row))
            image=resolve_image_path(Path(old['dataset_root']),row['image'])
            tier.append({'base_problem_id':base,'example_id':str(row['sample_index']),'variant':variant,
                'source_image':str(image),'source_image_sha256':sha(image),
                'candidate_facts':facts,'numeric_candidate_count':len(facts),'question':text_question(row),
                'text_dominant_question':text_question(variants['Text Dominant']),
                'selection_used_attention':False,'selection_used_causal_effect':False})
        tier.sort(key=lambda r:(-int(r['numeric_candidate_count']>=2),-r['numeric_candidate_count'],int(r['base_problem_id'])))
        candidates.extend(tier)
    assert len(candidates)>=1200
    screen=[];reused=[];reuse_by_id={}
    for p in (ROOT/'outputs/stage3c9/prospective_generation/raw').glob('shard_*/examples/*/result.json'):
        r=read_json(p);reuse_by_id[str(r['example_id'])]=(p,r)
    for order,item in enumerate(candidates[:1200]):
        item={**item,'screen_order':order,'screen_phase':'initial' if order<800 else 'extension','native_reuse':None}
        pair=reuse_by_id.get(item['example_id'])
        if pair:
            path,row=pair;shard=path.parents[2]
            env=read_json(shard/'environment.json');signature=read_json(shard/'config.json')['run_signature']
            assert env['gpu_name'].endswith('A6000') and env['model_checkpoint_requested']==old['model_checkpoint']
            assert env['language_attention_implementation']=='eager' and env['vision_attention_implementation']=='sdpa'
            assert all(signature['protocol'][k]==old['locked_generation_protocol'][k] for k in ['do_sample','temperature','top_p','top_k','presence_penalty','max_new_tokens','seed'])
            source_manifest={x['example_id']:x for x in read_jsonl(shard/'manifest.jsonl')}
            assert source_manifest[item['example_id']]['source_image_sha256']==item['source_image_sha256']
            artifact=path.parent
            provenance={str(p.relative_to(ROOT)):sha(p) for p in [path,artifact/'generation.json',artifact/'tokens.jsonl',artifact/'input.json',shard/'environment.json',shard/'config.json']}
            item['native_reuse']={'artifact_dir':str(artifact.relative_to(ROOT)),'sha256':provenance,'source_stage':'stage3c9','exact_protocol_image_hardware':True}
            reused.append({**row,'screen_order':order,'screen_phase':item['screen_phase'],'stage4a_generation_kind':'reused_matching_A6000_native','provenance':item['native_reuse']})
        screen.append(item)
    now=datetime.now(timezone.utc).isoformat()
    config={'frozen_at':now,'source_plan':'plan/stage4a_multi_evidence_switch_refresh_plan.md',
        'source_plan_sha256':sha(ROOT/'plan/stage4a_multi_evidence_switch_refresh_plan.md'),
        'implementation_plan_sha256':sha(ROOT/'workspace/stage4a_implementation_plan.md'),
        'model_checkpoint':old['model_checkpoint'],'dataset_root':old['dataset_root'],'locked_generation_protocol':old['locked_generation_protocol'],
        'runtime':{'slurm_allocation':'108548','tmux_session':'9','node':'node07','gpus':4,'gpu_class':'A6000','dtype':'bfloat16',
                   'max_generated_chunk':2048,'release_allocator_cache':True,'language_attention':'eager','vision_attention':'sdpa'},
        'screening':{'initial_budget':800,'maximum_budget':1200,'reuse_matching_native':True,'target_validation':8,'target_primary':48,'minimum_primary':36,
                    'stop_when_fully_resolved_prefix_yields_56':True,'earliest_eligible_per_base':True,'final_correctness_filter':False},
        'effect_floor':.05,'telemetry_layers':[28,29],
        'telemetry_heads':{'28':[16,0,3,6],'29':[11,6,15,12]},'sink_manipulated':False,'stage4b_started':False}
    write_json(OUT/'config/stage4a_config.json',config)
    write_json(OUT/'config/cohort_rules.json',{**config['screening'],'prior_excluded_bases':sorted(excluded,key=int),'prior_manifest_sources':sources,
        'ordering':'VD then VI then VO; >=2 static candidate facts first, descending fact count, base ID',
        'new_generation_can_stop_only_after_cohort_prefix_resolved':True,'correct_finals_not_required':True})
    write_json(OUT/'config/event_rules.json',{'order':['A1','B','A2'],'minimum_gap':12,'preferred_gap':24,
        'first_A_use_required':True,'bare_numeric_repetition_not_sufficient':True,'manual_semantic_review_required':True,
        'local_readout':'exact next discriminative numeric candidate; same OO text history and native-vs-edited fact pair',
        'zero_based_current_query':'candidate_start_token_index-1','selection_used_attention':False})
    write_json(OUT/'config/roi_rules.json',{'two_independent_facts':True,'pixel_disjoint':True,'merged_token_disjoint':True,
        'semantic_conditions':['OO','AO','OB','AB'],'shams':['A_sham','B_sham'],'manual_visual_validation':True,
        'irrelevant_control':'all bases where disjoint equal-cardinality low-ink region validated before scoring'})
    write_json(OUT/'config/source_windows.json',{'primary':'W2=[t-1,t]','sensitivity':'W8=[t-7,...,t]',
        'layers':list(range(36)),'heads':list(range(32)),'gain':0,'renormalize_attention':False})
    write_json(OUT/'config/trigger_definition.json',{'source':'up to16 generated positions strictly before current query',
        'layers':list(range(16,24)),'heads':list(range(32)),'query':'current only','gate':'robust Switch_AB OR Refresh_BA'})
    write_json(OUT/'config/primary_family.json',{'unit':'base_problem_id','tests':['S_A1','S_B','S_A2','Switch_AB','Refresh_BA','demanded_minus_irrelevant','TS_A1','TS_B','TS_A2'],
        'procedure':'two-sided paired Wilcoxon + nine-test Holm; unrun slots p=1',
        'bootstrap_resamples':10000,'bootstrap_seed':12348,'robust':'Holm p<.05, mean CI lower>0, median>0, positive_fraction>=.75'})
    write_jsonl(OUT/'cohort/prospective_screen_manifest.jsonl',screen)
    write_jsonl(OUT/'cohort/reused_native_outcomes.jsonl',reused)
    write_json(OUT/'cohort/screening_accounting.json',{'initial_budget':800,'maximum_budget':1200,'screened_native_available':len(reused),
        'initial_reusable':sum(r['screen_order']<800 for r in reused),'new_generated':0,'completed':sum(r['complete'] for r in reused),
        'correct':sum(r['correct'] for r in reused),'retained':0,'prior_excluded_base_count':len(excluded),'status':'semantic_screen_in_progress'})
    print({'excluded_bases':len(excluded),'screen_size':len(screen),'reused':len(reused),'initial_reused':sum(r['screen_order']<800 for r in reused),
           'missing_initial':sum(r['screen_order']<800 and r['native_reuse'] is None for r in screen),
           'first12':[(r['base_problem_id'],r['numeric_candidate_count'],r['native_reuse'] is not None) for r in screen[:12]]})

if __name__=='__main__':main()
