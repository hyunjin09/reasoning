"""Signed, truth-oriented metrics. No thresholds or learned features here."""
import numpy as np


def source_effect(native, suppressed):
    wrong = native['first_wrong_token_log_probability']
    wrong_off = suppressed['first_wrong_token_log_probability']
    margin = native['wrong_minus_correct_token_margin']
    margin_off = suppressed['wrong_minus_correct_token_margin']
    return dict(VSD=native['D']-suppressed['D'],
                EP_claim=native['observed_claim_log_probability']-suppressed['observed_claim_log_probability'],
                EP_token=None if wrong is None or wrong_off is None else wrong-wrong_off,
                EP_margin=None if margin is None or margin_off is None else margin-margin_off,
                EP_claim_margin=native['observed_minus_correct']-suppressed['observed_minus_correct'])


def semantic_effect(native, sham, edited, role):
    key = 'target_semantic' if role == 'T' else 'alternative_semantic'
    original = 'correct' if role == 'T' else 'alternative_original'
    def contrast(arm):
        c = arm['candidates']
        return c[key]['mean_log_probability']-c[original]['mean_log_probability']
    baseline, render, semantic = [contrast(a) for a in (native, sham, edited)]
    return dict(native_contrast=baseline, sham_contrast=render, semantic_contrast=semantic,
                semantic_shift=semantic-baseline, sham_shift=render-baseline,
                net_semantic_beyond_sham=semantic-render,
                native_D=native['D'], sham_D=sham['D'], semantic_D=edited['D'],
                sham_D_change=sham['D']-native['D'],
                orientation=f'logP({key})-logP({original}); positive shift follows edited source')


def distribution_similarity(left, right, k=50):
    a, b = [np.array(x, dtype=np.float64, copy=True).reshape(-1) for x in (left, right)]
    assert a.shape == b.shape and a.size > k and np.isfinite(a).all() and np.isfinite(b).all()
    a -= np.logaddexp.reduce(a)
    b -= np.logaddexp.reduce(b)
    middle = np.logaddexp(a, b)-np.log(2)
    js = .5*(np.sum(np.exp(a)*(a-middle))+np.sum(np.exp(b)*(b-middle)))
    aa, bb = [set(np.argpartition(x, -k)[-k:].tolist()) for x in (a, b)]
    return dict(JS_nats=max(0., float(js)), top50_overlap=len(aa & bb)/k)


def passive_control_distances(condition, distributions):
    """Offline oracle diagnostics from already-scored fixed-prefix controls."""
    result = {}
    for name in ('mask', 'no_image'):
        key = 'N' if condition == name else 'fixed_'+name
        result[name] = (dict(available=True, **distribution_similarity(distributions['N'], distributions[key]))
                        if key in distributions else dict(available=False))
    return result


def compile_metrics(entry, result, distributions):
    native = result['arms']['N']
    effects = {name: source_effect(native, arm) for name, arm in result['arms'].items() if name != 'N'}
    semantic = {}
    for role in ('T', 'X'):
        sham, edited = result['controls'].get(role+'_sham'), result['controls'].get(role+'_semantic')
        if sham is not None and edited is not None:
            semantic[role] = semantic_effect(native, sham, edited, role)
    control_distributions = {}
    # Include every pair in the matched fixed-prefix availability set, rather
    # than allowing a single close no-image comparison to define prior fill.
    selected = {}
    if entry['condition'] in ('intact', 'mask', 'unrelated', 'no_image'):
        selected[entry['condition']] = ('N', native)
    for condition in ('intact', 'mask', 'unrelated', 'no_image'):
        key = 'fixed_'+condition
        if key in result['controls']:
            selected[condition] = (key, result['controls'][key])
    for i, left in enumerate(selected):
        for right in list(selected)[i+1:]:
            ak, arm_a = selected[left]
            bk, arm_b = selected[right]
            control_distributions[left+'__'+right] = dict(
                **distribution_similarity(distributions[ak], distributions[bk]),
                absolute_candidate_margin_difference=abs(arm_a['D']-arm_b['D']),
                scope='fixed native prefix; fresh native evidence identity must be checked separately')
    return dict(id=entry['id'], base_id=entry['base_id'], group_id=entry['group_id'], split=entry['split'],
                dataset=entry['dataset'], cohort=entry['cohort'], condition=entry['condition'],
                readout_type=entry['readout_type'], claim_kind=entry['reviewed_claim']['kind'],
                local_correctness=entry['reviewed_claim']['locally_correct'],
                demand=entry['reviewed_claim']['demand'], source_separation_valid=entry['source_separation_valid'],
                native_D=native['D'], source_effects=effects, semantic_effects=semantic,
                distribution_similarity=control_distributions)
