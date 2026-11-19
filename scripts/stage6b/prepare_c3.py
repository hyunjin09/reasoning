"""Freeze all C3 native-condition yes/no endpoints and real distractor sources."""
import re
from collections import defaultdict,Counter
from transformers import AutoTokenizer
from scripts.stage6b.common import ROOT,OUT,SOURCE,read_json,read_jsonl,write_json,write_jsonl,sha,verify_stage6a
from scripts.stage6b.object_regions import category_footprints
from visual_reasoning.stage6b.protocol import candidate_event


def main():
    verify_stage6a()
    tokenizer=AutoTokenizer.from_pretrained(read_json(OUT/'config/stage6b_config.json')['model_checkpoint'],local_files_only=True)
    rows=[r for r in read_jsonl(SOURCE/'cohort/primary_release_events.jsonl') if r['cohort']=='C3']
    native={r['event_id']:r for r in read_jsonl(SOURCE/'traces/controlled_native_index.jsonl') if r['cohort']=='C3'}
    targetmaps={r['event_id']:r['absolute_token_indices'] for r in read_jsonl(SOURCE/'regions/controlled_roi_maps.jsonl') if r['cohort']=='C3' and r['source_id']=='T'}
    regions=defaultdict(list)
    for r in read_jsonl(SOURCE/'regions/ground_truth_rois.jsonl'):
        if r['cohort']=='C3':regions[r['base_id']].append(r)
    inv=read_json(SOURCE/'cohort/dataset_inventory.json')
    ann=next(r['instance_annotations'] for r in inv['datasets'] if r['dataset']=='COCO2014')
    supers={r['name']:r['supercategory'] for r in read_json(ann)['categories']}
    finals={r['event_id']:r for r in read_jsonl(SOURCE/'traces/controlled_final_correctness.jsonl')}
    entries=[];audits=[];failures=[]
    for row in rows:
        eid=row['event_id'];n=native[eid];tokens=read_jsonl(n['tokens_artifact']);raw=''.join(t['decoded_token'] for t in tokens)
        split=raw.rfind('</think>')
        if split<0:
            failures.append({'event_id':eid,'reason':'No complete native thinking/final boundary'});continue
        offset=split+len('</think>');tail=raw[offset:]
        match=re.search(r'\b(?:yes|no)\b',tail,re.I)
        literal=match is not None
        if match is None:match=re.search(r'[A-Za-z]+',tail)
        if match is None:
            failures.append({'event_id':eid,'reason':'No lexical native final endpoint'});continue
        value=match.group();yes='Yes' if value[0].isupper() else 'yes';no='No' if value[0].isupper() else 'no'
        try:event=candidate_event(tokens,offset+match.start(),offset+match.end(),yes,no,tokenizer)
        except ValueError as error:
            failures.append({'event_id':eid,'reason':str(error)});continue
        event['candidate_orientation']='D_yes_no = mean_logP(yes)-mean_logP(no), including absent-source families.'
        event['reviewed_claim']={'scope':'Native final yes/no response boundary; source presence/absence from frozen image review.',
            'literal_yes_no_answer':literal,'final_correctness':finals[eid]}
        meta=read_json(n['input_metadata_artifact']);groups={};source_roles={};scores=[]
        if not row.get('no_image') and row['condition']!='unrelated':
            groups,audit=category_footprints(regions[row['base_id']],meta)
            audits.append({'event_id':eid,'category_projection':audit})
            if row['present']:
                groups['T']=targetmaps[eid];scores=['T']
                source_roles['T']='Reviewed queried-object target polygon; residual context may remain.'
            else:
                query=row['category'];categories=[k for k in groups if k.removeprefix('COCO_CATEGORY:')!=query]
                categories.sort(key=lambda k:(supers.get(k.split(':',1)[1])!=supers.get(query),
                    raw.lower().find(k.split(':',1)[1]) if k.split(':',1)[1] in raw.lower() else 10**12,k))
                for alias,key in zip(['D','X'],categories[:2]):
                    groups[alias]=groups[key];scores.append(alias)
                    source_roles[alias]={'category':key,'same_COCO_supercategory':supers.get(key.split(':',1)[1])==supers.get(query),
                        'selection':'Same COCO supercategory first, then first literal native mention, then category name; independent of correctness/attention/effects.'}
                assert 'T' not in groups
        entries.append({'id':eid,'event_id':eid,'base_id':row['base_id'],'cohort':'C3','dataset':row['dataset'],
            'split':row['split'],'group_id':row['group_id'],'condition':row['condition'],'phase':'e',
            'row':row,'event':event,'source_groups':groups,'source_roles':source_roles,
            'roles':{'demanded':'T' if row['present'] else 'QUERY_ABSENT:'+row['category'],'present':row['present']},
            'w2_sources':scores,'w8_sources':[],'native_input_path':n['input_metadata_artifact'],
            'native_generation_path':n['generation_artifact'],'final_correctness':finals[eid],
            'native_final_readout':value,'literal_yes_no_readout':literal,'analysis_mode':'Own native-condition final answer prefix',
            'readout_caveat':'Yes/no preference at own native boundary; refusal/hedging remains separate. Mask plus yes is not labeled hallucination.'})
    assert not failures,failures
    assert len(entries)==660 and len({e['base_id'] for e in entries})==136
    write_jsonl(OUT/'c3_object_stress/native_endpoint_manifest.jsonl',entries,freeze=True)
    write_json(OUT/'audit/c3_region_projection.json',{'events':audits,'absent_target_rois_fabricated':0},freeze=True)
    write_json(OUT/'config/c3_replication_rules.json',{'events':660,'families':136,'present':63,'absent':73,
        'manifest_sha256':sha(OUT/'c3_object_stress/native_endpoint_manifest.jsonl'),
        'yes_no_orientation':'Positive means yes; in absent-source intact families, positive is wrong. Source removal is error-promoting only if wrong yes logP and yes-no preference both decrease.',
        'no_image_unrelated':'Own native-condition prefixes, descriptive distribution similarity; prefix confounding remains explicit.',
        'w2':'Present target T; absent real distractors D/X; no source intervention for no-image/unrelated.',
        'labels':'Residual target source support if W2 VSD>0.05; weak grounding with preserved engagement evaluated under frozen C1 retention logic where valid; never automatic hallucination from masked yes.',
        'statistical_family':'Present sham-minus-strong, sham-minus-mask for VSD, yes-no margin, attention density, QK cosine and alphaV (10 contrasts); plus two VSD-versus-engagement standardized slope divergences (attention,alphaV). Discovery-only standardization. Holm within all12.',
        'causal_layer_head_scope':'All36layers/32heads; passive28-29allheads; no new head search.'},freeze=True)
    print('Frozen C3:660 native endpoints,63present/73absent; no absent target ROI.')


if __name__=='__main__':main()
