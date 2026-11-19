"""Prospective coordinates, paired estimands and gates; no model access."""

PRIMARY = ['rds_T', 'vsd_T', 'did', 'r16_minus_e16',
           'target_minus_irrelevant', 'r16_minus_q', 'q_rescue_rds', 'q_rescue_vsd']


def source_windows(one_based_index):
    t = int(one_based_index) - 1
    if t < 0:
        raise ValueError('Historical query coordinate must be positive')
    groups = {f'R{k}': list(range(max(0, t-k), t)) for k in [1,2,4,8,16]}
    groups['E16'] = list(range(t-32, t-16)) if t >= 32 else None
    groups.update({f'P{d}': [t-d] if t >= d else None for d in range(1,9)})
    return groups


def vsd(arms, name, roi='T'):
    return arms[name]['none']['D'] - arms[name][roi]['D']


def paired_effects(states):
    t, m = states['T'], states['M']
    te = lambda state, name, roi='T': vsd(state, 'N', roi) - vsd(state, name, roi)
    result = {
        'rds_T': t['N']['none']['rds'] - t['R16']['none']['rds'],
        'vsd_T': te(t, 'R16'), 'did': te(t, 'R16') - te(m, 'R16'),
        'r16_minus_e16': te(t, 'R16') - te(t, 'E16') if 'E16' in t else None,
        'target_minus_irrelevant': te(t, 'R16') - te(t, 'R16', 'I'),
        'r16_minus_q': te(t, 'R16') - te(t, 'Q'),
        'rds_M': m['N']['none']['rds'] - m['R16']['none']['rds'],
        'vsd_M': te(m, 'R16'), 'q_vsd_T': te(t, 'Q'),
        'irrelevant_vsd_T': te(t, 'R16', 'I'),
        'e16_vsd_T': te(t, 'E16') if 'E16' in t else None,
    }
    result['rds_did'] = result['rds_T'] - result['rds_M']
    return result


def trigger_gate(statistics):
    checks = {name: bool(statistics[name]['robust_positive']) for name in PRIMARY[:5]}
    return {'checks': checks, 'passed': all(checks.values())}
