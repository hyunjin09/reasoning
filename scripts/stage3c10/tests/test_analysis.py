from visual_reasoning.stage3c10.analysis import summarize_family,k80_window
from visual_reasoning.stage3c10.protocol import PRIMARY

def test_unrun_rescue_keeps_eight_test_family_and_base_counts():
    values={k:{str(b):float(b+1) for b in range(24)} for k in PRIMARY[:6]}
    result=summarize_family(values)
    assert result['vsd_T']['N_unique_bases']==24
    assert result['vsd_T']['robust_positive']
    assert result['q_rescue_vsd']['wilcoxon_p']==1
    assert not result['q_rescue_vsd']['robust_positive']

def test_k80_needs_robust_vsd_and_direction_and_does_not_force_monotonicity():
    native={'robust_positive':True,'median':10}
    s={'1':{'median':9,'positive_fraction':.5},'2':{'median':8,'positive_fraction':.75},'4':{'median':3,'positive_fraction':1.}}
    assert k80_window(native,s)['k80']==2
    native['robust_positive']=False
    assert k80_window(native,s)['k80'] is None
