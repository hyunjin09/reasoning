"""Freeze native-condition passive endpoints, preserving semantic review scope."""
from collections import defaultdict,Counter
from scripts.stage6b.common import ROOT,OUT,SOURCE,read_json,read_jsonl,write_json,write_jsonl,sha,verify_stage6a


def main():
    verify_stage6a()
    release={r['event_id']:r for r in read_jsonl(SOURCE/'cohort/primary_release_events.jsonl') if r['cohort']=='C1'}
    native={r['event_id']:r for r in read_jsonl(SOURCE/'traces/controlled_native_index.jsonl') if r['event_id'] in release}
    maps=defaultdict(dict)
    for r in read_jsonl(SOURCE/'regions/controlled_roi_maps.jsonl'):
        if r['event_id'] in release:maps[r['event_id']][r['source_id']]=r['absolute_token_indices']
    spans=defaultdict(list);exclusions=[];coverage=Counter()
    for r in read_jsonl(SOURCE/'traces/controlled_demand_annotations.jsonl'):
        if r['event_id'] not in release:continue
        scope='manual_semantic_prefix' if r.get('manual_prefix_review') else 'reviewed_source_claim' if r.get('source_claims') else 'conservative_programmatic_demand'
        # Dense descriptive coverage includes all resolved annotations, while
        # mechanistic comparisons keep manual/reviewed and programmatic strata separate.
        if r['unresolved'] and not r.get('manual_prefix_review'):
            coverage['unresolved_unreviewed_not_labeled']+=1;continue
        if r['token_end']<8:
            exclusions.append({'event_id':r['event_id'],'span_id':r['span_id'],'reason':'Fewer than8nativequeries'});continue
        spans[r['event_id']].append({'id':r['event_id']+'__'+r['span_id'],'span_id':r['span_id'],
            'token_start':r['token_start'],'token_end':r['token_end'],'demanded_sources':r['demanded_sources'],
            'semantic_role':r['semantic_role'],'review_scope':scope,'section':r['section'],
            'semantic_unresolved':r['unresolved'],
            'normalized_progress':r['normalized_token_progress'],'source_claims':r.get('source_claims',[]),
            'previous_demand':r.get('previous_demand'),'demand_changed':r.get('demand_changed'),
            'first_reuse_refresh':r.get('first_reuse_refresh')})
        coverage[scope]+=1
    finals={r['event_id']:r for r in read_jsonl(SOURCE/'traces/controlled_final_correctness.jsonl')}
    entries=[]
    for eid,row in release.items():
        groups={} if row.get('no_image') or row['condition']=='unrelated' else maps[eid]
        n=native[eid]
        entries.append({'id':eid,'event_id':eid,'base_id':row['base_id'],'split':row['split'],'cohort':'C1',
            'condition':row['condition'],'dataset':row['dataset'],'group_id':row['group_id'],'row':row,
            'source_groups':groups,'native_input_path':n['input_metadata_artifact'],'native_generation_path':n['generation_artifact'],
            'spans':sorted(spans[eid],key=lambda s:s['token_end']),'final_correctness':finals[eid],
            'analysis_mode':'B2 own native-condition endpoints, never pooled with B1fixed prefixes'})
    write_jsonl(OUT/'trajectory/native_endpoint_manifest_v2.jsonl',entries,freeze=True)
    write_json(OUT/'config/native_passive_rules_v2.json',{'events':len(entries),'endpoints':sum(len(r['spans']) for r in entries),
        'coverage_by_review_scope':dict(coverage),'early_endpoint_exclusions':exclusions,
        'mechanics_sampling':'First2discoverybases, allconditions; first3andlast2eligibleendpoints pernativeevent.',
        'partition':'Reuse only completed canonical2048token chunks; eachendpoint partialchunk then8singlequeries unchanged; compare freshcanonicalroot inmechanics.',
        'pca':'Discovery fit after causal labels freeze; confirmation projection only; manual-reviewed main visualization, programmatic annotations separate descriptive coverage.',
        'unscored_unknowns':'Never impute demand or causal identity for unresolved spans. No arbitrary invented candidate margin.',
        'revision_reason':'Include all manually reviewed endpoints even when demand remains unresolved; preserve explicit unknowns. V1was never scored.',
        'manifest_sha256':sha(OUT/'trajectory/native_endpoint_manifest_v2.jsonl')},freeze=True)
    print({'events':len(entries),'endpoints':sum(len(r['spans']) for r in entries),'coverage':dict(coverage)})


if __name__=='__main__':main()
