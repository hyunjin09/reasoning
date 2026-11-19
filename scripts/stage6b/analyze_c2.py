"""Frozen C2 factorial contrasts and optional high-attention matched analysis."""
import math
from collections import defaultdict
from scripts.stage6b.common import OUT, read_json, write_json, write_jsonl, sha
from scripts.stage6b.c2_results import load_complete_run, flatten
from visual_reasoning.stage6b.statistics import paired_effect, holm, robustness


def matched_pairs(families, frozen):
    threshold=frozen['high_attention_density_threshold'];rules=frozen['matching'];pairs=[]
    for base,cells in families.items():
        aligned=cells['A_only'];density=aligned['focal_features']['attention_density']
        if density<threshold:continue
        options=[]
        for order,cell in enumerate(['AR','R_only']):
            other=cells[cell];other_density=other['focal_features']['attention_density']
            if other_density<threshold:continue
            log_ratio=abs(math.log(other_density/density))
            progress=abs(other['normalized_progress']-aligned['normalized_progress'])
            ratio=max(other['correct_candidate_tokens'],aligned['correct_candidate_tokens'])/min(other['correct_candidate_tokens'],aligned['correct_candidate_tokens'])
            if (log_ratio>rules['attention_log_ratio_max'] or progress>rules['normalized_progress_difference_max']
                    or ratio>rules['candidate_token_length_ratio_max'] or other['focal_roi_tokens']!=aligned['focal_roi_tokens']):continue
            options.append((log_ratio,order,other,progress,ratio))
        if options:
            distance,_,other,progress,ratio=min(options,key=lambda v:v[:2])
            pairs.append({'base_id':base,'group_id':aligned['group_id'],'alignment_event':aligned['id'],
                'retrieval_event':other['id'],'attention_log_ratio':distance,'progress_difference':progress,
                'candidate_length_ratio':ratio,'roi_token_count':aligned['focal_roi_tokens'],
                'effects':{str(w):other['vsd']['T'][str(w)]-aligned['vsd']['T'][str(w)] for w in [2,8]}})
    return pairs


def factorial(rows, frozen):
    families=defaultdict(dict)
    for r in rows:families[r['base_id']][r['condition']]=r
    assert all(set(c)=={'AR','A_only','R_only','Neither'} for c in families.values())
    contrasts=defaultdict(list);groups=[];per_base=[]
    for base,c in families.items():
        groups.append(c['AR']['group_id']);effects={}
        for feature in ['attention_density','qk_cosine','scaled_logit','alpha_v_norm','post_wo_norm']:
            f=lambda cell:c[cell]['focal_features'][feature]
            effects['alignment_'+feature]=(f('AR')+f('A_only')-f('R_only')-f('Neither'))/2
        for w in [2,8]:
            focal=lambda cell:c[cell]['vsd']['T'][str(w)]
            demanded=lambda cell:c[cell]['vsd'][c[cell]['roles']['demanded']][str(w)]
            effects[f'focal_demand_W{w}']=(focal('AR')+focal('R_only')-focal('A_only')-focal('Neither'))/2
            effects[f'AR_minus_A_only_focal_W{w}']=focal('AR')-focal('A_only')
            effects[f'R_only_minus_Neither_focal_W{w}']=focal('R_only')-focal('Neither')
            effects[f'current_demanded_source_factor_W{w}']=(demanded('AR')+demanded('R_only')-demanded('A_only')-demanded('Neither'))/2
        for k,v in effects.items():contrasts[k].append(v)
        per_base.append({'base_id':base,'group_id':groups[-1],'effects':effects})
    stats={name:paired_effect(values,groups) for name,values in contrasts.items()}
    pairs=matched_pairs(families,frozen)
    sufficient=len(pairs)>=frozen['matching']['minimum_confirmation_pairs']
    if sufficient:
        for w in [2,8]:
            stats[f'matched_retrieval_minus_A_only_W{w}']=paired_effect(
                [r['effects'][str(w)] for r in pairs],[r['group_id'] for r in pairs])
    adjusted=holm([r['p_raw'] for r in stats.values()])
    for result,pvalue in zip(stats.values(),adjusted):
        result.update(p_holm=pvalue,robust=robustness(result,pvalue))
    return {'families':len(families),'events':len(rows),'contrasts':stats,'base_effects':per_base,
        'matched_high_attention':{'status':'SUFFICIENT' if sufficient else 'INSUFFICIENT',
            'pairs':pairs,'count':len(pairs),'minimum':frozen['matching']['minimum_confirmation_pairs'],
            'threshold_unchanged':True,'threshold':frozen['high_attention_density_threshold']}}


def feature_factor_interactions(rows, scaling):
    families=defaultdict(dict)
    for row in rows:families[row['base_id']][row['condition']]=row
    output={}
    for feature in scaling['reported_features']:
        records=[]
        for base,cells in families.items():
            def effects(getter):
                ar,a,r,n=[getter(cells[k]) for k in ['AR','A_only','R_only','Neither']]
                return (ar+a-r-n)/2,(ar+r-a-n)/2
            ea,er=effects(lambda c:c['focal_features'][feature])
            ca,cr=effects(lambda c:c['vsd']['T']['2'])
            ea/=scaling['scales'][feature];er/=scaling['scales'][feature]
            ca/=scaling['scales']['focal_vsd_W2'];cr/=scaling['scales']['focal_vsd_W2']
            records.append({'base_id':base,'group_id':cells['AR']['group_id'],
                'engagement_alignment_z':ea,'engagement_demand_z':er,
                'causal_alignment_z':ca,'causal_demand_z':cr,
                'feature_family_by_factor_interaction':(ea-er)-(ca-cr)})
        effects=paired_effect([r['feature_family_by_factor_interaction'] for r in records],
                              [r['group_id'] for r in records])
        output[feature]={'base_components':records,'descriptive_effect':{k:v for k,v in effects.items() if k!='p_raw'},
                         'scope':scaling['role']}
    return output


def main():
    frozen=read_json(OUT/'config/c2_confirmation_freeze.json')
    assert frozen['status']=='FROZEN_BEFORE_CONFIRMATION'
    assert frozen['statistical_families_sha256']==sha(OUT/'config/statistical_families.json')
    all_rows=[];results={};w2=[];w8=[];split_rows={}
    for split,run in [('discovery','c2_discovery_01'),('confirmation','c2_confirmation_01')]:
        manifest,raw=load_complete_run(run,split)
        flat=[flatten(manifest[eid],r) for eid,r in raw.items()]
        split_rows[split]=flat
        all_rows+=flat;results[split]=factorial(flat,frozen)
        for eid,r in raw.items():
            for source in ['T','X']:
                for window,dest in [(2,w2),(8,w8)]:
                    arm=r['arms'][f'{source}_W{window}'];native=r['arms']['N']
                    dest.append({'event_id':eid,'base_id':r['base_id'],'split':split,'condition':r['condition'],
                        'source':source,'roles':r['roles'],'window':window,'VSD':native['D']-arm['D'],
                        'native_D':native['D'],'suppressed_D':arm['D'],
                        'native_correct_logP':native['L_o'],'native_foil_logP':native['L_c'],
                        'suppressed_correct_logP':arm['L_o'],'suppressed_foil_logP':arm['L_c'],
                        'foil_logP_change_under_removal':arm['L_c']-native['L_c'],
                        'error_interpretation':'Foil may be called the observed error only when independently matched to the actual wrong claim.'})
    results['pooled_exploratory']=factorial(all_rows,frozen)
    geometry=read_json(OUT/'config/c2_overlap_sensitivity.json')
    disjoint=set(geometry['disjoint_families'])
    results['disjoint_token_sensitivity']={split:factorial([r for r in flat if r['base_id'] in disjoint],frozen)
        for split,flat in split_rows.items()}
    scaling=read_json(OUT/'config/c2_interaction_scaling.json')
    interactions={split:feature_factor_interactions(flat,scaling) for split,flat in split_rows.items()}
    conf=results['confirmation']['contrasts'];disc=results['discovery']['contrasts']
    alignment=[k for k in ['alignment_attention_density','alignment_qk_cosine'] if conf[k]['robust']]
    consistent=disc['focal_demand_W2']['median']>0 and any(disc[k]['median']>0 for k in alignment)
    focal=bool(alignment and conf['focal_demand_W2']['robust'] and conf['focal_demand_W8']['robust'] and consistent)
    literal=bool(alignment and conf['current_demanded_source_factor_W2']['robust']
                 and conf['current_demanded_source_factor_W8']['robust'])
    assessment={'status':'COMPLETE','families':31,'events':124,
        'strong_focal_alignment_retrieval_dissociation':focal,
        'literal_current_demanded_source_factor_gate':literal,
        'confirmed_alignment_features':alignment,'discovery_confirmation_direction_consistent':consistent,
        'token_overlap_families':geometry['overlap_families'],
        'disjoint_confirmation_families':results['disjoint_token_sensitivity']['confirmation']['families'],
        'disjoint_focal_demand_W2':results['disjoint_token_sensitivity']['confirmation']['contrasts']['focal_demand_W2'],
        'source_isolation_limit':'Eight families have shared ROI tokens; report the separately frozen 23-family disjoint-token sensitivity before attributing source-specific effects.',
        'matched_analysis':results['confirmation']['matched_high_attention'],
        'scope':'The frozen manipulation is alignment/demand for a fixed focal ROI. A_only and Neither still demand X. Focal-source and current-demanded-source estimands are both reported; neither establishes global image independence.',
        'claim_gate_note':'Strong focal dissociation requires robust held-out focal-demand W2/W8 and expected alignment attention/QK effects. The literal current-demanded-source contrast from the plan is retained separately because the demanded ROI changes between cells.',
        'failure_causality':'No source is labeled error-promoting from a correct-versus-foil margin alone.',
        'W8_scope':'Both focal and current demanded sources scored, so every planned sensitivity contrast is available.',
        'next_stage_selected':False}
    write_jsonl(OUT/'c2_alignment_retrieval/w2_scores.jsonl',w2)
    write_jsonl(OUT/'c2_alignment_retrieval/w8_scores.jsonl',w8)
    write_jsonl(OUT/'c2_alignment_retrieval/passive_features.jsonl',all_rows)
    write_json(OUT/'c2_alignment_retrieval/factorial_statistics.json',results)
    write_json(OUT/'c2_alignment_retrieval/feature_family_factor_interactions.json',interactions)
    write_json(OUT/'c2_alignment_retrieval/matched_high_attention.json',
               {k:v['matched_high_attention'] for k,v in results.items() if 'matched_high_attention' in v})
    write_json(OUT/'c2_alignment_retrieval/claim_assessment.json',assessment)
    print('C2 complete; focal dissociation gate='+str(focal)+'; literal demanded-source gate='+str(literal))


if __name__=='__main__':main()
