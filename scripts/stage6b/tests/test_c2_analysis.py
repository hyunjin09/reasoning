from scripts.stage6b.analyze_c2 import factorial


def test_focal_demand_effect_is_not_confused_with_global_image_need():
    rows=[]
    for base in ['a','b']:
        for cell in ['AR','A_only','R_only','Neither']:
            demanded='T' if cell in ['AR','R_only'] else 'X'
            aligned=cell in ['AR','A_only']
            rows.append({'id':base+'__'+cell,'base_id':base,'group_id':base,'condition':cell,
                'roles':{'demanded':demanded},
                'focal_features':{k:(2. if aligned else 1.) for k in ['attention_density','qk_cosine','scaled_logit','alpha_v_norm','post_wo_norm']},
                'vsd':{source:{'2':2. if source==demanded else 0.,'8':2. if source==demanded else 0.} for source in ['T','X']},
                'normalized_progress':.1,'correct_candidate_tokens':1,'focal_roi_tokens':3})
    frozen={'high_attention_density_threshold':1.,'matching':{'attention_log_ratio_max':.35,
        'normalized_progress_difference_max':.2,'candidate_token_length_ratio_max':2.,'minimum_confirmation_pairs':8}}
    result=factorial(rows,frozen)
    assert result['contrasts']['focal_demand_W2']['mean']==2.
    assert result['contrasts']['current_demanded_source_factor_W2']['mean']==0.
    assert result['matched_high_attention']['count']==2
    assert result['matched_high_attention']['status']=='INSUFFICIENT'
