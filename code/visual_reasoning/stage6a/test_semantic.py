from visual_reasoning.stage6a.semantic import classify_span


def test_alignment_context_does_not_become_demand():
    r=classify_span('In the table containing WP2(2), what date is listed for WP2(4)?',
        {'T':r'WP2\(2\)','X':r'WP2\(4\)'},task_sources=['X'])
    assert r['mentioned_sources']==['T','X'] and r['demanded_sources']==['X']
    assert r['explicit_visual_claim_sources']==[]


def test_wrong_numeral_still_defines_semantic_demand():
    r=classify_span('The radius is 5.5 cm.',{'T':r'\bradius\b'})
    assert r['demanded_sources']==['T'] and r['candidate_visual_claim_sources']==['T']
    reviewed=classify_span('The radius is 5.5 cm.',{'T':r'\bradius\b'},manual_claim='The radius is 5.5 cm.')
    assert reviewed['explicit_visual_claim_sources']==['T']


def test_literal_mention_alone_is_unresolved():
    r=classify_span('Radius formula and general sphere theory.',{'T':r'\bradius\b'})
    assert r['mentioned_sources']==['T'] and r['unresolved']


def test_uncertain_claim_does_not_establish_prior_explicit_access():
    r=classify_span('Maybe the radius is 11 cm?',{'T':r'\bradius\b'})
    assert r['demanded_sources']==['T'] and not r['explicit_visual_claim_sources']


def test_digits_in_entity_name_do_not_become_visual_evidence():
    r=classify_span('WP2(2) is mentioned in the table.',{'T':r'WP2\(2\)'})
    assert r['unresolved'] and not r['explicit_visual_claim_sources']


def test_formula_is_not_promoted_to_prior_visual_fact():
    r=classify_span('Surface area is 4πr², where r is the radius. We need the radius.',{'T':r'\bradius\b'})
    assert not r['explicit_visual_claim_sources']


def test_reviewed_unknown_truth_is_not_promoted_to_correct():
    from visual_reasoning.stage6a.semantic import reviewed_visual_correctness
    claims=[{'local_visual_correctness':'CORRECT'},{'local_visual_correctness':'UNRESOLVED'}]
    assert reviewed_visual_correctness(claims)=='UNRESOLVED'
    assert reviewed_visual_correctness([])=='UNRESOLVED'


def test_reviewed_claim_errors_and_correctness_keep_their_scope():
    from visual_reasoning.stage6a.semantic import reviewed_visual_correctness
    assert reviewed_visual_correctness([{'local_visual_correctness':'CORRECT'}])=='CORRECT'
    assert reviewed_visual_correctness([{'local_visual_correctness':'INCORRECT_ROLE'},{'local_visual_correctness':'UNRESOLVED'}])=='INCORRECT'


def test_cross_span_claim_is_assigned_once_where_it_finishes():
    from visual_reasoning.stage6a.semantic import completed_claims
    claim=dict(quote='So yes, there is a chair.',char_start=10,char_end=34)
    spans=[dict(char_start=0,char_end=13),dict(char_start=13,char_end=40)]
    assert completed_claims(spans[0],[claim])==[]
    result=completed_claims(spans[1],[claim])
    assert len(result)==1 and result[0]['quote']==claim['quote']
    assert result[0]['claim_crosses_span_boundary'] is True


def test_claim_ending_at_a_boundary_belongs_to_the_earlier_span():
    from visual_reasoning.stage6a.semantic import completed_claims
    claim=dict(quote='Yes.',char_start=6,char_end=10)
    assert len(completed_claims(dict(char_start=0,char_end=10),[claim]))==1
    assert completed_claims(dict(char_start=10,char_end=15),[claim])==[]
