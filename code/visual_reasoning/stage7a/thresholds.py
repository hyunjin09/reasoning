"""Prospective calibration using discovery negative controls, never state yield."""
from collections import defaultdict
import math
import numpy as np


def family_quantile(rows, key, quantile, *, default):
    """Equal bases within image families; repeated events cannot add weight."""
    bases, groups = defaultdict(list), {}
    for row in rows:
        assert row['split'] == 'discovery', 'Confirmation cannot calibrate rules'
        value = row.get(key)
        if value is not None and np.isfinite(value):
            bases[row['base_id']].append(float(value))
            groups[row['base_id']] = row['group_id']
    families = defaultdict(list)
    for base, values in bases.items():
        families[groups[base]].append(float(np.median(values)))
    values = {g: float(np.median(v)) for g, v in sorted(families.items())}
    return dict(value=float(np.quantile(list(values.values()), quantile)) if values else default,
                quantile=quantile, family_values=values, n_families=len(values),
                fallback_used=not bool(values))


def calibrate(controls):
    assert controls and all(r['split'] == 'discovery' for r in controls)
    estimates = {key: family_quantile(controls, key, q, default=default)
                 for key, q, default in [
                     ('irrelevant_abs_vsd', .95, .05),
                     ('irrelevant_abs_claim_effect', .95, .05),
                     ('irrelevant_abs_wrong_effect', .95, .05),
                     ('sham_abs_semantic_shift', .95, .05),
                     ('sham_js', .95, .05),
                     ('sham_abs_margin_change', .95, .5),
                     ('sham_top50_overlap', .05, .8)]}
    values = {k: v['value'] for k, v in estimates.items()}
    # With few erroneous irrelevant-source controls, also use a conservative
    # two-log-probability noise envelope from correct-claim controls.
    ef = max(.05, values['irrelevant_abs_wrong_effect'],
             2 * values['irrelevant_abs_claim_effect'])
    thresholds = dict(vsd_floor=max(.05, values['irrelevant_abs_vsd']),
                      error_floor=ef, dominance_margin=max(.05, values['irrelevant_abs_vsd']),
                      semantic_floor=max(.05, values['sham_abs_semantic_shift']),
                      sham_fraction_max=.5,
                      prior_js_max=min(.05, max(1e-6, values['sham_js'])),
                      prior_margin_max=min(.5, max(.05, values['sham_abs_margin_change'])),
                      prior_top50_min=max(.8, values['sham_top50_overlap']))
    return thresholds, estimates


def matching_metadata(entry):
    groups = entry['source_groups']
    continuous = {'log_prefix_length': math.log1p(entry['event']['ed_generated_index']),
                  'log_visual_tokens': math.log1p(len(groups.get('G', [])))}
    for source in ('T', 'X', 'I'):
        continuous['log_'+source+'_tokens'] = math.log1p(len(groups.get(source, [])))
    for role, physical in [('T', entry['physical_demanded_source']),
                           ('X', entry['physical_alternative_source'])]:
        field = entry['row']['fields'].get(physical)
        if field:
            x0, y0, x1, y1 = field['roi']
            width, height = entry['row']['identity']['width'], entry['row']['identity']['height']
            continuous[role+'.x_center'] = (x0+x1)/(2*width)
            continuous[role+'.y_center'] = (y0+y1)/(2*height)
            continuous[role+'.area_fraction'] = (x1-x0)*(y1-y0)/(width*height)
    return dict(exact={key: entry[key] for key in ('dataset', 'cohort', 'condition', 'readout_type')},
                continuous=continuous)


def matching_tolerances(entries):
    assert entries and all(e['split'] == 'discovery' for e in entries)
    rows = [dict(base_id=e['base_id'], group_id=e['group_id'], split=e['split'],
                 **matching_metadata(e)['continuous']) for e in entries if e['readout_type'] == 'V']
    keys = sorted(set().union(*(set(r)-{'base_id', 'group_id', 'split'} for r in rows)))
    result = {}
    for key in keys:
        low = family_quantile(rows, key, .25, default=0.)
        high = family_quantile(rows, key, .75, default=0.)
        minimum = .1 if key.startswith('log_') else (.01 if key.endswith('area_fraction') else .05)
        result[key] = dict(tolerance=max(minimum, .5*(high['value']-low['value'])),
                           discovery_family_q25=low['value'], discovery_family_q75=high['value'],
                           n_families=low['n_families'])
    return result
