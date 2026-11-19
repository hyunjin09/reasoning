"""Attach conservative semantic demand states to every saved reasoning span.

Unresolved is an annotation outcome, never a cohort-membership filter. Exact
manually reviewed local claims supersede rules. No model-state data are read.
"""
import hashlib
import json
import re
from collections import Counter,defaultdict
from scripts.stage6a.inventory import OUT
from scripts.stage6a.prepare_candidates import write
from scripts.stage6a.source_annotations import secondary_sources, target_alias_patterns
from visual_reasoning.stage6a.semantic import classify_span,reviewed_visual_correctness,completed_claims
from visual_reasoning.stage6a.demand import temporal_labels


def load(path):return [json.loads(s) for s in path.read_text().splitlines()]


# Only unambiguous source aliases are broadened beyond the authored entity.
# Multiple-circle/angle cases retain exact source names and reviewed claims.
ALIASES={
 'mathverse_431':r'\b(?:west(?:ward)?|horizontal side)\b',
 'mathverse_635':r'\b(?:vertical height|height of the cone|height\s*\(?h\)?)\b',
 'mathverse_644':r'\bslant height\b','mathverse_645':r'\bslant height\b',
 'mathverse_651':r'\bradius\b','mathverse_654':r'\bradius\b','mathverse_664':r'\b(?:radius|diameter)\b',
 'mathverse_673':r'\b(?:cylinder height|height of (?:the )?cylinder)\b',
 'mathverse_692':r'\b(?:pipe length|length of (?:the )?pipe)\b',
 'mathverse_639':r'\b(?:pipe length|length of (?:the )?pipe)\b',
 'mathverse_735':r'\b(?:marked edges|seven edges)\b',
 'mathverse_724':r'\b(?:cube edge|edge (?:length|labeled)|side length of (?:the )?cube)\b',
 'mathverse_728':r'\b(?:cube edge|edge length|side length of (?:the )?cube)\b',
 'mathvision_1658':r'\b(?:pool length|length of (?:the )?pool|length of the rectangle)\b',
 'mathvision_1142':r'\b(?:CD|DC)\b','mathvision_2912':r'\bAC\b',
 'mathvision_3005':r'\bXY\b','mathverse_756':r'\bQR\b',
 'mathvision_2980':r'\bXY\b','mathvision_1529':r'\bAD\b',
 'mathvision_2530':r'\bBE\b','mathvista_897':r'\bLK\b',
 'mathvista_781':r'\bDG\b','mathvista_236':r'\bRT\b',
 'mathvision_2504':r'\bAB\b',
}


def source_patterns(row, target_overrides=None):
    if row['cohort']=='C1':
        literal=re.escape(row['target']['entity']).replace(r'\ ',r'\s+')
        return {'T':(target_overrides or {}).get(row['base_id'],ALIASES.get(row['base_id'],r'\b'+literal+r'\b')),
            **{s['source_id']:s['aliases'] for s in row.get('annotation_sources',[])}}
    if row['cohort']=='C2':
        return {source['source_id']:re.escape(source['entity']) for source in [row['target']]+row['other_sources']}
    key='T' if row['present'] else 'QUERY_ABSENT:'+row['category']
    return {key:r'\b'+re.escape(row['category'])+r's?\b'}


def main():
    target_overrides=target_alias_patterns()
    index={r['event_id']:r for r in load(OUT/'traces/controlled_native_index.jsonl')}
    grouped=defaultdict(list)
    for span in load(OUT/'traces/controlled_reasoning_spans.jsonl'):
        if span['section']=='reasoning':grouped[span['event_id']].append(span)
    reviews={r['event_id']:r for r in load(OUT/'c1_diagram_stress/intact_local_claim_review.jsonl')}
    manual_path=OUT/'traces/c1_manual_semantic_prefix.jsonl'
    manual={(r['event_id'],r['span_id']):r for r in load(manual_path)} if manual_path.exists() else {}
    controlled_review_path=OUT/'traces/controlled_manual_reviews.jsonl'
    controlled_reviews={r['event_id']:r for r in load(controlled_review_path)} if controlled_review_path.exists() else {}
    automatic_path=OUT/'traces/controlled_automatic_final_reviews.jsonl'
    automatic={r['event_id']:r for r in load(automatic_path)} if automatic_path.exists() else {}
    annotations=[];transitions=[];anchors=[];local=[];final=[]
    for eid,spans in grouped.items():
        row=index[eid];review=reviews.get(eid);final_review=controlled_reviews.get(eid);patterns=source_patterns(row,target_overrides);classified=[]
        for span in spans:
            quote=None
            if review and review['membership_status']=='eligible':
                if span['char_start']<=review['char_start'] and span['char_end']>=review['char_end']:
                    quote=review['claim_quote']
            label=classify_span(span['text'],patterns,row.get('demanded_sources',[]),quote)
            source_claims=completed_claims(span,(final_review or {}).get('source_claims',[]))
            if source_claims:
                known=sorted({c['source_id'] for c in source_claims})
                label={**label,'demanded_sources':sorted(set(label['demanded_sources'])|set(known)),
                    'mentioned_sources':sorted(set(label['mentioned_sources'])|set(known)),
                    'explicit_visual_claim_sources':known,'source_claims':source_claims,
                    'unresolved':bool(set(label['mentioned_sources'])-set(known)) and label['unresolved'],
                    'semantic_role':'REVIEWED_SOURCE_CLAIM',
                    'semantic_evidence':'Reviewed source-linked assertion completes in this span; full native quote offsets are retained across expanded-token boundaries. Other fields are not certified.'}
            explicit=manual.get((eid,span['span_id']))
            if explicit:
                assert explicit['text']==span['text'] and explicit['char_start']==span['char_start']
                mentioned=sorted(set(label['mentioned_sources'])|set(explicit['demanded_sources']))
                label={**explicit,'mentioned_sources':mentioned,
                    'semantic_evidence':explicit['note'],'candidate_visual_claim_sources':[],
                    'manual_prefix_review':True}
            # C1 local-claim review resolves T, not every other fact in a
            # multi-source paragraph. Preserve that scope rather than claiming a
            # complete demand vector for an unlocalized surrounding diagram.
            label['demand_source_coverage']='Reviewed T and available secondary numeric sources; surrounding geometry not exhaustively localized' if row['cohort']=='C1' else 'reviewed T/X fields' if row['cohort']=='C2' else 'queried object identity; no fabricated absent-object ROI'
            classified.append({**span,**label,'source_alias_patterns':patterns,
                'condition_evidence_availability':'absent' if row['condition'] in ['no_image','unrelated'] else 'opaque target mask with possible context' if row['condition']=='mask' else row['condition'],
                'prior_access_interpretation':('Earlier explicit queried-category assessment; no physical absent-object source is invented.' if not row['present'] else 'Earlier queried-category assertion; no inference of actual visibility, truth or causal use from masked/silhouette claims.') if row['cohort']=='C3' else 'Earlier source-linked utterance; no causal-use inference.',
                'semantic_annotation_method':'programmatic conservative predicates plus exact manually reviewed native claims',
                'attention_or_causal_data_used':False})
        temporal=temporal_labels(classified);annotations.extend(temporal)
        for item in temporal:
            changed=item['demand_changed'];prior=item['previous_demand'];current=item['demanded_sources']
            kind='UNRESOLVED' if changed is None else 'NO_CHANGE' if not changed else 'SOURCE_TO_SOURCE' if prior and current else 'DEMAND_ONSET_OR_OFFSET'
            transitions.append(dict(event_id=eid,base_id=row['base_id'],cohort=row['cohort'],span_id=item['span_id'],
                previous_demand=prior,current_demand=current,demand_changed=changed,transition_kind=kind,
                first_reuse_refresh=item['first_reuse_refresh'],source_temporal_roles=item['source_temporal_roles']))
            anchor_types=[]
            if kind=='SOURCE_TO_SOURCE':anchor_types.append('demand_transition')
            if 'REFRESH' in item['source_temporal_roles'].values():anchor_types.append('refresh')
            if kind=='NO_CHANGE' and current:anchor_types.append('matched_no_transition_candidate')
            reviewed_claims=item.get('source_claims',[])
            wrong_sources=[c['source_id'] for c in reviewed_claims if c['local_visual_correctness'].startswith('INCORRECT')]
            if wrong_sources or (item['semantic_role']=='REVIEWED_LOCAL_VISUAL_CLAIM' and review['local_visual_correctness'].startswith('INCORRECT')):anchor_types.append('wrong_claim')
            if current and row['condition'] in ['mask','strong','unrelated','no_image']:anchor_types.append('stress_high_risk')
            if anchor_types:
                anchors.append(dict(event_id=eid,base_id=row['base_id'],cohort=row['cohort'],span_id=item['span_id'],
                    token_start=item['token_start'],token_end=item['token_end'],source_ids=current,anchor_types=anchor_types,
                    role='prospective semantic anchor; no causal or mirage classification',
                    no_transition_matching_status='candidate pool; future within-source progress/length matching required',
                    wrong_claim_readout_scope='Semantic claim error may concern a geometric role while its numeric source readout is correct; error-token identity must be checked separately.' if 'wrong_claim' in anchor_types else None,
                    wrong_claim_sources=wrong_sources,source_claims=reviewed_claims,
                    refresh_sources=[key for key,role in item['source_temporal_roles'].items() if role=='REFRESH'],
                    raw_generation_artifact=row['generation_artifact'],tokens_artifact=row['tokens_artifact']))
            local.append(dict(event_id=eid,base_id=row['base_id'],span_id=item['span_id'],cohort=row['cohort'],
                local_visual_correctness=reviewed_visual_correctness(reviewed_claims) if reviewed_claims else review['local_visual_correctness'] if item['semantic_role']=='REVIEWED_LOCAL_VISUAL_CLAIM' else 'UNRESOLVED',
                source_claims=reviewed_claims,
                local_reasoning_correctness='NOT_APPLICABLE_TO_REVIEWED_VISUAL_ASSERTION' if reviewed_claims or item['semantic_role']=='REVIEWED_LOCAL_VISUAL_CLAIM' else 'UNRESOLVED',
                object_hallucination_presence=final_review.get('object_hallucination_presence','NOT_APPLICABLE_TO_FIELD_REVIEW') if reviewed_claims and final_review else 'NOT_ASSIGNED_BY_DEMAND_PARSER',
                correctness_scope='Specific reviewed source-linked claim only; not every assertion in the paragraph'))
        final.append(dict(event_id=eid,base_id=row['base_id'],cohort=row['cohort'],condition=row['condition'],
            final_answer_correctness=final_review['final_answer_correctness'] if final_review else review['final_answer_correctness'] if review else 'UNRESOLVED',
            final_readout=final_review['final_readout'] if final_review else review['final_readout'] if review else None,
            source_answer=row.get('source_answer',row['answer']),condition_answer=row['answer'],
            source_answer_consistency=final_review['source_answer_consistency'] if final_review else ('CONSISTENT' if review['final_answer_correctness']=='CORRECT' else 'INCONSISTENT' if review['final_answer_correctness']=='INCORRECT' else 'UNRESOLVED') if review else 'UNRESOLVED',
            object_hallucination_presence=final_review.get('object_hallucination_presence','NOT_APPLICABLE_TO_FIELD_REVIEW') if final_review else 'NOT_ASSIGNED_BY_DEMAND_PARSER',
            condition_answer_applicability=final_review['condition_answer_applicability'] if final_review else 'source-consistency only; no direct source image' if row['condition'] in ['no_image','unrelated'] else 'source-derived truth; manipulation availability recorded separately',
            review_note=final_review['final_review_note'] if final_review else review.get('final_review_note',review.get('eligibility_reason')) if review else 'Requires separate final-answer parsing/review'))
        if not final_review and not review and eid in automatic:
            final[-1].update(automatic[eid])
    for name,rows in [('controlled_demand_annotations',annotations),('controlled_transition_annotations',transitions),
                      ('controlled_future_causal_anchors',anchors),('controlled_local_correctness',local),('controlled_final_correctness',final)]:
        write(OUT/f'traces/{name}.jsonl',rows)
    source_sidecars=secondary_sources();extra_regions=sum(len(v) for v in source_sidecars.values())
    prefix_bases=len({r['base_id'] for r in manual.values()})
    rules=dict(method='High-precision predicate/source-alias rules; unknown demand remains UNRESOLVED',
        c1_aliases=ALIASES,source_alias_truth_values_used=False,
        reviewed_target_alias_overrides=target_overrides,
        local_claim_overrides='Explicit native claim review, correct and wrong claims retained',
        manual_prefix_scope=f'Full first20native reasoning spans of{prefix_bases}reviewed frozen C1bases; fixed dataset/construction-order scopes. Numeric-source demand only, not exhaustive geometry or all causal ancestors.',
        source_use_scope='Direct source-fact requests/readouts, explicit substitution, or source-bound geometric quantities; generic formulas and intermediate-only arithmetic are separately marked as no explicit mapped numeric demand.',
        prior_history='Complete sequence scanned; only reviewed source-linked native claims establish explicit access. Any unresolved prefix prevents a negative prior-access assertion.',
        limitations=[f'C1 localizes T and{extra_regions}secondary numeric sources across{len(source_sidecars)}source-reviewed frozen bases; remaining geometry/source dynamics are not exhaustively annotated.',
            'No claim that programmatic aliases provide exhaustive semantic recall.',
            'Final and local reasoning truth require separate review; missing review is not correctness.',
            'Semantic anchors are candidates for later scoring; no causal phenotype inferred.'])
    (OUT/'config/semantic_annotation_rules.json').write_text(json.dumps(rules,indent=2)+'\n')
    summary=dict(status='ANNOTATION_SNAPSHOT_REQUIRES_COVERAGE_REVIEW',events=len(final),reasoning_spans=len(annotations),
        semantic_roles=dict(Counter(r['semantic_role'] for r in annotations)),
        temporal_roles=dict(Counter(r['first_reuse_refresh'] for r in annotations)),
        transitions=dict(Counter(r['transition_kind'] for r in transitions)),anchors=len(anchors),
        resolved_final_answers=sum(r['final_answer_correctness'] in ['CORRECT','INCORRECT'] for r in final),
        manually_reviewed_final_answers=sum(r['event_id'] in reviews or r['event_id'] in controlled_reviews for r in final),
        c1_other_sources_not_exhaustively_localized=True,
        manual_prefix_spans=len(manual),manual_prefix_bases=len({r['base_id'] for r in manual.values()}),
        semantic_code_sha256=hashlib.sha256((OUT.parents[1]/'code/visual_reasoning/stage6a/semantic.py').read_bytes()).hexdigest())
    (OUT/'audit/controlled_annotation_snapshot.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
