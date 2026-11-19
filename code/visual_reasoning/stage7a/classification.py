"""Conservative plan-defined state rules; numerical values come from discovery.

No passive feature is an input. Unavailable controls and measured null controls
remain different observations, and no-image conditions cannot pass a vacuous
all-visual-weak test.
"""
def classify(entry, metrics, thresholds, *, native_prior_convergence=False):
    claim = entry['reviewed_claim']
    result = dict(id=entry['id'], state='UNRESOLVED', tier=None, source_identity=None,
                  locally_correct=claim['locally_correct'], reasons=[],
                  readout_type=entry['readout_type'], scope='W2 necessity at fixed native evidence prefix',
                  passive_features_used=False)
    def unresolved(reason):
        result['reasons'].append(reason)
        return result
    if entry['readout_type'] != 'V':
        return unresolved('Binding readout is a separate diagnostic, never a substitute for value/error evidence.')
    if claim['demand'] != 'singleton':
        return unresolved('Primary demand is not independently identified as a singleton.')
    effects = metrics['source_effects']
    semantic = metrics['semantic_effects']
    vf, ef = thresholds['vsd_floor'], thresholds['error_floor']
    dm, sf = thresholds['dominance_margin'], thresholds['semantic_floor']

    def effect(source, key):
        return effects.get(source+'_W2', {}).get(key)
    def positive(source, key, floor):
        value = effect(source, key)
        return value is not None and value > floor
    def error_promoting(source):
        return positive(source, 'EP_token', ef) and positive(source, 'EP_margin', ef)
    def semantic_pass(source):
        s = semantic.get(source)
        return bool(s and s['net_semantic_beyond_sham'] > sf and s['semantic_shift'] > sf and
                    abs(s['sham_shift']) <= thresholds['sham_fraction_max']*s['semantic_shift'])
    def semantic_weak(source):
        s = semantic.get(source)
        return s is None or (abs(s['net_semantic_beyond_sham']) <= sf and abs(s['semantic_shift']) <= sf)
    def dominates(source, key):
        value = effect(source, key)
        comparisons = [effect(s, key) for s in ('T', 'X', 'I') if s != source]
        comparisons = [x for x in comparisons if x is not None]
        return value is not None and bool(comparisons) and all(value-x > dm for x in comparisons)
    def set_state(state, source, tier=1, **extra):
        result.update(state=state, source_identity=source, tier=tier, **extra)
        return result

    separation = entry['source_separation_valid']
    target_faithful = positive('T', 'VSD', vf) and dominates('T', 'VSD') and separation
    if claim['locally_correct'] and target_faithful:
        if semantic_pass('T'):
            downstream = entry.get('downstream_review') or {}
            if (downstream.get('integration_error_eligible') is True and downstream.get('later_error') is True and
                    downstream.get('error_char_start', -1) > claim['readout_char_end']):
                return set_state('DOWNSTREAM_INTEGRATION_ERROR', 'T')
            return set_state('FAITHFUL_READ', 'T')
        if 'T' not in semantic:
            return set_state('FAITHFUL_READ', 'T', tier=2, strong_tier2=False,
                             reasons=['Demand and oriented source suppression support T; semantic counterfactual unavailable.'])
        return unresolved('Measured target semantic control failed; cannot relabel an available failed CF as missing Tier2 evidence.')

    if not claim['locally_correct'] and separation:
        wrong_matches_x = claim.get('wrong_claim_matches_alternative', False)
        x_strong = error_promoting('X') and dominates('X', 'EP_margin')
        target_weak_for_error = not error_promoting('T') and semantic_weak('T')
        if x_strong and wrong_matches_x and semantic_pass('X') and target_weak_for_error:
            if entry['source_aliases'].get('P') == 'X' and claim.get('kind') == 'aba_return':
                return set_state('STALE_SOURCE_READ', 'P', harmful=True)
            return set_state('WRONG_SOURCE_READ', 'X')
        if error_promoting('T') and dominates('T', 'EP_margin') and semantic_pass('T'):
            return set_state('SOURCE_COUPLED_EXTRACTION_ERROR', 'T')
        if x_strong:
            result['candidate_state'] = 'SOURCE_ANOMALY'
            result['reasons'].append('Alternative error support lacks convergent source-semantic identification.')

    available = entry['row']['target_availability']
    unavailable = (available in ('printed_target_masked', 'source_image_unavailable', 'unavailable', 'queried_object_absent') or
                   (available == 'degraded' and 'T' in semantic and semantic_weak('T')))
    measured = [effects[k] for k in effects if k.endswith('_W2')]
    all_visual_weak = ('G_W2' in effects and bool(measured) and
                       all(abs(e['VSD']) <= vf and abs(e['EP_claim']) <= ef for e in measured))
    prior_pairs = [r for key, r in metrics['distribution_similarity'].items()
                   if set(key.split('__')) <= {'mask', 'unrelated', 'no_image'}]
    similar = (len(prior_pairs) == 3 and all(r['JS_nats'] <= thresholds['prior_js_max'] and
               r['absolute_candidate_margin_difference'] <= thresholds['prior_margin_max'] and
               r['top50_overlap'] >= thresholds['prior_top50_min'] for r in prior_pairs))
    if (unavailable and all_visual_weak and all(semantic_weak(s) for s in ('T', 'X')) and native_prior_convergence and similar and
            not claim.get('explicit_text_memory_reuse', False)):
        # Masked target semantic edits are structurally absent. All-visual
        # suppression + matched native/prefix controls still identify weak local
        # visual necessity, but this is not full Tier1 semantic certification.
        return set_state('PRIOR_FILL', None, tier=2, strong_tier2=True,
                         reasons=['Target missing or strongly degraded with measured weak target semantic control; weak global/local visual necessity; no strong measured T/X semantic control; matched native and fixed-prefix availability convergence.'])
    if not separation:
        result['reasons'].append('T and X share visual tokens; independent source identity is not identifiable.')
    if claim.get('explicit_text_memory_reuse'):
        result['reasons'].append('Explicit earlier-text reuse cannot by itself certify prior-filled fresh acquisition.')
    return unresolved('Convergent requirements for a named causal state were not met.')
