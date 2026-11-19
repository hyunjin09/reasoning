from visual_reasoning.stage7a.classification import classify


THRESHOLDS = dict(vsd_floor=.1, error_floor=.1, dominance_margin=.1, semantic_floor=.1,
                  sham_fraction_max=.5, prior_js_max=.05, prior_margin_max=.2, prior_top50_min=.5)


def entry():
    return dict(id='e', readout_type='V', reviewed_claim=dict(locally_correct=True, demand='singleton',
                readout_char_end=30, kind='primary'), source_separation_valid=True, source_aliases={},
                row={'target_availability': 'available'}, downstream_review=None)


def test_failed_available_cf_cannot_be_downgraded_to_missing_cf_faithful():
    metrics = dict(source_effects={'T_W2': {'VSD': 2.}, 'X_W2': {'VSD': 0.}},
                   semantic_effects={'T': {'net_semantic_beyond_sham': 0., 'semantic_shift': 0., 'sham_shift': 0.}},
                   distribution_similarity={})
    r = classify(entry(), metrics, THRESHOLDS)
    assert r['state'] == 'UNRESOLVED' and 'failed' in r['reasons'][0]


def test_no_image_all_visual_weak_cannot_pass_vacuously():
    e = entry()
    e['row']['target_availability'] = 'unavailable'
    m = dict(source_effects={}, semantic_effects={}, distribution_similarity={
        key: dict(JS_nats=0., absolute_candidate_margin_difference=0., top50_overlap=1.)
        for key in ['mask__unrelated', 'mask__no_image', 'unrelated__no_image']})
    assert classify(e, m, THRESHOLDS, native_prior_convergence=True)['state'] == 'UNRESOLVED'


def test_wrong_source_needs_both_error_orientation_and_semantic_control():
    e = entry()
    e['reviewed_claim'].update(locally_correct=False, wrong_claim_matches_alternative=True)
    def effect(vsd, token, margin): return dict(VSD=vsd, EP_token=token, EP_margin=margin, EP_claim=token)
    m = dict(source_effects={'T_W2': effect(0, 0, 0), 'X_W2': effect(3, 2, 0)},
             semantic_effects={'X': dict(net_semantic_beyond_sham=2., semantic_shift=2., sham_shift=0.)},
             distribution_similarity={})
    assert classify(e, m, THRESHOLDS)['state'] == 'UNRESOLVED'
    m['source_effects']['X_W2']['EP_margin'] = 2.
    assert classify(e, m, THRESHOLDS)['state'] == 'WRONG_SOURCE_READ'


def test_strong_alternative_semantic_coupling_disqualifies_prior_even_when_w2_is_weak():
    e = entry()
    e['row']['target_availability'] = 'degraded'
    m = dict(source_effects={s+'_W2': dict(VSD=0., EP_claim=0.) for s in ('T', 'X', 'G')},
             semantic_effects={'T': dict(net_semantic_beyond_sham=0., semantic_shift=0., sham_shift=0.),
                               'X': dict(net_semantic_beyond_sham=2., semantic_shift=2., sham_shift=0.)},
             distribution_similarity={key: dict(JS_nats=0., absolute_candidate_margin_difference=0., top50_overlap=1.)
                                      for key in ['mask__unrelated', 'mask__no_image', 'unrelated__no_image']})
    assert classify(e, m, THRESHOLDS, native_prior_convergence=True)['state'] == 'UNRESOLVED'
    m['semantic_effects']['X'] = m['semantic_effects']['T'].copy()
    assert classify(e, m, THRESHOLDS, native_prior_convergence=True)['state'] == 'PRIOR_FILL'
