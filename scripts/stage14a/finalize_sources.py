"""Assemble reviewed Stage14A source artifacts; never loads evaluated-model payloads."""
import copy
import json
from collections import Counter,defaultdict
from pathlib import Path
from scripts.stage14a.common import ROOT,load,save,sha,now,digest
from scripts.stage14a.review import FLAGS,rendering
from scripts.stage14a.review_v2 import validate
from scripts.stage14a.review_v4 import canonical_map
from scripts.stage14a.sampling import confirm


def effective_accepts(primary,qc,canonical):
    selected={};dispositions=[]
    for r in sorted(primary,key=lambda x:x['rank']):
        f=canonical[r['family_id']];q=qc.get(r['item_id'],{})
        decision=r['decision'];reason=r.get('exclusion_reason')
        if q.get('eligibility')=='FAIL':decision='EXCLUDE';reason=q['exclusion_reason']
        if decision=='ACCEPT' and f in selected:disposition='ALIAS_ALREADY_ACCEPTED'
        elif decision=='ACCEPT':disposition='ACCEPT';selected[f]=r
        else:disposition='EXCLUDE'
        dispositions.append(dict(rank=r['rank'],item_id=r['item_id'],family_id=f,disposition=disposition,exclusion_reason=reason))
    return selected,dispositions


def history_rows(groups,records,dataset):
    by=defaultdict(list)
    for i,r in enumerate(records):
        for item in r[dataset+'_ids']:by[item].append(i)
    rows=[]
    for family,members in sorted(groups.items()):
        indices=sorted({i for m in members for i in by[m]});rr=[records[i] for i in indices];kinds={r['kind'] for r in rr}
        outcome=bool(kinds&{'OUTCOME_INSPECTION_ARTIFACT','TRACE_REVIEW_ARTIFACT'})
        technical=any(r.get('technical_behavior_review',False) for r in rr) or 'TECHNICAL_ARTIFACT' in kinds
        generation='GENERATION_ARTIFACT' in kinds
        group='UNTOUCHED' if not indices else 'OUTCOME_OR_TRACE_REVIEW' if outcome else 'GENERATION_OR_TECHNICAL' if generation or technical else 'SOURCE_ONLY' if kinds<={'SOURCE_CATALOG','SOURCE_OR_DESIGN_ARTIFACT'} else 'OTHER_EXPOSURE_UNCLASSIFIED'
        rows.append(dict(family_id=family,member_item_ids=members,status='HISTORICALLY_EXPOSED' if indices else 'HISTORICALLY_UNTOUCHED',historically_exposed=bool(indices),historical_stages=sorted({r['stage'] for r in rr}),exposure_kinds=sorted(kinds),artifact_indices=indices,family_expanded_item_provenance={m:by[m] for m in members},outcome_inspection_evidence=outcome,technical_exposure_evidence=technical,scientific_generation_evidence=generation,exposure_group=group))
    return rows


def assemble():
    products={};stamp=now()
    def put(name,**data):products['stage14a_'+name+'.json']=dict(at=stamp,model_outcomes_used=False,**data)
    mv=load(ROOT/'audit/mathvision_census_source_snapshot.json');verse=load(ROOT/'audit/mathverse_mapping_source_snapshot.json')
    canonical=canonical_map({r['family_id'] for r in mv['rows']},[load(p) for p in sorted((ROOT/'audit').glob('source_alias_supplement_*_v1.json'))])
    groups=defaultdict(list)
    for r in mv['rows']:groups[canonical[r['family_id']]].append(r['item_id'])
    for members in groups.values():members.sort(key=int)
    scan=load(ROOT/'audit/history_v2/historical_identity_scan.json');records=copy.deepcopy(scan['records']);repairs=[]
    for i,r in enumerate(records):
        if r['path'] in ['outputs/qwen3vl_official_eval/v1/annotations/official_instruct_direct_review.json','outputs/qwen3vl_official_eval/v1/annotations/official_thinking_review.json']:
            repairs.append(dict(artifact_index=i,path=r['path'],old_kind=r['kind'],new_kind='TRACE_REVIEW_ARTIFACT',reason='Technical completion/repetition review artifact, not source annotation; classification uses path/schema provenance, no behavior values.'))
            r.update(kind='TRACE_REVIEW_ARTIFACT',technical_behavior_review=True,stage='qwen3vl_official_eval')
    assert len(repairs)==2
    products['audit/historical_identity_scan_final.json']=dict(at=stamp,records=records,repairs=repairs,base_scan_sha256=sha(ROOT/'audit/history_v2/historical_identity_scan.json'),files_examined=scan['files_examined'],failures=scan['failures'],test_fixture_exclusions=scan['test_fixture_exclusions'],no_model_outcomes_interpreted=True)
    histories={}
    for ds,g in [('mathvision',groups),('mathverse',{r['family_id']:[r['problem_index']] for r in verse['families']})]:
        rows=history_rows(g,records,ds);histories[ds]={r['family_id']:r for r in rows}
        put(ds+'_historical_exposure',rows=rows,scan='audit/historical_identity_scan_final.json',meaning='Catalog appearances are source exposure. Outcome/trace artifacts are evidence of recorded review, not proof a particular human inspected them. Per-item provenance includes frozen conservative family expansion; it is not direct-use evidence.',limitations='Cannot detect undocumented inspections. Unknown artifact kinds are retained. Broad source catalogs mean no strictly historically untouched family remains.',outcome_values_inspected=False)
    broad=[]
    for r in mv['rows']:
        f=canonical[r['family_id']];h=histories['mathvision'][f]
        broad.append(dict(r,original_family_id=r['family_id'],family_id=f,alias_member_item_ids=groups[f],historically_exposed=h['historically_exposed'],historical_stages=h['historical_stages'],historical_exposure={k:h[k] for k in ['status','exposure_kinds','outcome_inspection_evidence','technical_exposure_evidence','scientific_generation_evidence']},historical_exposure_record='stage14a_mathvision_historical_exposure.json#'+f,file_integrity_status='PASS'))
    source_issues={p.name:load(p) for p in sorted((ROOT/'audit').glob('source_issue_mathvision*.json'))}
    put('mathvision3040_manifest',source_issue_audits=source_issues,rows=broad,problem_count=len(broad),conservative_family_count=len(groups),alias_groups=dict(groups),exclusions=[],note='3040 native records preserved; records are not3040 independent conservative visual families.')
    by={r['item_id']:r for r in broad}
    paths=sorted((ROOT/'audit/reviews/mathvision_v2').glob('*.json'));primary=[load(p) for p in paths]
    order=load(ROOT/'stage14a_mathvision_candidate_order.json')['rows']
    assert [r['item_id'] for r in primary]==[r['item_id'] for r in order[:len(primary)]]
    qcpaths={p.stem:p for p in (ROOT/'audit/reviews/mathvision_qc250').glob('*.json')};qc={k:load(p) for k,p in qcpaths.items()}
    selected,dispositions=effective_accepts(primary,qc,canonical)
    assert len(selected)==1000
    finalqc=load(ROOT/'audit/mathvision_final_prospective_qc250.json')['rows']
    expected=sorted(selected,key=lambda f:digest('stage14a-v1|mv-qc|'+f))[:250]
    assert [r['family_id'] for r in finalqc]==expected
    for r in finalqc:
        q=qc[r['item_id']];assert q['eligibility']=='PASS' and q['source_reread_complete'] and q['resolved_for_final_seal']
    annotations=[];qcout=[]
    for f,r in selected.items():
        s=by[r['item_id']];a=copy.deepcopy(r);q=qc.get(r['item_id']);p=paths[r['rank']-1]
        if q:
            assert q['primary_receipt_sha256']==sha(p)
            a.update(q['annotation_overrides'])
            if 'e_star_atoms' in q['annotation_overrides'] and 'task_critical_relations' not in q['annotation_overrides']:a['task_critical_relations']=a['e_star_atoms']
        validate(s,a);assert a['equal_evidence_rendering']==rendering(s,a['e_star_atoms'])
        a.update({k:s[k] for k in ['question','question_hash','options','gold_answer','answer_type','subject','difficulty','image','image_hash']})
        a.update(family_id=f,original_family_id=r['family_id'],num_e_star_atoms=len(a['e_star_atoms']),historically_exposed=s['historically_exposed'],historical_stages=s['historical_stages'],primary_annotation_status='COMPLETE',second_review_status='PASS',final_qc_status='PASS',exclusion_reason_if_any=None,primary_receipt=str(p),primary_receipt_sha256=sha(p),complete_reread_receipt=str(qcpaths[r['item_id']]) if q else None,model_outcomes_used=False)
        annotations.append(a)
        qcout.append(dict(family_id=f,item_id=r['item_id'],primary_receipt=str(p),primary_receipt_sha256=sha(p),second_review=r['second_review'],final_250_selected=f in expected,complete_reread=q,final_qc_status='PASS',same_agent=True))
    compact=[{k:r[k] for k in ['family_id','original_family_id','item_id','rank','question_hash','image_hash','answer_type','subject','difficulty','num_e_star_atoms','historically_exposed','historical_stages','final_qc_status','primary_receipt']} for r in annotations]
    put('mathvision_e_star1000_manifest',rows=compact,screened=len(primary),selection='Unchanged frozen source-stratified order; earliest accepted representative per conservative family; QC rejection1174 replaced by rank1727item879.',source_only=True,final_qc_count=1000)
    put('mathvision_e_star_annotations',rows=annotations,atom_count_rule='plan/stage14a_atom_count_user_clarification_v2.md',same_agent_qc=True)
    put('mathvision_equal_evidence_renderings',rows=[dict(family_id=r['family_id'],item_id=r['item_id'],text=r['equal_evidence_rendering'],sha256=digest(r['equal_evidence_rendering'])) for r in annotations],original_question_verbatim=True,original_options_preserved=True)
    put('mathvision_evidence_probe_requests',rows=[dict(family_id=r['family_id'],item_id=r['item_id'],requests=r['evidence_request_per_atom']) for r in annotations])
    put('mathvision_qc_records',rows=qcout,all_reread_receipts=list(qc.values()),final_selected_family_ids=expected,screening_dispositions=dispositions,original_250_selection_preserved='audit/mathvision_prospective_qc250.json',final_250_selection='audit/mathvision_final_prospective_qc250.json',same_agent_not_independent_interrater=True)
    fields=['subject','difficulty','answer_type','num_e_star_atoms'];confirmed=confirm(compact,300,fields,'stage14a-v1|mv-confirm|')
    put('mathvision_confirm300_manifest',rows=confirmed,strata=fields,selection='Hamilton proportional quotas; within strata SHA256(stage14a-v1|mv-confirm|family_id).',future_generation_authorized=False)
    events=[]
    original_log=ROOT/'audit/pre_final_root/stage14a_e_star_eligibility_log.jsonl'
    if not original_log.exists():original_log=ROOT/'stage14a_e_star_eligibility_log.jsonl'
    for p,label in [(original_log,'original_v1'),(ROOT/'audit/eligibility_log_v2.jsonl','user_clarified_v2')]:
        for line in p.read_text().splitlines():events.append(dict(event_type=label,record=json.loads(line)))
    events += [dict(event_type='complete_source_reread',record=r) for r in qc.values()]
    events += [dict(event_type='final_disposition',record=r) for r in dispositions]
    products['stage14a_e_star_eligibility_log.jsonl']=''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in events)
    # Native MathVerse IDs and confirmation sample stay fixed; repeated tasks flagged separately.
    repeat_groups=[]
    for p in sorted((ROOT/'audit').glob('mathverse_source_repeat_observations_v*.json')):
        d=load(p)
        repeat_groups.extend(d.get('groups', [dict(problem_indices=list(map(str,pair)),reason=d.get('observation','Source repeat.')) for pair in d.get('observed_pairs',[])]))
    repeats={k:sorted(set(g['problem_indices']),key=int) for g in repeat_groups for k in g['problem_indices']}
    vp={p.stem:load(p) for p in (ROOT/'audit/reviews/mathverse').glob('*.json')};vq={p.stem:load(p) for p in (ROOT/'audit/reviews/mathverse_qc').glob('*.json')}
    assert len(vp)==788 and len(vq)==197
    assert {r['family_id'] for r in vq.values()}==set(load(ROOT/'audit/mathverse_prospective_qc197.json')['family_ids'])
    scope={r['family_id']:r for r in load(ROOT/'audit/mathverse_final_visual_scope_repair_v1.json')['rows']}
    overlays=defaultdict(list)
    for r in load(ROOT/'audit/mathverse_metadata_requirement_repair_v1.json')['rows']:overlays[r['family_id']].append((r['version'],r['field'],r['new_value']))
    for r in load(ROOT/'audit/mathverse_metadata_source_read_repair_v2.json')['changes']:overlays[r['family_id']].append((r['version'],r['field'],r['new']))
    families=[];metadata=[];vqc=[];normalizations=[]
    for f0 in verse['families']:
        f=copy.deepcopy(f0);k=f['problem_index'];r=vp[k];q=vq.get(k);checks=copy.deepcopy(r['consistency_checks']);meta=copy.deepcopy(r['source_metadata']);applied=[]
        for vn,field,value in overlays[f['family_id']]:meta[vn][field]=value
        if q:
            assert q['primary_receipt_sha256']==sha(ROOT/f'audit/reviews/mathverse/{k}.json')
            checks.update(q.get('check_overrides',{}))
            for vn,values in q.get('source_metadata_overrides',{}).items():meta[vn].update(values)
            assert q['resolved_for_final_seal'] or k=='7'
        if k=='7':
            a=load(ROOT/'audit/mathverse_family7_final_adjudication_v1.json');checks.update(a['check_overrides'])
            for vn,values in a['source_metadata_overrides'].items():meta[vn].update(values)
            applied.append('audit/mathverse_family7_final_adjudication_v1.json')
        if f['family_id'] in scope:checks.update(scope[f['family_id']]['check_overrides']);applied.append('audit/mathverse_final_visual_scope_repair_v1.json')
        # Requirement versus availability: infer only what completed semantic checks establish.
        to=meta['Text Only'];before=copy.deepcopy(to)
        if checks['text_only_sufficient']=='PASS':to.update(textual_information_level='full',requires_visual_binding=False,requires_low_level_visual_detail=False)
        elif checks['text_only_sufficient']=='FAIL':
            to['textual_information_level']='partial'
            to['requires_visual_binding']=True if checks['visual_versions_sufficient']=='PASS' else None
            to['requires_low_level_visual_detail']=None
        else:to.update(textual_information_level='uncertain',requires_visual_binding=None,requires_low_level_visual_detail=None)
        if to!=before:normalizations.append(dict(family_id=f['family_id'],version='Text Only',before=before,after=copy.deepcopy(to),basis='Completed source-only sufficiency checks; if both text and visuals defective/uncertain, requirement remains null rather than inventing a binding.'))
        for vn,m in meta.items():metadata.append(dict(family_id=f['family_id'],version=vn,**m))
        f.update(semantic_source_review='COMPLETE',consistency_checks=checks,review_note=r['review_note'],visual_versions_sufficient_scope=['Vision Dominant','Vision Only'],historical_exposure=histories['mathverse'][f['family_id']],source_repeat_problem_indices=repeats.get(k,[k]),all_source_checks_pass=all(v=='PASS' for v in checks.values()),source_validity_status='ALL_CHECKS_PASS' if all(v=='PASS' for v in checks.values()) else 'DOCUMENTED_SOURCE_FAILURE' if 'FAIL' in checks.values() else 'DOCUMENTED_SOURCE_AMBIGUITY',review_disagreements_resolved=True)
        families.append(f)
        vqc.append(dict(family_id=f['family_id'],primary_receipt=f'audit/reviews/mathverse/{k}.json',primary_receipt_sha256=sha(ROOT/f'audit/reviews/mathverse/{k}.json'),primary_checks=r['consistency_checks'],primary_review_note=r['review_note'],second_review=q,final_checks=checks,final_visual_check_scope=['Vision Dominant','Vision Only'],final_adjudication_overlays=applied,same_agent=True,review_disagreements_resolved=True,remaining_source_uncertainty=[key for key,v in checks.items() if v=='UNRESOLVED']))
    versions=[dict(v,semantic_source_review='COMPLETE',semantic_family_qc='stage14a_mathverse_qc_records.json') for v in verse['versions']]
    assert len(versions)==4728 and all(not v['missing'] and not v['corrupt'] for v in versions)
    put('mathverse788_family_manifest',rows=families,native_family_count=788,version_count=4728,complete_six_version_families=788,source_repeat_groups=repeat_groups,native_ids_retained=True,note='Source ambiguity/failure flags preserved. Native IDs do not certify cross-ID mathematical independence.')
    put('mathverse_variant_mapping',rows=versions,family_to_versions={r['family_id']:r['versions'] for r in families},all_expected_versions_present=True)
    put('mathverse_source_metadata',rows=metadata,definition={'textual_information_level':'Information in serialized prompt/question; Vision Only rasterized text is visual input.','visual_information_level':'Source modality description, not model difficulty.','requires_visual_binding':'Task requirement, distinct from image availability; null where source insufficiency prevents a defensible inference.','requires_low_level_visual_detail':'Source reading requirement; null denotes not established, never a performance claim.'})
    put('mathverse_qc_records',rows=vqc,primary_count=788,prospective_second_pass_count=197,same_agent_not_independent_interrater=True,uncertainty_policy='UNRESOLVED denotes a documented source-semantic ambiguity retained in the native cohort, not unfinished annotation or an unresolved reviewer disagreement. No native source/gold rewritten.')
    products['audit/mathverse_final_metadata_normalization_v1.json']=dict(at=stamp,rows=normalizations,model_outcomes_used=False)
    # The frozen MathVerse confirmation manifest contains historical PENDING labels;
    # retain it byte-for-byte and resolve current QC via the final family manifest.
    confv=load(ROOT/'stage14a_mathverse_confirm300_manifest.json')
    assert len(confv['rows'])==300
    expected_v=confirm(verse['families'],300,confv['strata'],'stage14a-v1|mathverse-confirm|')
    assert [r['family_id'] for r in confv['rows']]==[r['family_id'] for r in expected_v]
    stats=dict(mathvision=dict(native_problems=3040,conservative_families=len(groups),screened=len(primary),accepted=1000,exclusions=dict(Counter(r['exclusion_reason'] for r in dispositions if r['disposition']=='EXCLUDE')),duplicate_accepted_source_receipts=sum(r['disposition']=='ALIAS_ALREADY_ACCEPTED' for r in dispositions),full_reread_final_cohort=250,total_full_rereads_including_rejected=len(qc),distributions={field:dict(Counter(str(r[field]) for r in annotations)) for field in fields},evidence_types={flag:sum(r[flag] for r in annotations) for flag in FLAGS},atom_types=dict(Counter(m['atom_type'] for r in annotations for m in r['atom_metadata'])),structured_atom_sizes=[dict(family_id=r['family_id'],atom_index=i+1,**m) for r in annotations for i,m in enumerate(r['atom_metadata']) if m['atom_type']=='structured_layout'],historically_exposed_accepted=sum(r['historically_exposed'] for r in annotations),historically_untouched_accepted=sum(not r['historically_exposed'] for r in annotations)),mathverse=dict(native_families=788,variants=4728,complete6=788,semantic_primary=788,second_pass=197,missing_or_corrupt=0,source_check_counts={key:dict(Counter(f['consistency_checks'][key] for f in families)) for key in families[0]['consistency_checks']},source_validity_status=dict(Counter(f['source_validity_status'] for f in families)),source_repeat_groups=len(repeat_groups)),historical_exposure={ds:dict(Counter(r['exposure_group'] for r in h.values())) for ds,h in histories.items()},new_evaluated_model_calls=0,external_annotator_calls=0,gpu_hours=0)
    assert sum(stats['mathvision']['exclusions'].values())+1000+stats['mathvision']['duplicate_accepted_source_receipts']==len(primary)
    put('source_statistics',**stats)
    return products


def publish(products):
    # Never overwrite review/source evidence. Archive the two preliminary histories
    # and original v1 eligibility stream before replacing public projections.
    allowed={'stage14a_mathvision_historical_exposure.json','stage14a_mathverse_historical_exposure.json','stage14a_e_star_eligibility_log.jsonl'}
    for name in products:
        target=ROOT/name
        assert not target.exists() or name in allowed, f'Final artifact already exists: {target}'
    for name,data in products.items():
        target=ROOT/name
        if target.exists():
            archive=ROOT/'audit/pre_final_root'/name;archive.parent.mkdir(parents=True,exist_ok=True)
            if not archive.exists():
                with archive.open('xb') as f:f.write(target.read_bytes())
            else:assert sha(archive)==sha(target), 'Archive must exactly preserve replaced preliminary projection.'
        payload=data if isinstance(data,str) else json.dumps(data,ensure_ascii=False,indent=2)+'\n'
        assert len(payload.encode())<128*1024*1024, 'Unexpected projection expansion.'
        target.parent.mkdir(parents=True,exist_ok=True)
        temporary=target.with_name(target.name+'.building')
        with temporary.open('x') as f:f.write(payload)
        temporary.replace(target)
    print('PUBLISHED',len(products),'source projections')


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');args=p.parse_args()
    products=assemble()
    print(json.dumps(products['stage14a_source_statistics.json']|{'mathvision':{k:v for k,v in products['stage14a_source_statistics.json']['mathvision'].items() if k!='structured_atom_sizes'}},ensure_ascii=False,indent=2))
    if args.publish:publish(products)
