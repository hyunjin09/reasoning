"""Small natural validation: matched passive descriptors and explicit causal gaps."""
import argparse
from collections import defaultdict
import numpy as np
from scripts.stage6b.common import OUT,SOURCE,read_json,read_jsonl,write_json,write_jsonl,sha
from scripts.stage6b.dense_results import load_dense,passive_vector
from visual_reasoning.stage6b.statistics import paired_effect

FEATURES={'visual_attention_mass':'global_visual_attention','sink_attention_mass':'sink_mass','predictive_entropy':'entropy'}


def freeze():
    assert not (OUT/'raw/c4_native_01').exists()
    rows={r['id']:r for r in read_jsonl(OUT/'c1_mirage/fixed_prefix_scores.jsonl') if r['split']=='discovery'}
    labels=read_json(OUT/'c1_mirage/mirage_discovery.json')['classification_rows']
    deltas=defaultdict(lambda:defaultdict(list))
    for label in labels:
        if not label['strict_mirage']:continue
        stress=rows[label['id']];intact=rows[label['base_id']+'__intact']
        for native,c1 in FEATURES.items():deltas[label['base_id']][native].append(stress[c1]-intact[c1])
    signature={k:float(np.mean([np.mean(v[k]) for v in deltas.values()])) if deltas else None for k in FEATURES}
    write_json(OUT/'config/c4_controlled_signature_freeze.json',{'source':'C1discoverystrictmirage minus same-prefix intact; equal base weighting',
        'training_bases':len(deltas),'mean_passive_descriptor_differences':signature,
        'classification':'Descriptive directions only, not a learned classifier or substitute for missing causal source state.',
        'C1rule_sha256':sha(OUT/'config/mirage_discovery_rule.json'),
        'natural_primary_comparison':'Each frozen case vs its matched control, mean over reasoning-span endpoints. Pre-wrong-claim endpoints are separate and never added to only one side of that primary mean.',
        'confirmation_or_C4_values_used':False,'correctness_training':'Controlled causal labels exclude correctness.'},freeze=True)
    print('C4descriptor directions frozen using',len(deltas),'C1discoverybases.')


def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['freeze','analyze']);args=p.parse_args()
    if args.action=='freeze':freeze();return
    signature=read_json(OUT/'config/c4_controlled_signature_freeze.json');summaries={};wrong=[];vectors=[]
    for e,r in load_dense('c4_native_01',OUT/'c4_natural_validation/native_endpoint_manifest.jsonl'):
        primary=[]
        for endpoint in r['endpoints']:
            values,sources=passive_vector(endpoint['passive'])
            item={'id':endpoint['id'],'base_id':e['base_id'],'split':e['split'],'pair_id':e['case_control']['pair_id'],
                'role':e['case_control']['atlas_role'],'review_scope':endpoint['review_scope'],
                'token_end':endpoint['token_end'],'demanded_sources':endpoint['demanded_sources'],
                'source_specific_features':sources,**values}
            vectors.append(item)
            if endpoint['semantic_role']=='REVIEWED_WRONG_OBJECT_CLAIM':
                wrong.append({**item,'claim':endpoint['source_claims'][0],
                    'wrong_next_token_logP':endpoint['passive']['native_next_token_logP'],
                    'strict_causal_failure_signature':'UNIDENTIFIED: nonexistent queried category has no target ROI; no truth-oriented exact source contrast was predeclared.',
                    'error_promoting_source_claim':False})
            elif endpoint['section']=='reasoning':primary.append(item)
        means={k:float(np.mean([s[k] for s in primary])) if primary else None for k in FEATURES}
        summaries[e['base_id']]={'base_id':e['base_id'],'split':e['split'],'pair_id':e['case_control']['pair_id'],
            'role':e['case_control']['atlas_role'],'matched_base_id':e['case_control']['matched_base_id'],
            'reasoning_endpoints':len(primary),'passive_means':means,'source_image':e['row']['image_path'],
            'strict_mirage_signature':'UNIDENTIFIED_NO_COUNTERFACTUAL_OR_SOURCE_GROUNDING_CONTRAST',
            'causal_dynamics_signature':'UNIDENTIFIED_NO_EXACT_CAUSAL_SOURCE_STATES',
            'no_image_like_signature':'UNAVAILABLE_NO_PAIRED_C4NO_IMAGE_CONDITION',
            'scope':'COCO80 object-presence cases, not exhaustive caption truth; small exploratory sample.'}
    pairs=[]
    for case in summaries.values():
        if case['role']!='hallucination_case':continue
        control=summaries[case['matched_base_id']]
        assert case['pair_id']==control['pair_id'] and case['split']==control['split']
        delta={k:case['passive_means'][k]-control['passive_means'][k] if case['passive_means'][k] is not None and control['passive_means'][k] is not None else None for k in FEATURES}
        pairs.append({'pair_id':case['pair_id'],'split':case['split'],'case':case['base_id'],'control':control['base_id'],
            'case_minus_control':delta,
            'controlled_descriptor_direction_match':{k:(delta[k]*signature['mean_passive_descriptor_differences'][k]>0) if delta[k] is not None and signature['mean_passive_descriptor_differences'][k] is not None else None for k in FEATURES},
            'causal_signature_replication_established':False})
    effects={}
    for split in ['discovery','confirmation','pooled_exploratory']:
        selected=pairs if split=='pooled_exploratory' else [r for r in pairs if r['split']==split]
        effects[split]={}
        for k in FEATURES:
            values=[r['case_minus_control'][k] for r in selected if r['case_minus_control'][k] is not None]
            if not values:continue
            result=paired_effect(values)
            effects[split][k]={key:result[key] for key in ['bases','mean','median','positive_fraction','bootstrap_mean_ci95','bootstrap_resamples']}
            effects[split][k]['unit']='Frozen matched case-control pair; small exploratory sample, no confirmatory p-value headline.'
    write_jsonl(OUT/'c4_natural_validation/controlled_signature_projection.jsonl',list(summaries.values()))
    write_jsonl(OUT/'c4_natural_validation/passive_state_vectors.jsonl',vectors)
    write_jsonl(OUT/'c4_natural_validation/wrong_claim_passive_readouts.jsonl',wrong)
    write_json(OUT/'c4_natural_validation/exploratory_effects.json',{'matched_pairs':pairs,'effect_sizes':effects,
        'cases':10,'controls':10,'predeclared_wrong_anchors':len(wrong),
        'controlled_signature_freeze_sha256':sha(OUT/'config/c4_controlled_signature_freeze.json'),
        'causal_replication_established':False,'prevalence_claim_extended':False,
        'reason':'Global passive tendencies can be compared, but missing truth-oriented causal contrasts and nonexistent hallucinated-category ROIs preclude strict controlled-state replication.'})
    lines=['# Frozen C4 natural cases and matched controls','',
        'Exploratory only:10cases/10controls. These global passive descriptors do not supply missing causal source states. No new natural traces were generated.','']
    for pair in sorted(pairs,key=lambda p:p['pair_id']):
        case=summaries[pair['case']];control=summaries[pair['control']]
        claims=[r['claim'] for r in wrong if r['base_id']==pair['case']]
        categories=sorted({r['category'] for r in claims})
        reason=claims[0]['manual_review']['reason'] if claims else 'See frozen Stage6Aadjudication.'
        lines += [f"## {pair['pair_id']} ({pair['split']})",'',
            f"Case [{pair['case']}]({case['source_image']}); control [{pair['control']}]({control['source_image']}).",
            'Unsupported categories: '+', '.join(categories)+'.',reason,'',
            'Case-minus-control mean reasoning-endpoint descriptors: '+str(pair['case_minus_control'])+'.',
            'Strict mirage, source fixation and wandering remain causally unidentified for this pair.','']
    (OUT/'c4_natural_validation/individual_cases.md').write_text('\n'.join(lines)+'\n')
    print('C4exploratory report:10pairs,',len(wrong),'predeclared wrong anchors; no strict causal replication claim.')


if __name__=='__main__':main()
