"""Freeze a separate natural case-control atlas only after completed acquisition."""
import json
import math
from collections import Counter,defaultdict
import numpy as np
from PIL import Image
from scripts.stage6a.inventory import OUT
from scripts.stage6a.prepare_candidates import write
from visual_reasoning.stage6a.matching import match_controls


def load(path):return [json.loads(s) for s in path.read_text().splitlines()]


def main():
    stats=json.loads((OUT/'c4_natural_failure/unbiased_prevalence.json').read_text())
    assert stats['completed_generation_records']==stats['planned_images'] and not stats['pending_claim_reviews']
    if (OUT/'cohort/c4_extension_activation.json').exists():assert stats['planned_images']==1000
    target=OUT/'c4_natural_failure/case_control_manifest.jsonl';assert not target.exists(), 'Preserve frozen atlas'
    splits=json.loads((OUT/'cohort/prospective_source_split.json').read_text())['assignments']
    if (OUT/'cohort/c4_extension_preparation/split_preparation.json').exists():
        splits.update(json.loads((OUT/'cohort/c4_extension_preparation/split_preparation.json').read_text())['assignments'])
    labels={r['base_id']:r for r in load(OUT/'c4_natural_failure/hallucination_labels.jsonl')}
    inventories={r['base_id']:r for r in load(OUT/'c4_natural_failure/reference_inventory.jsonl')}
    areas=defaultdict(lambda:defaultdict(float))
    for region in load(OUT/'regions/ground_truth_rois.jsonl'):
        if region['cohort']=='C4':areas[region['base_id']][region['category']]+=region['annotated_area']
    features=[]
    for row in load(OUT/'c4_natural_failure/generations.jsonl'):
        key=row['base_id'];image=Image.open(row['image_path']).convert('L').resize((128,128))
        gray=np.asarray(image,dtype=float)/255
        complexity=float((np.abs(np.diff(gray,axis=0)).mean()+np.abs(np.diff(gray,axis=1)).mean())/2)
        parts=row['raw_decoded_response'].split('</think>',1)
        thinking_words=len(parts[0].split());caption_words=len(parts[1].split()) if len(parts)>1 else 0
        dominant=sorted(areas[key],key=lambda cat:(-areas[key][cat],cat))[:3]
        values=[math.log1p(inventories[key]['instance_count']),complexity,math.log1p(thinking_words),math.log1p(caption_words),math.log1p(row['token_count'])]
        features.append(dict(base_id=key,split=splits[key]['split'],object_hallucination_presence=labels[key]['object_hallucination_presence'],
            complete_native_trace=row['complete'],object_count=inventories[key]['instance_count'],image_complexity=complexity,
            reasoning_word_count=thinking_words,caption_word_count=caption_words,generation_token_count=row['token_count'],
            dominant_object_categories=dominant,matching_vector=values))
    eligible=[r for r in features if r['complete_native_trace'] and r['split'] in ['discovery','confirmation']]
    vectors=np.asarray([r['matching_vector'] for r in eligible]);scale=np.std(vectors,axis=0);scale[scale<1e-9]=1
    cases=[r for r in eligible if r['object_hallucination_presence']=='hallucination']
    controls=[r for r in eligible if r['object_hallucination_presence']=='no_detected_object_hallucination']
    def cost(left,right):
        numeric=float(np.abs((np.asarray(left['matching_vector'])-right['matching_vector'])/scale).mean())
        a=set(left['dominant_object_categories']);b=set(right['dominant_object_categories'])
        return numeric+(1-len(a&b)/max(1,len(a|b)))
    pairs,unmatched=match_controls(cases,controls,cost);by_id={r['base_id']:r for r in features};manifest=[]
    for number,pair in enumerate(pairs):
        for role,field in [('hallucination_case','case_base_id'),('no_detected_control','control_base_id')]:
            manifest.append(dict(pair_id=f'C4PAIR{number:04}',atlas_role=role,**by_id[pair[field]],
                matched_base_id=pair['control_base_id'] if role=='hallucination_case' else pair['case_base_id'],
                matching_cost=pair['matching_cost'],used_for_prevalence=False))
    write(target,manifest);write(OUT/'c4_natural_failure/matching_covariates.jsonl',features)
    case_values=np.asarray([by_id[p['case_base_id']]['matching_vector'] for p in pairs])
    control_values=np.asarray([by_id[p['control_base_id']]['matching_vector'] for p in pairs])
    diagnostics=dict(status='PASS_MINIMUM' if len(pairs)>=60 else 'INSUFFICIENT_NATURAL_FAILURE_YIELD',
        prospective_images=stats['planned_images'],confirmed_cases_before_completeness=sum(r['object_hallucination_presence']=='hallucination' for r in features),
        eligible_cases=len(cases),eligible_controls=len(controls),matched_pairs=len(pairs),unmatched_case_ids=unmatched,
        minimum_pairs=60,target_pairs=100,same_fold_and_unique_controls=True,
        matching_method='Within-fold minimum-total-cost bipartite assignment; mean standardized absolute log-count/length and edge-complexity distance plus dominant-category Jaccard distance.',
        vector_order=['log1p annotated object count','128x128 gray mean absolute finite-difference edge density','log1p reasoning words','log1p caption words','log1p generated tokens'],
        pooled_scales=scale.tolist(),standardized_mean_differences=((case_values.mean(axis=0)-control_values.mean(axis=0))/scale).tolist() if pairs else None,
        pair_costs=[p['matching_cost'] for p in pairs],split_pair_counts=dict(Counter(p['split'] for p in pairs)),
        object_category_exact_matches=sum(by_id[p['case_base_id']]['dominant_object_categories']==by_id[p['control_base_id']]['dominant_object_categories'] for p in pairs),
        attention_hidden_state_and_causal_features_used=False,
        limits=['Atlas is outcome-balanced and never estimates prevalence.',
            'No-detected controls satisfy the frozen object-presence protocol; they are not certified free of every attribute, relation or reasoning error.',
            'Covariate matching is approximate; imbalance is reported, and no causal effect is estimated.',
            'All confirmed eligible cases are retained even when matching is weak; no feature threshold searches for a positive mechanism.'])
    (OUT/'c4_natural_failure/matching_diagnostics.json').write_text(json.dumps(diagnostics,indent=2)+'\n')
    print(json.dumps(diagnostics,indent=2))


if __name__=='__main__':main()
