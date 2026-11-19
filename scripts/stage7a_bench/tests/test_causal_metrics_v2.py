from copy import deepcopy
import numpy as np
import pytest

from scripts.stage7a_bench.causal_metrics_v2 import compile_benchmark_metrics, classify_benchmark


def entry():
    return dict(id='event__e0',base_id='base',benchmark='charxiv',condition='image_present',
        analysis_family_id='verified-shared-image',native_family_id='old-file-name',
        readout_type='V',source_separation_valid=True,source_aliases={},
        reviewed_claim=dict(locally_correct=False,demand='singleton',readout_char_end=15,
            wrong_claim_matches_alternative=True),
        row=dict(target_availability='intact'),source_groups=dict(T=[1],X=[2],G=[1,2]),
        causal_pilot_frozen=True,pilot_stratum='failure')


def arm(correct=0.,foil=-1.,wrong=-2.,native=-2.,tsem=-1.,xorig=-2.,xsem=-3.):
    return dict(D=correct-foil,first_wrong_token_log_probability=wrong,
        wrong_minus_correct_token_margin=wrong-correct,observed_claim_log_probability=native,
        observed_minus_correct=native-correct,finite=True,
        candidates={k:dict(mean_log_probability=v) for k,v in
            dict(correct=correct,foil=foil,native=native,target_semantic=tsem,
                 alternative_original=xorig,alternative_semantic=xsem).items()})


def evidence():
    n=arm()
    result=dict(id='event__e0',complete=True,checks=dict(all_finite=True),
        arms=dict(N=n,T_W2=arm(),X_W2=arm(wrong=-4.,native=-4.),
                  G_W2=arm(),T_W8=arm(),X_W8=arm(wrong=-4.,native=-4.)),
        controls=dict(X_sham=arm(),X_semantic=arm(xsem=1.)),passive_features_collected=False)
    return result,dict(N=np.arange(64,dtype=float))


THRESHOLDS=dict(vsd_floor=.1,error_floor=.1,dominance_margin=.1,semantic_floor=1.,
    sham_fraction_max=.5,prior_js_max=.01,prior_margin_max=.5,prior_top50_min=.8)


def test_wrong_source_signed_orientation_and_verified_family_are_preserved():
    e=entry();r,d=evidence();before=deepcopy(e)
    m=compile_benchmark_metrics(e,r,d)
    assert m['source_effects']['X_W2']['EP_token']==2.
    assert m['source_effects']['X_W2']['EP_margin']==2.
    assert m['semantic_effects']['X']['semantic_shift']==4.
    assert m['group_id']=='verified-shared-image' and m['split']=='benchmark_pilot'
    assert m['condition']=='image_present' and m['dataset']=='charxiv'
    assert e==before
    assert classify_benchmark(e,m,THRESHOLDS)['state']=='WRONG_SOURCE_READ'


def test_alternative_dominance_without_semantic_control_is_not_wrong_source():
    e=entry();r,d=evidence();r['controls']={}
    c=classify_benchmark(e,compile_benchmark_metrics(e,r,d),THRESHOLDS)
    assert c['state']=='UNRESOLVED' and c['candidate_state']=='SOURCE_ANOMALY'


def test_paired_no_image_similarity_alone_cannot_certify_prior_fill():
    e=entry();e['row']['target_availability']='unavailable';r,d=evidence()
    r['arms']={k:arm() for k in r['arms']};r['controls']={'fixed_no_image':arm()}
    d['fixed_no_image']=d['N'].copy()
    m=compile_benchmark_metrics(e,r,d)
    assert set(m['distribution_similarity'])=={'intact__no_image'}
    assert classify_benchmark(e,m,THRESHOLDS)['state']=='UNRESOLVED'


@pytest.mark.parametrize('converges,intact,strong_global,expected', [
    (True, False, False, 'PRIOR_FILL'), (False, False, False, 'UNRESOLVED'),
    (True, True, False, 'UNRESOLVED'), (True, False, True, 'UNRESOLVED')])
def test_reviewed_native_gate_keeps_all_other_inherited_requirements(monkeypatch, converges, intact, strong_global, expected):
    import scripts.stage7a_bench.causal_metrics_v2 as module
    monkeypatch.setattr(module, 'load_native_convergence',
        lambda entry, reference: dict(available=True, converges=converges))
    e=entry(); e['row']['target_availability']='intact' if intact else 'unavailable'
    r,d=evidence(); r['arms']={k:arm() for k in r['arms']}
    if strong_global: r['arms']['G_W2']=arm(correct=-2.)
    r['controls']={'fixed_'+c:arm() for c in ('mask','unrelated','no_image')}
    d.update({'fixed_'+c:d['N'].copy() for c in ('mask','unrelated','no_image')})
    result=classify_benchmark(e,compile_benchmark_metrics(e,r,d),THRESHOLDS,
                              native_convergence_reference={'path':'verified_fixture'})
    assert result['state']==expected and result['native_prior_convergence_available']


@pytest.mark.parametrize('change,match',[
    ('unfrozen','frozen pilot'),('missing_w8','W8'),('wrong_id','identity'),
    ('incomplete','complete'),('passive','passive'),('partial_sham','matched sham')])
def test_incomplete_or_unfrozen_evidence_cannot_be_interpreted(change,match):
    e=entry();r,d=evidence()
    if change=='unfrozen':e['causal_pilot_frozen']=False
    if change=='missing_w8':del r['arms']['X_W8']
    if change=='wrong_id':r['id']='other'
    if change=='incomplete':r['complete']=False
    if change=='passive':r['passive_features_collected']=True
    if change=='partial_sham':del r['controls']['X_sham']
    with pytest.raises(ValueError,match=match):compile_benchmark_metrics(e,r,d)


def test_missing_alternative_is_reported_without_inventing_token_overlap():
    e=entry();e['source_separation_valid']=False;e['source_groups'].pop('X')
    r,d=evidence();r['arms']={k:v for k,v in r['arms'].items() if not k.startswith('X_')};r['controls']={}
    c=classify_benchmark(e,compile_benchmark_metrics(e,r,d),THRESHOLDS)
    assert c['state']=='UNRESOLVED'
    assert c['source_identifiability_note']=='Primary alternative is unavailable; token overlap is not established.'
    assert c['inherited_classifier_reasons']
    assert not any('share visual tokens' in x for x in c['reasons'])
