"""Secondary native-condition object stress, with explicit absent-source limits."""
import argparse
from collections import defaultdict,Counter
import numpy as np
from scripts.stage6b.common import OUT,read_json,read_jsonl,write_json,write_jsonl,sha
from scripts.stage6b.event_results import load_run,feature_values,distribution_similarity
from visual_reasoning.stage6b.statistics import paired_effect,holm,robustness

MANIFEST=OUT/'c3_object_stress/native_endpoint_manifest.jsonl'
FEATURES=['vsd','margin','attention_density','qk_cosine','alpha_v_norm']


def flatten(entries,results):
    rows=[]
    for eid,e in entries.items():
        r=results[eid];n=r['arms']['N']
        source='T' if e['row']['present'] else 'D'
        effects={s:{'yes_no_vsd':n['D']-r['arms'][s+'_W2']['D'],
                    'removal_delta_yes_logP':r['arms'][s+'_W2']['L_o']-n['L_o'],
                    'removal_delta_yes_minus_no':r['arms'][s+'_W2']['D']-n['D']}
                 for s in e['w2_sources']}
        rows.append({'id':eid,'base_id':e['base_id'],'split':e['split'],'group_id':e['group_id'],
            'condition':e['condition'],'present':e['row']['present'],'queried_category':e['row']['category'],
            'native_answer':e['final_correctness']['final_readout'],'native_correctness':e['final_correctness']['final_answer_correctness'],
            'object_hallucination_presence':e['final_correctness']['object_hallucination_presence'],
            'source_review_note':e['final_correctness']['review_note'],
            'source_answer_consistency':e['final_correctness']['source_answer_consistency'],
            'margin':n['D'],'yes_logP':n['L_o'],'no_logP':n['L_c'],'entropy':r['passive']['predictive_entropy'],
            'vsd':effects['T']['yes_no_vsd'] if 'T' in effects else None,'source_effects':effects,
            'source_roles':e['source_roles'],**feature_values(r,source),
            'global_visual_mass':feature_values(r,'visual')['attention_mass'],'sink_mass':feature_values(r,'sink')['attention_mass'],
            'interpretation':'Own native-condition prefix; residual context can survive masks. Absent target has no invented ROI.'})
    return rows


def grouped(rows):
    result=defaultdict(dict)
    for r in rows:result[r['base_id']][r['condition']]=r
    return result


def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['freeze','analyze']);args=p.parse_args()
    if args.action=='freeze':
        assert not (OUT/'raw/c3_confirmation_01').exists()
        entries,results,_=load_run('c3_discovery_01',MANIFEST,'discovery');rows=flatten(entries,results)
        present=[r for r in rows if r['present'] and r['condition'] in ['intact','strong','mask','sham','sham_strong']]
        rule={'manifest_sha256':sha(MANIFEST),'base_rules_sha256':sha(OUT/'config/c3_replication_rules.json'),
            'feature_scales':{k:max(float(np.std([r[k] for r in present],ddof=1)),1e-12) for k in FEATURES},
            'effect_floor':.05,'retention':.8,'collapse_fraction':.2,'sham_grounding_retention':.5,
            'absolute_engagement':{k:float(np.quantile([r[k] for r in present if r['condition']=='intact'],.25)) for k in ['attention_density','alpha_v_norm']},
            'calibration':'C1 fixed relative-retention/collapse constants; object-specific absolute feature scales from C3discovery only. No CF gate exists for C3, so only mirage-like candidates.',
            'discovery_events':len(rows),'correctness_in_label_rule':False}
        write_json(OUT/'config/c3_confirmation_freeze.json',rule,freeze=True);print('C3discovery calibration frozen');return
    rule=read_json(OUT/'config/c3_confirmation_freeze.json');rows=[];paths={}
    for split in ['discovery','confirmation']:
        e,r,p=load_run('c3_'+split+'_01',MANIFEST,split);rows+=flatten(e,r);paths.update(p)
    bases=grouped(rows);labels=[];contrasts=defaultdict(dict);similarities=[];error_diagnostics=[]
    for base,c in bases.items():
        i=c['intact']
        if i['present']:
            divergence={k:[] for k in ['attention_density','alpha_v_norm']}
            for severity,condition in enumerate(['strong','mask'],1):
                stress=c[condition];sham=c['sham_strong' if condition=='strong' else 'sham']
                for k in FEATURES:contrasts[f'sham_minus_{condition}__{k}'][base]=sham[k]-stress[k]
                for k in divergence:
                    divergence[k].append(severity*((sham['vsd']-stress['vsd'])/rule['feature_scales']['vsd']-(sham[k]-stress[k])/rule['feature_scales'][k]))
                retained=any(stress[k]>=rule['retention']*i[k] and stress[k]>=threshold for k,threshold in rule['absolute_engagement'].items())
                collapsed=i['vsd']>.05 and abs(stress['vsd'])<=max(.05,rule['collapse_fraction']*i['vsd'])
                specific=sham['vsd']>=.5*i['vsd'] and sham['vsd']-stress['vsd']>.05
                category='residual_target_source_support' if stress['vsd']>.05 else 'apparent_engagement_weak_grounding_candidate' if retained and collapsed and specific else 'unresolved_or_weak_source_support'
                labels.append({'id':stress['id'],'base_id':base,'split':i['split'],'condition':condition,
                    'state':category,'retained_engagement':retained,'collapsed_target_vsd':collapsed,'sham_specific':specific,
                    'native_answer_after_label':stress['native_answer'],'native_correctness_after_label':stress['native_correctness'],
                    'native_answer_differs_from_both_references':all(stress['native_answer']!=c[ref]['native_answer'] for ref in ['unrelated','no_image']),
                    'native_answer_matches_both_references':all(stress['native_answer']==c[ref]['native_answer'] for ref in ['unrelated','no_image']),
                    'prior_like_classification':'Not established by answer agreement or own-prefix distribution similarity alone.',
                    'strict_semantic_mirage':False,'mask_plus_yes_is_hallucination':False})
            for k,v in divergence.items():contrasts['grounding_minus_'+k+'_slope'][base]=sum(v)/5.
        else:
            # Error-oriented tests require an actual explicit wrong native yes.
            if i['native_answer']=='yes':
                for source,effect in i['source_effects'].items():
                    error_diagnostics.append({'id':i['id'],'source':source,**effect,
                        'error_scope':'Disagreement with fixed POPE/COCO reference; preserve independent category-boundary review.',
                        'object_hallucination_presence':i['object_hallucination_presence'],
                        'source_review_note':i['source_review_note'],
                        'error_promoting_direction':effect['removal_delta_yes_logP']<0 and effect['removal_delta_yes_minus_no']<0})
        distributions={cond:np.load(paths[row['id']])['log_probabilities'] for cond,row in c.items() if cond in ['intact','strong','mask','no_image','unrelated']}
        for cond in ['intact','strong','mask']:
            if cond not in distributions:continue
            for reference in ['no_image','unrelated']:
                similarities.append({'base_id':base,'split':i['split'],'present':i['present'],'condition':cond,'reference':reference,
                    **distribution_similarity(distributions[cond],distributions[reference]),
                    'candidate_margin_distance':abs(c[cond]['margin']-c[reference]['margin']),
                    'prefix_controlled':False})
    stats={}
    for split in ['discovery','confirmation']:
        table={}
        for key,values in contrasts.items():
            ids=sorted(b for b in values if bases[b]['intact']['split']==split)
            table[key]=paired_effect([values[b] for b in ids],groups=[bases[b]['intact']['group_id'] for b in ids])
        for result,p in zip(table.values(),holm([r['p_raw'] for r in table.values()])):
            result.update(p_holm=p,robust=robustness(result,p))
        stats[split]=table
    for kind,present in [('present',True),('absent',False)]:
        write_jsonl(OUT/'c3_object_stress'/f'{kind}_object_scores.jsonl',[r for r in rows if r['present']==present])
    write_jsonl(OUT/'c3_object_stress/target_vsd.jsonl',[{k:r[k] for k in ['id','base_id','split','condition','vsd','margin']} for r in rows if r['present']])
    write_jsonl(OUT/'c3_object_stress/passive_features.jsonl',rows)
    write_json(OUT/'c3_object_stress/prior_similarity.json',{'comparisons':similarities,'caveat':'Different own native prefixes; descriptive similarity, not isolated image effect or zero visual influence.'})
    conf=stats['confirmation'];robust=[c for c in ['strong','mask'] if conf[f'sham_minus_{c}__vsd']['robust']]
    div=[k for k,v in conf.items() if k.startswith('grounding_minus') and v['robust']]
    candidates=[r for r in labels if r['split']=='confirmation' and r['state']=='apparent_engagement_weak_grounding_candidate']
    separated=[r for r in candidates if r['native_answer_differs_from_both_references']]
    reference_yes=[c['intact'] for c in bases.values() if not c['intact']['present'] and c['intact']['native_answer']=='yes']
    write_json(OUT/'c3_object_stress/replication_assessment.json',{'replication_support':bool(robust and div and candidates and separated),
        'robust_target_vsd_levels':robust,'robust_continuous_divergences':div,'confirmation_mirage_like_candidates':len(candidates),
        'candidate_behavior_differs_from_both_reference_answers':len(separated),
        'behavioral_gate_scope':'Descriptive native-answer separation from both unrelated/no-image; own-prefix differences do not isolate a causal residual-image effect.',
        'statistics':stats,'condition_labels':labels,'error_oriented_absent_diagnostics':error_diagnostics,
        'absent_native_wrong_yes_events':len({r['id'] for r in error_diagnostics}),
        'absent_yes_count_scope':'Reference-disagreeing native yes; not automatically a confirmed objective object hallucination. See preserved category-boundary adjudication.',
        'absent_yes_hallucination_adjudications':dict(Counter(i['object_hallucination_presence'] for i in reference_yes)),
        'limitations':['No complete-evidence-removal claim for object masks.','Own-condition prefixes include natural adaptation.','No nonexistent queried-object ROI invented.']})
    print('C3 robust target VSD levels:',robust,'divergences:',div,'candidate count:',len(candidates))


if __name__=='__main__':main()
