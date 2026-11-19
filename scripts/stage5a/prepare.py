"""Create the Stage5A ontology, independent screen and native provenance once."""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
from scripts.stage4a.prepare_config import ROOT,read_json,read_jsonl,write_json,write_jsonl,sha,text_question
from visual_reasoning.stage0.data import load_mathverse_rows,resolve_image_path
from visual_reasoning.stage3c8.fresh import infer_missing_numeric_facts

OUT=ROOT/'outputs/stage5a'


def main():
    if OUT.exists():raise FileExistsError('Stage5A prospective preparation is create-once')
    old=read_json(ROOT/'outputs/stage4a/config/stage4a_config.json')
    prior_rules=read_json(ROOT/'outputs/stage4a/config/cohort_rules.json')
    prior_freeze=read_json(ROOT/'outputs/stage4a/cohort/cohort_freeze_complete.json')
    excluded=set(prior_rules['prior_excluded_bases'])|set(prior_freeze['validation_bases'])|set(prior_freeze['primary_bases'])
    dataset=load_mathverse_rows(Path(old['dataset_root']));by={}
    for r in dataset:by.setdefault(str(r['problem_index']),{})[r['problem_version']]=r
    reusable={}
    for stage in ('stage3c9','stage4a'):
        for path in sorted((ROOT/f'outputs/{stage}/prospective_generation/raw').glob('shard_*/examples/*/result.json')):
            row=read_json(path);key=str(row['example_id'])
            if key in reusable:continue
            shard=path.parents[2];env=read_json(shard/'environment.json')
            signature=read_json(shard/'config.json')['run_signature']
            if 'A6000' not in env['gpu_name'] or env['model_checkpoint_requested']!=old['model_checkpoint']:continue
            if not all(signature['protocol'][k]==old['locked_generation_protocol'][k] for k in ('do_sample','temperature','top_p','top_k','presence_penalty','max_new_tokens','seed')):continue
            reusable[key]=(path,row,env,signature)
    screen=[];reused=[];prior_images={}
    for b in excluded:
        image=resolve_image_path(Path(old['dataset_root']),by[b]['Vision Dominant']['image'])
        prior_images.setdefault(sha(image),[]).append(b)
    for variant in ('Vision Dominant','Vision Intensive','Vision Only','Text Lite'):
        for base in sorted(set(by)-excluded,key=int):
            row=by[base][variant];image=resolve_image_path(Path(old['dataset_root']),row['image'])
            digest=sha(image);order=len(screen);key=str(row['sample_index'])
            item={'base_problem_id':base,'example_id':key,'variant':variant,'screen_order':order,
                'screen_phase':'initial' if order<800 else 'extension','source_image':str(image),
                'source_image_sha256':digest,'question':text_question(row),
                'text_dominant_question':text_question(by[base]['Text Dominant']),
                'candidate_facts':infer_missing_numeric_facts(text_question(by[base]['Text Dominant']),text_question(row)),
                'dataset_metadata':row['metadata'],'prior_exact_image_matches':prior_images.get(digest,[]),
                'native_reuse':None,'selection_used_attention':False,'selection_used_causal_effect':False,
                'selection_used_correctness':False}
            if key in reusable:
                path,result,env,signature=reusable[key];artifact=path.parent;shard=path.parents[2]
                input_record=read_json(artifact/'input.json')
                assert input_record['generation_query']==str(row.get('query_cot') or row.get('question') or '')
                manifest={str(r['example_id']):r for r in read_jsonl(shard/'manifest.jsonl')}
                assert manifest[key]['source_image_sha256']==digest
                provenance={str(p.relative_to(ROOT)):sha(p) for p in (path,artifact/'generation.json',artifact/'tokens.jsonl',artifact/'input.json',shard/'environment.json',shard/'config.json')}
                item['native_reuse']={'artifact_dir':str(artifact.relative_to(ROOT)),'sha256':provenance,
                    'exact_protocol_image_prompt_hardware':True,'instrumentation':False}
                reused.append({**result,'screen_order':order,'screen_phase':item['screen_phase'],
                    'artifact_dir':str(artifact.relative_to(ROOT)),'stage5a_generation_kind':'matched_native_reuse'})
            screen.append(item)
            if len(screen)==1400:break
        if len(screen)==1400:break
    config={'frozen_at':datetime.now(timezone.utc).isoformat(),'source_plan':'plan/stage5a_failure_attention_state_taxonomy_plan.md',
        'source_plan_sha256':sha(ROOT/'plan/stage5a_failure_attention_state_taxonomy_plan.md'),
        'implementation_plan_sha256':sha(ROOT/'workspace/stage5a_implementation_plan.md'),
        'model_checkpoint':old['model_checkpoint'],'dataset_root':old['dataset_root'],
        'locked_generation_protocol':old['locked_generation_protocol'],'runtime':old['runtime'],
        'effect_floor':.05,'bootstrap_resamples':10000,'bootstrap_seed':12348,
        'validation':'8 historical Stage4A validation bases','passive_extraction_gate':'semantic/causal labels hash-frozen first',
        'no_sink_intervention':True,'no_representation_substitution':True,'no_failure_rescue':True}
    write_json(OUT/'config/stage5a_config.json',config)
    write_json(OUT/'config/cohort_rules.json',{'initial_budget':800,'maximum_budget':1400,
        'natural_target':200,'natural_minimum':160,'atlas_target':128,'atlas_minimum':96,
        'cf_target':64,'cf_minimum':48,'trigger_target':96,'trigger_minimum':80,
        'utility_target_events':48,'utility_minimum_events':32,'discovery_first_atlas_bases':32,
        'prior_excluded_bases':sorted(excluded,key=int),'screen_order':'VD then VI then VO then Text Lite; base-ID ascending',
        'natural_eligibility':'Complete native trajectory and >=1 semantically reviewable localized visual claim/demand, irrespective of correctness/editability',
        'atlas_selection':'First64 failure-containing and64 other eligible natural bases, fill exhausted stratum from natural order',
        'event_priorities':['first explicit visual claim/demand','first changed source/subgoal','late visual claim/reuse'],
        'attention_used':False,'causal_effect_used':False,'natural_correctness_balance':False,'reuse_matching_native_only':True,
        'prior_config_sha256':sha(ROOT/'outputs/stage4a/config/cohort_rules.json'),'prior_cohort_freeze_sha256':sha(ROOT/'outputs/stage4a/cohort/cohort_freeze_complete.json')})
    axes={'A':['MENTION_ONLY','CURRENTLY_DEMANDED','VISUAL_CLAIM','VERIFICATION_OR_RECHECK','REFRESH_OR_REENGAGEMENT','SUBGOAL_TRANSITION','OTHER'],
        'B':['CORRECT','INCORRECT','UNDECIDABLE','NO_EXPLICIT_CLAIM'],
        'C':['DEMANDED_ROI_DOMINANT','ALTERNATIVE_ROI_DOMINANT','MIXED_VISUAL_SUPPORT','LOCAL_VISUAL_INSENSITIVE','BROADER_LOCAL_SOURCE_DEPENDENCE','UNRESOLVED'],
        'D':['FIRST_USE','REUSE_WITHOUT_INTERVENING_SOURCE','REFRESH_AFTER_OTHER_SOURCE','STALE_PRIOR_SOURCE','NONE'],
        'E':['HIGH_MATCHED_VISUAL_ATTENTION','LOW_MATCHED_VISUAL_ATTENTION','TARGET_DOMINANT','MENTION_DOMINANT','MIXED_ATTENTION','SINK_RELEASE','SINK_PERSISTENT']}
    write_json(OUT/'config/annotation_ontology.json',{'axes':axes,'axes_ABD_before_causal':True,'axis_E_after_ABCD_freeze':True,
        'correctness':'Local image claim independently reviewed; final wrongness is a separate field',
        'integration':'Require an explicitly reviewed downstream reasoning error for H-INT; correct local+wrong final alone is a candidate',
        'ground_truth':'Text-Dominant annotation aid plus visual verification; generated text and numeric matching are proposals only',
        'template_family':'Manual geometry/evidence family, with dataset source/subfield fallback flagged as coarse'})
    write_json(OUT/'config/derived_taxonomy_rules.json',{'implementation':'code/visual_reasoning/stage5a/protocol.py',
        'implementation_sha256':sha(ROOT/'code/visual_reasoning/stage5a/protocol.py'),'floor':.05,
        'strong_semantic_control':'CE-abs(sham)>.05','unsupported_requires_measured_CE_null':True,
        'strict_dominance':True,'ties_unresolved':True,'profiles_and_failure_subtypes_can_overlap':True,
        'missing_or_underpowered_classes':'Report unavailable/insufficient; do not relax semantic or effect definitions'})
    write_json(OUT/'config/source_windows.json',{'W2':'[t-1,t] primary T/M/X/I','W8':'[t-7,t] T on every atlas event',
        'source_layers':list(range(36)),'heads':list(range(32)),'renormalize':False,'joint':'one union reduction secondary',
        'trigger':{'R':16,'layers':list(range(16,24)),'queries':'current only'},
        'prefix':'max2048 chunks then8 single-query barriers','matched_prior_query':'t-8, independently replayed for passive baseline'})
    write_json(OUT/'config/mirage_discovery_rule.json',{'discovery':'historical compatible A6000 anchors + first32 fresh atlas bases',
        'confirmation':'remaining fresh atlas bases','high_attention':'discovery matched percentile >=.90',
        'matching':{'roi_token_count_buckets':[1,2,4,8,16,32,1000000],'progress_quartiles':[.25,.5,.75],
                    'sequence_length_buckets':[256,512,1024,2048,4096,8192,16384,65536],'source_class':'evidence_type'},
        'minimum_reference_rois':8,'sparse_reference':'merge adjacent progress/length buckets only; preserve source class and size bucket, otherwise unresolved',
        'strict_mirage':'high attention AND weak W2/W8 AND measured weak CE; missing CE candidate only',
        'rule_freeze_before_confirmation_attention_comparison':True})
    write_json(OUT/'config/statistical_families.json',{'unit':'base_problem_id','events_nested':True,
        'families':{x:['VSD_T','CE_minus_sham','QK_T_minus_control','alphaV_T','TE_T','sink_release'] for x in ('alignment_vs_retrieval','mirage_vs_retrieval')},
        'hallucination_family':['T_minus_X','T_minus_I','CE_minus_sham','TE_T'],
        'sink_family':['state_sink_mass','state_sink_release','attention_adjusted_sink'],
        'utility_family':['correct_candidate_NLL','demanded_D','final_candidate_margin'],
        'procedure':'Within-base or matched-base nonparametric contrasts, Holm per named family,10000 base bootstrap seed12348',
        'minimum_paired_bases':12,'low_yield':'descriptive only; unrun slots p=1',
        'feature_models':'regularized logistic regression; train-fold median imputation/scaling; grouped base/template holdouts',
        'causal_feature_circularity':'F4/F5 can reconstruct causal labels; not independent validation of an internal mechanism',
        'exploratory_geometry':'PCA only; no cluster-defined taxonomy'})
    write_jsonl(OUT/'cohort/prospective_screen_manifest.jsonl',screen)
    write_jsonl(OUT/'cohort/reused_native_outcomes.jsonl',reused)
    anchors=[]
    sources=[('stage3c2','cohort/primary_dissociation_manifest.jsonl'),('stage3c10','cohort/primary_manifest.jsonl'),
             ('stage4a','cohort/primary_manifest.jsonl'),('stage3c9r','cohort/primary_manifest.jsonl')]
    for stage,name in sources:
        p=ROOT/'outputs'/stage/name
        for row in read_jsonl(p):
            anchors.append({'source_stage':stage,'base_problem_id':str(row.get('base_problem_id',row.get('problem_index'))),
                'manifest':str(p.relative_to(ROOT)),'manifest_sha256':sha(p),'used_for_natural_prevalence':False,
                'quantitative_attention_discovery_compatible':stage=='stage4a'})
    write_jsonl(OUT/'cohort/historical_anchor_manifest.jsonl',anchors)
    write_json(OUT/'cohort/screening_accounting.json',{'status':'screen_frozen_before_annotation','screen_size':len(screen),
        'initial_budget':800,'maximum_budget':1400,'excluded_prior_bases':len(excluded),'fresh_candidate_bases':len(by)-len(excluded),
        'matching_native_available':len(reused),'initial_matching_native':sum(r['screen_order']<800 for r in reused),
        'new_native':0,'natural_retained':0,'atlas_retained':0})
    write_json(OUT/'config/prospective_freeze.json',{'frozen_at':config['frozen_at'],
        'sha256':{str(p.relative_to(ROOT)):sha(p) for p in list((OUT/'config').glob('*.json'))+[OUT/'cohort/prospective_screen_manifest.jsonl',OUT/'cohort/historical_anchor_manifest.jsonl']}})
    print(read_json(OUT/'cohort/screening_accounting.json'))


if __name__=='__main__':main()
