from visual_reasoning.stage5a.protocol import select_natural, select_atlas, classify_event


def test_natural_prefix_ignores_correctness_and_duplicate_variants():
    rows=[{'base':'1','eligible':True,'local_incorrect':False},
          {'base':'1','eligible':True,'local_incorrect':True},
          {'base':'2','eligible':False,'local_incorrect':True},
          {'base':'3','eligible':True,'local_incorrect':True}]
    assert [r['base'] for r in select_natural(rows,2)]==['1','3']


def test_atlas_semantic_balance_fills_exhausted_stratum_in_natural_order():
    rows=[{'base':str(i),'atlas_eligible':True,'local_incorrect':i==2} for i in range(6)]
    assert [r['base'] for r in select_atlas(rows,4)]==['0','1','2','3']


def test_wrong_final_with_correct_fact_is_not_visual_hallucination():
    result=classify_event(local_correctness='CORRECT',final_correct=False,
        vsd={'T':1.,'X':0.,'I':0.},w8_t=1.,ce_minus_sham=.5,
        temporal='FIRST_USE',integration_error_reviewed=False)
    assert not result['hallucination_subtypes']
    assert not result['integration_failure']
    assert result['grounded_local_globally_wrong']


def test_w8_or_semantic_control_prevents_strong_no_retrieval_label():
    for w8,ce in [(1.,0.),(0.,1.)]:
        result=classify_event(local_correctness='INCORRECT',final_correct=False,
            vsd={'T':0.,'X':0.,'I':0.},w8_t=w8,ce_minus_sham=ce,temporal='FIRST_USE')
        assert not result['unsupported_grounding']
        assert 'H-NR' not in result['hallucination_subtypes']


def test_exact_source_tie_is_not_misretrieval_or_stale_source():
    result=classify_event(local_correctness='INCORRECT',final_correct=False,
        vsd={'T':.3125,'X':.3125,'I':0.},w8_t=.3125,ce_minus_sham=None,
        temporal='REFRESH_AFTER_OTHER_SOURCE')
    assert result['source_tie']
    assert not result['alternative_dominant']
    assert not {'H-MR','H-ST'} & set(result['hallucination_subtypes'])


def test_derived_wrong_answer_is_not_a_visual_hallucination_subtype():
    result=classify_event(local_correctness='INCORRECT',final_correct=False,
        vsd={'T':.2,'X':.9,'I':0.},w8_t=.2,ce_minus_sham=.3,
        temporal='REFRESH_AFTER_OTHER_SOURCE',has_explicit_claim=False)
    assert not result['hallucination_subtypes']


def test_large_negative_suppression_is_not_a_null():
    result=classify_event(local_correctness='INCORRECT',final_correct=False,
        vsd={'T':-.5,'X':0.,'I':0.},w8_t=-.7,ce_minus_sham=0.,
        ce_effect=0.,sham_effect=0.,temporal='FIRST_USE')
    assert not result['local_insensitive']
    assert not result['unsupported_grounding']


def test_counterfactual_presence_alone_does_not_give_tier_one():
    result=classify_event(local_correctness='INCORRECT',final_correct=False,
        vsd={'T':.1,'X':.8,'I':0.},w8_t=.1,ce_minus_sham=0.,
        ce_effect=0.,sham_effect=0.,temporal='REFRESH_AFTER_OTHER_SOURCE')
    assert result['confidence_tier']=='Tier2'
    assert 'H-MR' in result['hallucination_subtypes']
    assert 'H-ST' not in result['hallucination_subtypes']


def test_stale_source_requires_the_previous_source_to_dominate():
    args=dict(local_correctness='INCORRECT',final_correct=False,
        vsd={'T':.1,'X':.8,'M':0.,'I':0.},w8_t=.1,ce_minus_sham=None,
        temporal='REFRESH_AFTER_OTHER_SOURCE')
    assert 'H-ST' not in classify_event(**args,previous_source_roi='M')['hallucination_subtypes']
    assert 'H-ST' in classify_event(**args,previous_source_roi='X')['hallucination_subtypes']


def test_strong_negative_semantic_response_is_conflicting_not_unsupported():
    result=classify_event(local_correctness='INCORRECT',final_correct=False,
        vsd={'T':0.,'X':0.,'I':0.},w8_t=0.,ce_minus_sham=-1.,
        ce_effect=-1.,sham_effect=0.,temporal='FIRST_USE')
    assert result['semantic_conflict']
    assert not result['unsupported_grounding']


def test_confirmation_of_other_alternative_cannot_upgrade_stale_mechanism():
    result=classify_event(local_correctness='INCORRECT',final_correct=False,
        vsd={'T':.1,'X':.9,'M':.8,'I':0.},w8_t=.1,ce_minus_sham=None,
        alternative_ce_minus_sham=1.,alternative_ce_roi='X',previous_source_roi='M',
        temporal='REFRESH_AFTER_OTHER_SOURCE')
    assert result['subtype_confidence_tiers']['H-MR']=='Tier1'
    assert result['subtype_confidence_tiers']['H-ST']=='Tier2'
