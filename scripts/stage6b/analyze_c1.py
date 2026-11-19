"""Discovery freeze and unchanged confirmation of C1 fixed-prefix stress."""
import argparse
from collections import defaultdict,Counter
import math
import numpy as np
from scripts.stage6b.common import ROOT,OUT,SOURCE,read_json,read_jsonl,sha,write_json,write_jsonl,verify_stage6a
from scripts.stage6b.event_results import load_run,feature_values,distribution_similarity
from visual_reasoning.stage6b.mirage import classify
from visual_reasoning.stage6b.statistics import paired_effect,holm,robustness

MANIFEST=OUT/'c1_mirage/fixed_prefix_manifest.jsonl'
LEVELS=['mild','strong','mask']
FEATURES=['vsd','margin','attention_density','qk_cosine','alpha_v_norm']


def protocol():
    return {'version':1,'effect_floor':.05,'collapse_fraction':.2,'engagement_retention':.8,
        'sham_grounding_retention':.5,'absolute_engagement_fit':'Q25 of positive discovery intact values, per attention_density and alpha_v_norm',
        'semantic_gate':'CF > 0.05 + abs(intact Dx - render-sham Dx)',
        'causal_collapse':'abs(stress VSD) <= max(0.05, 0.2 * intact VSD); large negative VSD is causal use, not absent use',
        'semantic_collapse':'stress Dx <= 0.2 * intact Dx, with intact Dx > 0.05',
        'sham_specificity':'sham VSD >= 0.5 intact VSD; sham-stress VSD and Dx both >0.05',
        'conditions':['strong','mask'],'correctness_defines_label':False,
        'continuous_scaling':'Discovery pooled seven-condition standard deviation, each feature separately; same scales on confirmation',
        'divergence':'(sham-stress VSD)/SD(VSD) - (sham-stress feature)/SD(feature); ordinal-severity slope through zero across mild,strong,mask',
        'statistical_family':'15 intact-stress drops + 15 sham-stress contrasts + 3 engagement-vs-VSD slope divergences; Holm within all33 by split',
        'no_threshold_search':True,'same_path_requirement':True}


def flatten(entries,results):
    rows=[]
    for eid,e in entries.items():
        r=results[eid];n=r['arms']['N'];cond=e['condition']
        f=feature_values(r,'placebo_T' if cond=='unrelated' else 'T')
        rows.append({'id':eid,'base_id':e['base_id'],'group_id':e['group_id'],'dataset':e['dataset'],
            'split':e['split'],'condition':cond,'margin':n['D'],'reverse_margin':-n['D'],
            'correct_logP':n['L_o'],'foil_logP':n['L_c'],
            'P_x_geometric_mean':math.exp(n['L_o']),'P_xprime_geometric_mean':math.exp(n['L_c']),
            'P_x_sequence':math.exp(n['original_candidate']['sum_log_probability']),
            'P_xprime_sequence':math.exp(n['counterfactual_candidate']['sum_log_probability']),
            'candidate_details':{k:n[k] for k in ['original_candidate','counterfactual_candidate']},
            'vsd':n['D']-r['arms']['T_W2']['D'] if 'T_W2' in r['arms'] else None,
            'vsd_w8':n['D']-r['arms']['T_W8']['D'] if 'T_W8' in r['arms'] else None,
            **f,'entropy':r['passive']['predictive_entropy'],
            'sink_mass':feature_values(r,'sink')['attention_mass'],
            'global_visual_attention':feature_values(r,'visual')['attention_mass'],
            'current_query':r['current_query_zero_based'],
            'prefix_literal_target_occurrences':e['prefix_literal_target_occurrences'],
            'local_numeric_readout_correctness':'CORRECT' if n['D']>0 else 'INCORRECT' if n['D']<0 else 'TIE',
            'correctness_scope':'Fixed-prefix x-versus-xprime preference only; not a generated native claim or geometry assessment.'})
    return rows


def grouped(rows):
    result=defaultdict(dict)
    for r in rows:result[r['base_id']][r['condition']]=r
    return result


def freeze():
    assert not (OUT/'raw/c1_confirmation_01').exists()
    entries,results,_=load_run('c1_discovery_01',MANIFEST,'discovery')
    rows=flatten(entries,results);bases=grouped(rows)
    rule=protocol()
    assert read_json(OUT/'config/mirage_rule_protocol.json')==rule
    intact=[b['intact'] for b in bases.values()]
    rule['absolute_engagement']={k:float(np.quantile([r[k] for r in intact if r[k]>0],.25)) for k in ['attention_density','alpha_v_norm']}
    rule['feature_scales']={k:max(float(np.std([r[k] for r in rows if r['condition'] in ['intact']+LEVELS+['sham_'+x for x in LEVELS]],ddof=1)),1e-12) for k in FEATURES}
    rule['discovery_bases']=len(bases);rule['discovery_events']=len(rows)
    rule['manifest_sha256']=sha(MANIFEST);rule['protocol_sha256']=sha(OUT/'config/mirage_rule_protocol.json')
    rule['discovery_signatures']={str(rank):sha(OUT/'raw/c1_discovery_01'/f'shard_{rank:02d}/signature.json') for rank in range(2)}
    write_json(OUT/'config/mirage_discovery_rule.json',rule,freeze=True)
    write_jsonl(OUT/'c1_mirage/discovery_fixed_prefix_scores.jsonl',rows)
    print('Mirage rule frozen on47discovery bases; no correctness or confirmation scores selected thresholds.')


def contrasts(bases,rule):
    values=defaultdict(dict)
    for base,c in bases.items():
        for level in LEVELS:
            for k in FEATURES:
                values[f'intact_to_{level}__{k}'][base]=c['intact'][k]-c[level][k]
                values[f'sham_minus_{level}__{k}'][base]=c['sham_'+level][k]-c[level][k]
        for k in ['attention_density','qk_cosine','alpha_v_norm']:
            divergences=[(c['sham_'+level]['vsd']-c[level]['vsd'])/rule['feature_scales']['vsd']-(c['sham_'+level][k]-c[level][k])/rule['feature_scales'][k] for level in LEVELS]
            values['grounding_minus_'+k+'_degradation_slope'][base]=sum((i+1)*v for i,v in enumerate(divergences))/14
    return values


def statistics(bases,rule):
    values=contrasts(bases,rule);result={}
    for key,v in values.items():
        ids=sorted(v);result[key]=paired_effect([v[b] for b in ids],groups=[bases[b]['intact']['group_id'] for b in ids])
    corrected=holm([r['p_raw'] for r in result.values()])
    for (key,r),p in zip(result.items(),corrected):r.update(p_holm=p,robust=robustness(r,p))
    return result


def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['protocol','freeze','analyze']);args=p.parse_args()
    if args.action=='protocol':
        write_json(OUT/'config/mirage_rule_protocol.json',protocol(),freeze=True);return
    if args.action=='freeze':freeze();return
    verify_stage6a();rule=read_json(OUT/'config/mirage_discovery_rule.json')
    assert rule['manifest_sha256']==sha(MANIFEST)
    rows=[];paths={};entries={}
    for split in ['discovery','confirmation']:
        e,r,p=load_run('c1_'+split+'_01',MANIFEST,split);rows+=flatten(e,r);entries.update(e);paths.update(p)
    bases=grouped(rows);mechanics={r['event_id']:r for r in read_json(SOURCE/'audit/manipulation_audit.json')['records'] if r['cohort']=='C1'}
    stats={split:statistics({b:c for b,c in bases.items() if c['intact']['split']==split},rule) for split in ['discovery','confirmation']}
    labels=[];cfrows=[];similarities=[]
    for base,c in bases.items():
        cf=c['intact']['margin']-c['counterfactual']['margin'];sham=c['intact']['margin']-c['counterfactual_render_sham']['margin']
        cfrows.append({'base_id':base,'split':c['intact']['split'],'dataset':c['intact']['dataset'],'CF':cf,'render_sham_effect':sham,'beyond_sham':cf-abs(sham),
            'validated':cf>.05+abs(sham),'intact_Dx':c['intact']['margin'],'counterfactual_Dx':c['counterfactual']['margin'],
            'direction_specific_follows_both':c['intact']['margin']>0 and c['counterfactual']['margin']<0})
        for cond in ['strong','mask']:
            m=mechanics[c[cond]['id']];s=mechanics[c['sham_'+cond]['id']]
            verified=all(a['status']=='PASS' and a['outside_mask_exact'] and a['matched_target_sham_area'] and a['sham_disjoint'] for a in [m,s])
            label=classify(c['intact'],c[cond],c['sham_'+cond],cf,sham,verified,rule)
            label.update(base_id=base,id=c[cond]['id'],condition=cond,split=c['intact']['split'],dataset=c['intact']['dataset'],
                local_numeric_readout_correctness=c[cond]['local_numeric_readout_correctness'],
                post_label_outcome='error_associated_candidate_preference' if c[cond]['margin']<0 else 'benign_candidate_preference' if c[cond]['margin']>0 else 'tied_candidate_preference',
                native_hallucination_claim=False,scope='Target-local semantic contrast; not zero all-image influence or a native generated hallucination.')
            labels.append(label)
        distributions={cond:np.load(paths[c[cond]['id']])['log_probabilities'] for cond in ['intact','strong','mask','unrelated','no_image']}
        for cond in ['intact','strong','mask','unrelated']:
            for reference in ['no_image','unrelated']:
                if cond==reference:continue
                similarity=distribution_similarity(distributions[cond],distributions[reference])
                similarities.append({'base_id':base,'split':c['intact']['split'],'condition':cond,'reference':reference,**similarity,
                    'candidate_margin_distance':abs(c[cond]['margin']-c[reference]['margin'])})
    write_jsonl(OUT/'c1_mirage/fixed_prefix_scores.jsonl',rows)
    write_jsonl(OUT/'c1_mirage/target_vsd_by_condition.jsonl',[{k:r[k] for k in ['id','base_id','dataset','split','condition','vsd','vsd_w8','margin']} for r in rows])
    write_json(OUT/'c1_mirage/sham_did.json',{'statistics':stats,'contrasts':contrasts(bases,rule),
        'sign_convention':'Positive sham-minus-stress = evidence-specific loss; opposite sign to algebraic DiD in plan.'})
    write_json(OUT/'c1_mirage/counterfactual_followability.json',{'bases':cfrows})
    write_json(OUT/'c1_mirage/no_image_similarity.json',{'comparisons':similarities,'interpretation':'Supporting prior-like similarity; not zero visual use.'})
    for split in ['discovery','confirmation']:
        selected=[r for r in labels if r['split']==split];strict=[r for r in selected if r['strict_mirage']]
        nbase=len({r['base_id'] for r in selected});nstrict=len({r['base_id'] for r in strict})
        first={b:next(r['condition'] for r in strict if r['base_id']==b) for b in sorted({r['base_id'] for r in strict})}
        write_json(OUT/'c1_mirage'/f'mirage_{split}.json',{'rule_sha256':sha(OUT/'config/mirage_discovery_rule.json'),
            'n_bases':nbase,'strict_event_count':len(strict),'strict_base_count':nstrict,'strict_base_fraction':nstrict/nbase,
            'first_transition_condition':first,'post_label_outcomes':dict(Counter(r['post_label_outcome'] for r in strict)),
            'classification_rows':selected,'denominator':'All frozen bases; strict CF eligibility reported separately.'})
    conf=stats['confirmation']
    divergences=[k for k,v in conf.items() if k.startswith('grounding_minus') and v['robust']]
    grounding=[l for l in ['strong','mask'] if conf[f'sham_minus_{l}__vsd']['robust'] and conf[f'sham_minus_{l}__margin']['robust']]
    strict=[r for r in labels if r['split']=='confirmation' and r['strict_mirage']]
    w8_stats={}
    confirmation_bases={b:c for b,c in bases.items() if c['intact']['split']=='confirmation'}
    for level in ['strong','mask']:
        ordered=sorted(confirmation_bases)
        w8_stats[level]=paired_effect([bases[b]['intact']['vsd_w8']-bases[b][level]['vsd_w8'] for b in ordered],
            groups=[bases[b]['intact']['group_id'] for b in ordered])
    for result,p in zip(w8_stats.values(),holm([r['p_raw'] for r in w8_stats.values()])):
        result.update(p_holm=p,robust=robustness(result,p))
    w8_labels=[]
    for label in strict:
        c=bases[label['base_id']];native=c['intact']['vsd_w8'];stress=c[label['condition']]['vsd_w8']
        w8_labels.append({'id':label['id'],'native_W8':native,'stress_W8':stress,
            'W8_grounding_collapse':native>.05 and abs(stress)<=max(.05,.2*native),
            'scope':'No W8sham arm was predeclared; sensitivity cannot independently establish W8target-vs-sham specificity.'})
    write_json(OUT/'c1_mirage/w8_sensitivity.json',{'confirmation_drop_statistics':w8_stats,
        'W2_strict_mirage_events':w8_labels,'interpretation':'Local source dependence over the last8queries; neither W2norW8 establishes zero influence of earlier visual acquisition.'})
    write_json(OUT/'c1_mirage/claim_assessment.json',{'strong_mirage_claim':bool(divergences and grounding and strict),
        'robust_continuous_divergences':divergences,'robust_joint_grounding_levels':grounding,'confirmation_strict_events':len(strict),
        'confirmation_strict_bases':len({r['base_id'] for r in strict}),
        'strict_W2_events_with_W8_collapse':sum(r['W8_grounding_collapse'] for r in w8_labels),
        'scope':'Frozen C1 target-local fixed-prefix effects; domain breadth assessed separately; no claim of zero all-image use.'})
    print(read_json(OUT/'c1_mirage/claim_assessment.json'))


if __name__=='__main__':main()
