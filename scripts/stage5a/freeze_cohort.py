"""Create-once semantic cohort, readout, source, subset and provenance freeze."""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
from scripts.stage5a.prepare import ROOT,OUT,read_json,read_jsonl,write_json,write_jsonl,sha
from visual_reasoning.stage5a.protocol import select_natural,select_atlas
from visual_reasoning.stage5a.annotation import canonical_source_class


def main():
    flag=OUT/'cohort/cohort_freeze_complete.json'
    if flag.exists():raise FileExistsError('Cohort freeze is create-once')
    config=read_json(OUT/'config/stage5a_config.json');rules=read_json(OUT/'config/cohort_rules.json')
    old=read_json(OUT/'config/prospective_freeze.json')
    for p,h in old['sha256'].items():assert sha(ROOT/p)==h,('original prospective config changed',p)
    rows=[read_json(ROOT/r['metadata_path']) for r in read_jsonl(OUT/'cohort/provisional_natural.jsonl')]
    atlas=[r for r in rows if r['atlas_selected']];ids={r['base'] for r in atlas};discovery={r['base'] for r in atlas[:32]}
    assert len(rows)==200 and len(atlas)==128 and len({r['base'] for r in rows})==200
    provisional=[r for p in sorted((OUT/'annotations').glob('provisional_manual_*.jsonl')) for r in read_jsonl(p)]
    assert [r['base'] for r in select_natural(provisional)]==[r['base'] for r in rows]
    assert [r['base'] for r in select_atlas(select_natural(provisional))]==[r['base'] for r in atlas]
    assert not {r['base'] for r in rows}&set(rules['prior_excluded_bases'])
    cf=[r for r in atlas if r['cf_reviewed']];assert len(cf)>=48
    trigger=select_atlas(atlas,target=96);assert len(trigger)==96
    trigger_ids={r['base'] for r in trigger};products={};event_rows=[];native_hashes={};asset_hashes={}
    for r in rows:
        assert r['final_asset_review_complete'] and r['native_generation_layout_exact'] and r['native_generation_query_exact']
        assert not r['attention_used'] and not r['causal_scores_available']
        assert sha(r['source_image'])==r['source_image_sha256']
        for p,h in r['native_reuse']['sha256'].items():
            if p not in native_hashes:assert sha(ROOT/p)==h,p
            native_hashes[p]=h
        r['split']='discovery' if r['base'] in discovery else 'confirmation' if r['base'] in ids else 'natural_only'
        r['trigger_selected']=r['base'] in trigger_ids
        for e in r['events']:
            p=e['candidate_start_token'];assert p>=8 and p==len(e['history_before_ed_token_ids']) and e['current_query_zero_based']==p-1
            assert e['original_divergent_suffix_ids']!=e['counterfactual_divergent_suffix_ids']
            assert e['source_groups']['T'] and set(e['source_groups']['T'])<=set(r['prompt_metadata']['visual_token_indices'])
            if 'I' in e['source_groups']:
                assert e['irrelevant_control_validated'] and len(e['source_groups']['I'])==len(e['source_groups']['T'])
            e['source_class']=canonical_source_class(r['facts'][e['source']])
            e['token_start']=p;e['token_end_exclusive']=p+len(e['actual_generated_candidate_ids'])
            e['mentioned_visual_entity']=r['facts'][e.get('mentioned_source',e['source'])]['identity']
            e['demanded_visual_entity']=[r['facts'][s]['identity'] for s in e['joint_source_ids']]
            e['claimed_visual_fact']=e['quote'];e['ground_truth_visual_fact']=[r['facts'][s] for s in e['joint_source_ids']]
            e['next_downstream_use']=r.get('integration_error_quote')
            e['next_downstream_use_scope']='reviewed later integration error, not necessarily first downstream use' if e['next_downstream_use'] else 'not independently localized'
            event_rows.append({'base_problem_id':r['base'],'example_id':r['example_id'],'split':r['split'],
                               'template_family':r['template'],'evidence_type':r['evidence_type'],'final_correct':r['final_correct'],
                               'integration_error_reviewed':r.get('integration_error_reviewed',False),**e})
        for name,p in r['paths'].items():
            assert sha(ROOT/p)==r['image_sha256'][name]
            asset_hashes[p]=r['image_sha256'][name]
        write_json(ROOT/r['metadata_path'],r);asset_hashes[r['metadata_path']]=sha(ROOT/r['metadata_path'])
    def manifest(items):
        return [{k:r[k] for k in ('base_problem_id','example_id','screen_order','variant','template','evidence_type','split','final_correct','local_incorrect','metadata_path','trigger_selected','cf_reviewed')}|
                {'asset_metadata':r['metadata_path'],'asset_metadata_sha256':sha(ROOT/r['metadata_path'])} for r in items]
    products['cohort/natural_prevalence_manifest.jsonl']=manifest(rows)
    products['cohort/causal_atlas_manifest.jsonl']=manifest(atlas)
    products['phase_c_counterfactual/subset_manifest.jsonl']=manifest(cf)
    products['phase_d_trigger/trigger_subset_manifest.jsonl']=manifest(trigger)
    products['annotations/events.jsonl']=event_rows
    for name,keys in [('semantic_roles',['semantic_role','has_explicit_visual_claim','mentioned_visual_entity','demanded_visual_entity','source_class']),
                      ('claim_correctness',['local_correctness','readout_correctness','claimed_visual_fact','ground_truth_visual_fact']),
                      ('temporal_roles',['temporal_role','temporal_unresolved','prior_explicit_availability','previous_source','previous_source_roi','temporal_evidence','next_downstream_use','next_downstream_use_scope']),
                      ('roi_t_m_x_i',['source_groups','source_identities','roi_aliases','source_overlap','irrelevant_control_validated']),
                      ('local_and_final_correctness',['local_correctness','final_correct','integration_error_reviewed'])]:
        products[f'annotations/{name}.jsonl']=[{k:e[k] for k in ['base_problem_id','event_id','split',*keys]} for e in event_rows]
    cutoff=rows[-1]['screen_order'];prefix=[r for r in provisional if r['screen_order']<=cutoff]
    products['cohort/exclusions.jsonl']=[{'base_problem_id':r['base'],'screen_order':r['screen_order'],'reason':r.get('identity_exclusion_reason',r.get('candidate_exclusion_reason',r.get('exclusion_reason','documented duplicate stimulus')))} for r in prefix if not r['eligible']]
    for path,values in products.items():write_jsonl(OUT/path,values)
    write_json(OUT/'cohort/template_families.json',dict(Counter(r['template'] for r in rows)))
    write_json(OUT/'config/prospective_amendments/source_class_normalization.json',{'before_causal_scoring':True,'reason':'Combined base-level evidence-type strings are not the kind of the individual ROI; canonicalize reviewed source kind to avoid arbitrary naming fragmentation in matching.','preserved':'Original base evidence_type and template remain unchanged.','matching_source_class':'canonical_source_class of the reviewed ROI fact','implementation':'code/visual_reasoning/stage5a/annotation.py','sha256':sha(ROOT/'code/visual_reasoning/stage5a/annotation.py'),'atlas_source_class_counts':dict(Counter(e['source_class'] for e in event_rows if e['split']!='natural_only'))})
    screen=read_jsonl(OUT/'cohort/prospective_screen_manifest.jsonl');new=list((OUT/'prospective_generation/raw').glob('shard_*/examples/*/result.json'))
    accounting={'status':'cohort_and_subsets_frozen','initial_budget':800,'maximum_budget':1400,'reviewed_prefix':cutoff+1,
                'provisional_reviewed_screen_positions':len(provisional),'natural_bases':200,'natural_events':len(event_rows),
                'atlas_bases':128,'atlas_events':sum(e['split']!='natural_only' for e in event_rows),'atlas_incorrect_bases':sum(r['local_incorrect'] for r in atlas),
                'cf_bases':len(cf),'cf_events':sum(e['cf_validated'] for r in atlas for e in r['events']),'cf_target':64,'cf_minimum':48,
                'trigger_bases':len(trigger),'discovery_bases':32,'confirmation_bases':96,'prefix_exclusions':len(products['cohort/exclusions.jsonl']),
                'reused_native_available':len(read_jsonl(OUT/'cohort/reused_native_outcomes.jsonl')),'new_completed_at_freeze':len(new),
                'new_attempted_at_freeze':len(list((OUT/'prospective_generation/raw').glob('shard_*/examples/*/input.json'))),
                'outside_prefix_outcomes':'Preserved, not included in natural prevalence; workers stop between complete trajectories.',
                'selection_used_attention':False,'selection_used_causal_effects':False,'natural_correctness_balanced':False,
                'trigger_selection':'first48 failure-containing plus first48 other atlas bases, in frozen atlas order',
                'cf_selection':'all48 image-review feasible bases after exhausting the fixed conservative construction over92 semantically eligible atlas bases; no effect selection'}
    write_json(OUT/'cohort/screening_accounting.json',accounting)
    original_valid=read_jsonl(ROOT/'outputs/stage4a/cohort/validation_manifest.jsonl')
    assert len(original_valid)==8
    write_jsonl(OUT/'cohort/validation_manifest.jsonl',original_valid)
    frozen=[OUT/p for p in products]+[OUT/'cohort/validation_manifest.jsonl',OUT/'cohort/template_families.json',OUT/'cohort/screening_accounting.json']
    frozen+=list((OUT/'config').rglob('*.json'))+[OUT/'cohort/review/temporal_review_ledger.json',OUT/'cohort/review/irrelevant_control_review.json',OUT/'counterfactual_assets/manual_review.jsonl']
    freeze={'frozen_at':datetime.now(timezone.utc).isoformat(),'natural_bases':[r['base'] for r in rows],'atlas_bases':[r['base'] for r in atlas],
            'discovery_bases':[r['base'] for r in atlas[:32]],'confirmation_bases':[r['base'] for r in atlas[32:]],
            'cf_bases':[r['base'] for r in cf],'trigger_bases':[r['base'] for r in trigger],'prefix_last_screen_order':cutoff,
            'causal_scoring_started':False,'passive_features_available':False,
            'sha256':{str(p.relative_to(ROOT)):sha(p) for p in frozen},'asset_metadata_sha256':asset_hashes,'native_provenance_sha256':native_hashes,
            'stage5a_protocol_sha256':sha(ROOT/'code/visual_reasoning/stage5a/protocol.py'),'annotation_implementation_sha256':sha(ROOT/'code/visual_reasoning/stage5a/annotation.py')}
    write_json(flag,freeze)
    print(accounting)


if __name__=='__main__':main()
