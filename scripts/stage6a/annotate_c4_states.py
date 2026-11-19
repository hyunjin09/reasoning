"""Coarse object-description states from frozen C4 claim/context adjudication.

Category-level states do not claim to identify an instance among multiple
same-category objects. Attribute/relation truth remains separate and unresolved.
"""
import json
from collections import defaultdict,Counter
from scripts.stage6a.inventory import OUT
from scripts.stage6a.prepare_candidates import write
from visual_reasoning.stage6a.demand import temporal_labels


def load(path):return [json.loads(s) for s in path.read_text().splitlines()]


def main():
    grouped=defaultdict(list);claims=defaultdict(list)
    for row in load(OUT/'traces/c4_native_reasoning_spans.jsonl'):
        if row['section']=='reasoning':grouped[row['event_id']].append(row)
    for row in load(OUT/'c4_natural_failure/adjudicated_object_claims.jsonl'):
        claims[(row['event_id'],row['span_id'])].append(row)
    regions={r['base_id']:r['category_source_groups'] for r in load(OUT/'regions/coco_category_source_groups.jsonl') if r['cohort']=='C4'}
    labels={r['event_id']:r for r in load(OUT/'c4_natural_failure/hallucination_labels.jsonl')}
    annotations=[];transitions=[];anchors=[];local=[];final=[]
    excluded={'not_object_claim','nonasserted'}
    for eid,spans in grouped.items():
        states=[]
        for span in spans:
            items=claims[(eid,span['span_id'])]
            objects=[c for c in items if c['adjudicated_label'] not in excluded and c['assertion']=='asserted']
            unresolved=any(c['adjudicated_label'] in ['unresolved_image','pending_image_review'] for c in objects)
            categories=sorted({c['category'] for c in objects})
            sources=['COCO_CATEGORY:'+cat for cat in categories]
            states.append({**span,'demanded_sources':sources,
                'mentioned_sources':sorted({'COCO_CATEGORY:'+c['category'] for c in items if c['adjudicated_label']!='not_object_claim'}),
                'explicit_visual_claim_sources':sources if not unresolved else [],'unresolved':unresolved,
                'semantic_role':'OBJECT_CURRENTLY_DESCRIBED' if sources else 'NO_NORMALIZED_OBJECT_DEMAND',
                'object_categories_currently_described':categories,
                'attribute_relation_assertion_context':span['text'] if sources else None,
                'attribute_relation_correctness':'UNRESOLVED_NOT_EXHAUSTIVELY_ANNOTATED',
                'instance_region_members':{key:regions[span['base_id']].get(key,[]) for key in sources},
                'missing_region_interpretation':'No source instance coordinates, not proof of object absence; may be hallucinated or manually supported but unannotated.',
                'semantic_resolution':'coarse COCO80 normalized object description; per-instance identity unresolved',
                'prior_access_interpretation':'Earlier category assertion, including possible object errors; not proof that a physical source existed or was visually acquired.',
                'annotation_method':'Frozen object parser plus explicit candidate-assertion/image adjudication; no attention or causal features',
                'claim_ids':[c['claim_id'] for c in objects],
                'coverage_limit':'Reference-supported categories are not exhaustive manual reviews of every assertion; attributes, counts, relations and non-COCO objects remain separate.'})
            hall=[c for c in objects if c['adjudicated_label']=='hallucination']
            local.append(dict(event_id=eid,base_id=span['base_id'],cohort='C4',span_id=span['span_id'],
                local_visual_correctness='INCORRECT_OBJECT_PRESENCE' if hall else 'UNRESOLVED' if unresolved else 'NO_OBJECT_ERROR_DETECTED' if objects else 'NOT_APPLICABLE_TO_NORMALIZED_OBJECT_PRESENCE',
                local_reasoning_correctness='UNRESOLVED_NOT_EXHAUSTIVELY_ANNOTATED',
                object_hallucination_presence=bool(hall),
                correctness_scope='COCO80 object-presence assertions only; no full-sentence truth guarantee'))
            for claim in hall:
                anchors.append(dict(event_id=eid,base_id=span['base_id'],cohort='C4',span_id=span['span_id'],
                    claim_id=claim['claim_id'],token_start=claim['token_start'],token_end=claim['token_end'],
                    source_ids=['COCO_CATEGORY:'+claim['category']],anchor_types=['wrong_claim'],
                    status='prospective natural wrong-object anchor, no causal phenotype',
                    region_identity='Queried category may have no ground-truth ROI; no coordinates invented'))
        result=temporal_labels(states);annotations.extend(result)
        for item in result:
            changed=item['demand_changed'];previous=item['previous_demand'];current=item['demanded_sources']
            kind='UNRESOLVED' if changed is None else 'NO_CHANGE' if not changed else 'COARSE_OBJECT_SET_CHANGE' if previous and current else 'DEMAND_ONSET_OR_OFFSET'
            transitions.append(dict(event_id=eid,base_id=item['base_id'],cohort='C4',span_id=item['span_id'],
                previous_demand=previous,current_demand=current,demand_changed=changed,transition_kind=kind,
                first_reuse_refresh=item['first_reuse_refresh'],source_temporal_roles=item['source_temporal_roles'],
                granularity='category set, not individual visual object'))
            types=[]
            if kind=='COARSE_OBJECT_SET_CHANGE':types.append('coarse_demand_transition')
            if 'REFRESH' in item['source_temporal_roles'].values():types.append('coarse_refresh')
            if kind=='NO_CHANGE' and current:types.append('matched_no_transition_candidate')
            if types:
                anchors.append(dict(event_id=eid,base_id=item['base_id'],cohort='C4',span_id=item['span_id'],
                    token_start=item['token_start'],token_end=item['token_end'],source_ids=current,anchor_types=types,
                    refresh_sources=[key for key,role in item['source_temporal_roles'].items() if role=='REFRESH'],
                    granularity='COCO80 category-set annotation; not exact object-instance identity or causal retrieval',
                    no_transition_matching_status='candidate pool; future within-source progress/length matching required',
                    status='prospective semantic anchor; no causal phenotype or membership filtering'))
        label=labels[eid]
        final.append(dict(event_id=eid,base_id=label['base_id'],cohort='C4',
            final_answer_correctness='INCORRECT_OBJECT_PRESENCE' if label['final_caption_object_hallucination']=='hallucination' else 'UNRESOLVED_FULL_CAPTION_TRUTH',
            final_caption_object_hallucination=label['final_caption_object_hallucination'],
            local_reasoning_correctness='UNRESOLVED_NOT_EXHAUSTIVELY_ANNOTATED',
            explanation='Object-label absence does not certify every attribute, relation, count or nonvisual assertion in an open-ended caption.'))
    for name,rows in [('c4_demand_annotations',annotations),('c4_transition_annotations',transitions),
                      ('c4_future_causal_anchors',anchors),('c4_local_correctness',local),('c4_final_correctness',final)]:
        write(OUT/f'traces/{name}.jsonl',rows)
    summary=dict(status='COARSE_ANNOTATION_SNAPSHOT',events=len(final),reasoning_spans=len(annotations),
        semantic_roles=dict(Counter(r['semantic_role'] for r in annotations)),
        temporal_roles=dict(Counter(r['first_reuse_refresh'] for r in annotations)),
        transitions=dict(Counter(r['transition_kind'] for r in transitions)),
        wrong_object_anchors=sum('wrong_claim' in r['anchor_types'] for r in anchors),
        anchor_types=dict(Counter(kind for r in anchors for kind in r['anchor_types'])),
        natural_category_states_not_pooled_with_controlled_exact_source_states=True,
        full_attribute_relation_and_nonvisual_truth_not_claimed=True)
    (OUT/'audit/c4_annotation_snapshot.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
