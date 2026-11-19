from scripts.stage10a.analyze_dominance_v2 import summary


def panel(values):
    return [dict(image_id='one',condition=c,semantic_score=v,follows_original=v==-1,
        follows_counterfactual=v==1,correct_current_image=False,unscorable=False,at_length_cap=False)
        for c,v in zip(('I0T0','I1T0','I0T1','I1T1'),values)]


def test_text_and_image_factorial_directions():
    text=summary(panel([-1,-1,1,1]));image=summary(panel([-1,1,-1,1]))
    assert text['E_text']['point']==2 and text['E_image']['point']==0
    assert image['E_image']['point']==2 and image['E_text']['point']==0
    assert text['text_minus_image']['point']==2
    assert image['text_minus_image']['point']==-2


def test_joint_only_effect_is_interaction_without_dominance():
    s=summary(panel([-1,-1,-1,1]))
    assert s['E_text']['point']==s['E_image']['point']==1
    assert s['interaction']['point']==2 and s['text_minus_image']['point']==0
