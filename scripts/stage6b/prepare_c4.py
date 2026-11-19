"""Frozen20case/control traces and their predeclared wrong-claim boundaries."""
from collections import defaultdict,Counter
from scripts.stage6b.common import ROOT,OUT,SOURCE,read_json,read_jsonl,write_json,write_jsonl,sha
from scripts.stage6b.object_regions import category_footprints


def main():
    cases=read_jsonl(SOURCE/'c4_natural_failure/case_control_manifest.jsonl');ids={r['base_id'] for r in cases}
    release={r['base_id']:r for r in read_jsonl(SOURCE/'cohort/primary_release_events.jsonl') if r['base_id'] in ids}
    native={r['base_id']:r for r in read_jsonl(SOURCE/'c4_natural_failure/generations.jsonl') if r['base_id'] in ids}
    regions=defaultdict(list);spans=defaultdict(list);claims={}
    for r in read_jsonl(SOURCE/'regions/ground_truth_rois.jsonl'):
        if r['base_id'] in ids:regions[r['base_id']].append(r)
    for r in read_jsonl(SOURCE/'c4_natural_failure/adjudicated_object_claims.jsonl'):
        if r['base_id'] in ids:claims[r['claim_id']]=r
    for r in read_jsonl(SOURCE/'traces/c4_demand_annotations.jsonl'):
        if r['base_id'] not in ids or r['token_end']<8:continue
        spans[r['base_id']].append({'id':r['event_id']+'__'+r['span_id'],'span_id':r['span_id'],
            'token_start':r['token_start'],'token_end':r['token_end'],'demanded_sources':r['demanded_sources'],
            'semantic_role':r['semantic_role'],'semantic_unresolved':r['unresolved'],
            'review_scope':'coarse_COCO80_description; per-instance/attribute semantics unresolved','section':r['section'],
            'normalized_progress':r['normalized_token_progress'],'source_claims':[],
            'previous_demand':r.get('previous_demand'),'demand_changed':r.get('demand_changed'),
            'first_reuse_refresh':r.get('first_reuse_refresh')})
    wrong=[]
    for r in read_jsonl(SOURCE/'traces/c4_future_causal_anchors.jsonl'):
        if r['base_id'] not in ids or 'wrong_claim' not in r['anchor_types']:continue
        c=claims[r['claim_id']];assert c['adjudicated_label']=='hallucination'
        if c['token_start']<8:continue
        aid=r['claim_id']+'__preclaim'
        s={'id':aid,'span_id':r['span_id'],'token_start':max(0,c['token_start']-8),'token_end':c['token_start'],
            'demanded_sources':r['source_ids'],'semantic_role':'REVIEWED_WRONG_OBJECT_CLAIM',
            'semantic_unresolved':False,'review_scope':'explicit_manual_hallucination_adjudication; no fabricated target ROI',
            'section':c['section'],'normalized_progress':c['token_start']/native[r['base_id']]['token_count'],
            'source_claims':[c],'previous_demand':None,'demand_changed':None,'first_reuse_refresh':None,
            'claim_id':c['claim_id'],'readout_scope':'Passive state immediately before actual wrong native noun; next-token logP descriptive only.'}
        spans[r['base_id']].append(s);wrong.append({'base_id':r['base_id'],**s})
    entries=[];audits=[]
    for case in cases:
        base=case['base_id'];row=release[base];n=native[base];directory=ROOT/n['artifact_dir']
        meta=read_json(directory/'input.json');groups,audit=category_footprints(regions[base],meta)
        entries.append({'id':row['event_id'],'event_id':row['event_id'],'base_id':base,'split':row['split'],'cohort':'C4',
            'condition':row['condition'],'dataset':row['dataset'],'group_id':row['group_id'],'row':row,
            'source_groups':groups,'native_input_path':str(directory/'input.json'),'native_generation_path':str(directory/'generation.json'),
            'spans':sorted(spans[base],key=lambda s:(s['token_end'],s['id'])),'case_control':case,
            'analysis_mode':'Exploratory frozen natural case/control validation; no native extension, no fabricated absent target'})
        audits.append({'base_id':base,'projection':audit})
    assert len(entries)==20
    write_jsonl(OUT/'c4_natural_validation/frozen_cases.jsonl',cases,freeze=True)
    write_jsonl(OUT/'c4_natural_validation/native_endpoint_manifest.jsonl',entries,freeze=True)
    write_jsonl(OUT/'c4_natural_validation/wrong_claim_anchors.jsonl',wrong,freeze=True)
    write_json(OUT/'audit/c4_source_projection.json',{'cases_controls':20,'predeclared_wrong_anchors':len(wrong),'source_maps':audits,
        'causal_identity_limit':'Hallucinated category has no true ROI; existing present-category source geometry is retained. Missing correct contrast/localization precludes a strict causal source-state signature at such anchors.',
        'no_image_comparison':'No paired Stage6A C4no-image trace; no-image-like claim is unavailable in this frozen natural validation.'},freeze=True)
    print('C4 frozen:',len(entries),'traces,',sum(len(e['spans']) for e in entries),'endpoints including',len(wrong),'predeclared wrong claims.')


if __name__=='__main__':main()
