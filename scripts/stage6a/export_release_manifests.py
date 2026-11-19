"""Join the final primary release only after acquisition and annotations finish.

Raw manifests, excluded native traces and earlier construction catalogs remain
available. This export never changes membership, stimulus pixels or source folds.
"""
import hashlib
import json
from collections import Counter,defaultdict
from pathlib import Path
from scripts.stage6a.inventory import OUT,allowed
from scripts.stage6a.prepare_candidates import write


def load(path):return [json.loads(s) for s in path.read_text().splitlines()]


def preserve_write(path,rows):
    if path.exists():
        backup=path.with_name(path.stem+'_before_primary_release'+path.suffix)
        if not backup.exists():backup.write_bytes(path.read_bytes())
    write(path,rows)


def main():
    marker=OUT/'cohort/primary_release_manifest.json'
    assert not marker.exists(),'Preserve a released manifest; use an explicit version for repairs'
    c1_freeze=json.loads((OUT/'cohort/c1_membership_freeze.json').read_text())
    c1_keys={r['base_id'] for r in load(OUT/'c1_diagram_stress/base_manifest.jsonl')}
    assert len(c1_keys)==c1_freeze['retained_bases']
    prefix_scope=json.loads((OUT/'config/c1_secondary_remaining_annotation_scope.json').read_text())
    assert prefix_scope['status']=='COMPLETE','Finish the committed remaining C1 source and prefix review before release'
    from scripts.stage6a.source_annotations import source_records
    assert set(source_records())==c1_keys
    assert {r['base_id'] for r in load(OUT/'traces/c1_manual_semantic_prefix.jsonl')}==c1_keys
    assert json.loads((OUT/'audit/controlled_annotation_integrity.json').read_text())['complete_manual_prefix_bases']==len(c1_keys)
    c1=[r for r in load(OUT/'cohort/c1_primary_v2_manifest.jsonl') if r['base_id'] in c1_keys]
    source_answers={r['base_id']:r['answer'] for r in c1 if r['condition']=='intact'}
    c1=[{**r,'source_answer':source_answers[r['base_id']],
        'primary_membership_status':'eligible_after_native_completion_and_readout_review',
        'native_membership_review_artifact':'c1_diagram_stress/intact_local_claim_review.jsonl'} for r in c1]
    c2=load(OUT/'cohort/c2_primary_manifest.jsonl')
    c2_review=json.loads((OUT/'audit/c2_source_mapping_revalidation.json').read_text())
    assert c2_review['status']=='COMPLETE' and set(c2_review['reviewed_base_ids'])=={r['base_id'] for r in c2}
    c2_excluded={r['base_id'] for r in load(OUT/'cohort/c2_semantic_release_exclusions.jsonl')}
    assert c2_excluded==set(c2_review['excluded_base_ids'])
    c2=[{**r,'primary_membership_status':'source_mapping_revalidated',
        'semantic_revalidation_artifact':'audit/c2_source_mapping_revalidation.json'} for r in c2 if r['base_id'] not in c2_excluded]
    c3=load(OUT/'cohort/c3_primary_v2_manifest.jsonl')
    c4=load(OUT/'cohort/c4_primary_manifest.jsonl')+load(OUT/'cohort/c4_extension_manifest.jsonl')
    original_split=OUT/'cohort/prospective_source_split.json'
    splits=json.loads(original_split.read_text())['assignments']
    extension=json.loads((OUT/'cohort/c4_extension_preparation/split_preparation.json').read_text())
    assert hashlib.sha256(original_split.read_bytes()).hexdigest()==extension['original_split_sha256']
    assert not set(splits)&set(extension['assignments'])
    splits={**splits,**extension['assignments']}
    manifests={name:[{**r,**splits[r['base_id']]} for r in rows] for name,rows in [('C1',c1),('C2',c2),('C3',c3),('C4',c4)]}
    events=[r for rows in manifests.values() for r in rows]
    expected={r['event_id'] for r in events};assert len(expected)==len(events)
    native=load(OUT/'traces/controlled_native_index.jsonl')+load(OUT/'c4_natural_failure/generations.jsonl')
    assert expected<={r['event_id'] for r in native},'Finish every planned primary generation first'
    prevalence=json.loads((OUT/'c4_natural_failure/unbiased_prevalence.json').read_text())
    assert prevalence['completed_generation_records']==1000 and prevalence['pending_claim_reviews']==0
    assert (OUT/'c4_natural_failure/matching_diagnostics.json').exists(),'Build and review the separate atlas first'
    # Verify annotation coverage before writing the release aliases.
    merged={}
    for name,controlled,natural in [
        ('reasoning_spans','controlled_reasoning_spans','c4_native_reasoning_spans'),
        ('demand_annotations','controlled_demand_annotations','c4_demand_annotations'),
        ('local_correctness','controlled_local_correctness','c4_local_correctness'),
        ('final_correctness','controlled_final_correctness','c4_final_correctness'),
        ('transition_annotations','controlled_transition_annotations','c4_transition_annotations'),
        ('future_causal_anchor_manifest','controlled_future_causal_anchors','c4_future_causal_anchors')]:
        rows=load(OUT/f'traces/{controlled}.jsonl')+load(OUT/f'traces/{natural}.jsonl')
        merged[name]=[r for r in rows if r['event_id'] in expected]
        if name in ['reasoning_spans','demand_annotations','final_correctness']:
            assert expected=={r['event_id'] for r in merged[name]},f'Incomplete {name} snapshot'
    maps=load(OUT/'regions/controlled_roi_maps.jsonl')
    for cohort in ['C1','C2','C3']:
        folder={'C1':'c1_diagram_stress','C2':'c2_alignment_factorial','C3':'c3_object_stress'}[cohort]
        write(OUT/f'{folder}/roi_maps.jsonl',[r for r in maps if r['event_id'] in expected and r['cohort']==cohort])
    by_base=defaultdict(list)
    for row in manifests['C2']:by_base[row['base_id']].append(row)
    families=[];pairs=[]
    for key,rows in by_base.items():
        assert {r['condition'] for r in rows}=={'AR','A_only','R_only','Neither'}
        ar=next(r for r in rows if r['condition']=='AR')
        families.append(dict(base_id=key,dataset='DocVQA',cohort='C2',group_id=ar['group_id'],split=ar['split'],
            image_path=ar['image_path'],source_document=ar['metadata'],target=ar['target'],other_sources=ar['other_sources'],
            answers=ar['answers'],event_ids=[r['event_id'] for r in rows],unmatched_properties=ar['unmatched_properties']))
        pairs.append(dict(base_id=key,events=[{k:r[k] for k in ['event_id','condition','prompt','answer','demanded_sources','mentioned_sources']} for r in rows],
            pairing='Same source image and reviewed T/X fields; spatial/ordinal cues remain in retrieval-only prompts.'))
    write(OUT/'c2_alignment_factorial/base_families.jsonl',families)
    write(OUT/'c2_alignment_factorial/prompt_pairs.jsonl',pairs)
    for condition,name in [('AR','ar'),('A_only','alignment_only'),('R_only','retrieval_only'),('Neither','neither')]:
        write(OUT/f'c2_alignment_factorial/{name}_events.jsonl',[r for r in manifests['C2'] if r['condition']==condition])
    c3_bases=[r for r in manifests['C3'] if r['condition']=='intact']
    for filename,rows in [('pope_manifest',c3_bases),('present_object_manifest',[r for r in c3_bases if r['present']]),
        ('absent_object_manifest',[r for r in c3_bases if not r['present']]),
        ('occlusion_manifest',[r for r in manifests['C3'] if r['condition'] in ['mask','strong']]),
        ('sham_manifest',[r for r in manifests['C3'] if r['condition'] in ['sham','sham_strong']])]:
        preserve_write(OUT/f'c3_object_stress/{filename}.jsonl',rows)
    write(OUT/'c3_object_stress/distractor_rois.jsonl',[dict(base_id=r['base_id'],image_id=r['image_id'],
        queried_category=r['category'],other_object_rois=r['other_rois'],
        role='Source object-instance alternatives; no claim that every instance is a plausible semantic distractor') for r in c3_bases])
    image_ids={r['image_id'] for r in c3_bases}
    inventory=json.loads((OUT/'cohort/dataset_inventory.json').read_text())
    coco=next(r for r in inventory['datasets'] if r['dataset']=='COCO2014')
    source_annotations=json.loads(allowed(Path(coco['instance_annotations'])).read_text())
    by_image=defaultdict(list)
    for annotation in source_annotations['annotations']:
        if annotation['image_id'] in image_ids:by_image[annotation['image_id']].append(annotation)
    assert image_ids==set(by_image)
    preserve_write(OUT/'c3_object_stress/coco_object_annotations.jsonl',[
        dict(image_id=key,annotations=by_image[key],scope='Final retained primary C3 source images') for key in sorted(image_ids)])
    preserve_write(OUT/'c4_natural_failure/coco_native_manifest.jsonl',manifests['C4'])
    for name,rows in merged.items():write(OUT/f'traces/{name}.jsonl',rows)
    base_ids={r['base_id'] for r in events}
    release_splits={key:splits[key] for key in sorted(base_ids)}
    (OUT/'cohort/discovery_confirmation_split.json').write_text(json.dumps(dict(assignments=release_splits,
        policy='Inherited immutable prospective grouping; C4 extension links preexisting groups without reshuffling.',
        source_split_sha256=extension['original_split_sha256'],excluded_history_and_validation=True,
        original_membership_and_folds_unchanged=True),indent=2)+'\n')
    write(OUT/'cohort/primary_release_events.jsonl',events)
    report=dict(status='PRIMARY_ARTIFACT_EXPORT_COMPLETE_NOT_ACCEPTANCE',events=len(events),bases=len(base_ids),
        per_cohort_events={k:len(v) for k,v in manifests.items()},
        per_cohort_bases={k:len({r['base_id'] for r in v}) for k,v in manifests.items()},
        native_terminal_records=len(expected),native_eos_complete=sum(r['complete'] for r in native if r['event_id'] in expected),
        annotations={k:len(v) for k,v in merged.items()},
        release_events_sha256=hashlib.sha256((OUT/'cohort/primary_release_events.jsonl').read_bytes()).hexdigest(),
        source_region_catalog_scope='Ground-truth region catalog also preserves construction candidates excluded at native eligibility; join primary_release_events for retained analyses.',
        semantic_unknowns_preserved=True,no_attention_or_causal_membership_selection=True,
        final_acceptance='Separate semantic/ROI/split/selection/resource audit and summary required.')
    marker.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
