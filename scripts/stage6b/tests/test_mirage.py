from visual_reasoning.stage6b.mirage import classify


def row(vsd=1.,margin=2.,attention=1.,alpha=1.):
    return dict(vsd=vsd,margin=margin,attention_density=attention,alpha_v_norm=alpha)


def rule():
    return dict(effect_floor=.05,collapse_fraction=.2,engagement_retention=.8,
                sham_grounding_retention=.5,absolute_engagement={'attention_density':.1,'alpha_v_norm':.1})


def test_large_negative_source_effect_is_not_absent_causal_use():
    result=classify(row(),row(-2.,0.),row(),3.,.1,True,rule())
    assert not result['strict_mirage'] and not result['grounding_collapsed']


def test_label_needs_semantic_followability_sham_and_engagement():
    assert classify(row(),row(.01,.01),row(),3.,.1,True,rule())['strict_mirage']
    assert not classify(row(),row(.01,.01),row(),.01,.1,True,rule())['strict_mirage']
    assert not classify(row(),row(.01,.01),row(.01,.01),3.,.1,True,rule())['strict_mirage']
    assert not classify(row(),row(.01,.01,.01,.01),row(),3.,.1,True,rule())['strict_mirage']
    assert not classify(row(),row(.01,.01),row(),3.,.1,False,rule())['strict_mirage']
