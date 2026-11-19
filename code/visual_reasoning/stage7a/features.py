"""Fixed passive feature families and image-family-safe feasibility splits."""
import math


def feature_families(entry, report, residual_vectors):
    groups = entry['source_groups']
    layout = {'condition='+entry['condition']: 1., 'dataset='+entry['dataset']: 1.,
              'cohort='+entry['cohort']: 1., 'claim_kind='+entry['reviewed_claim']['kind']: 1.,
              'physical_demand='+entry['physical_demanded_source']: 1.,
              'log_prefix_length': math.log1p(report['generated_prefix_length']),
              'log_visual_tokens': math.log1p(report['visual_token_count'])}
    for source in ('T', 'X', 'I'):
        layout['log_tokens_'+source] = math.log1p(len(groups.get(source, [])))
    for role, physical in [('T', entry['physical_demanded_source']), ('X', entry['physical_alternative_source'])]:
        field = entry['row']['fields'].get(physical)
        if field:
            x0, y0, x1, y1 = field['roi']
            width, height = entry['row']['identity']['width'], entry['row']['identity']['height']
            layout[role+'.x_center'] = (x0+x1)/(2*width)
            layout[role+'.y_center'] = (y0+y1)/(2*height)
            layout[role+'.image_area_fraction'] = (x1-x0)*(y1-y0)/(width*height)
    collected = {name: {} for name in ('global_visual', 'source_specific', 'recent_reasoning', 'sink_only')}
    roles = {'global_visual': ['visual'], 'source_specific': ['T', 'X', 'I'],
             'recent_reasoning': ['reasoning', 'recent_reasoning16', 'prompt_text'], 'sink_only': ['sink']}
    for layer in ('28', '29'):
        aggregates = report['telemetry'][layer]['groups']
        for family, sources in roles.items():
            for source in sources:
                values = aggregates.get(source, {})
                collected[family][layer+'.'+source+'.available'] = float(bool(values))
                for key, value in values.items():
                    if key != 'token_count' and isinstance(value, (int, float)):
                        collected[family][layer+'.'+source+'.'+key] = float(value)
        for key in sorted(set(aggregates.get('T', {})) & set(aggregates.get('X', {}))):
            if key != 'token_count':
                collected['source_specific'][layer+'.T_minus_X.'+key] = float(aggregates['T'][key]-aggregates['X'][key])
    residual = {layer+'.residual.'+str(i): float(x) for layer in ('28', '29')
                for i, x in enumerate(residual_vectors[layer])}
    for layer in ('28', '29'):
        residual[layer+'.residual_norm'] = report['residual_norms'][layer]
    release = report['sink_release']
    collected['sink_only']['release.available'] = float(release['available'])
    prior = report['prior_t_minus8']
    collected['recent_reasoning']['t_minus8.available'] = float(prior['available'])
    for layer in ('28', '29'):
        if release['available']:
            collected['sink_only'][layer+'.sink_release'] = release['layers'][layer]
        if prior['available']:
            collected['recent_reasoning'][layer+'.t_minus8.residual_norm'] = prior['residual_norms'][layer]
            collected['recent_reasoning'][layer+'.residual_norm_change'] = report['residual_norms'][layer]-prior['residual_norms'][layer]
    oracle = {key: report[key] for key in ('D', 'L_o', 'L_c', 'predictive_entropy')}
    for condition, values in report['offline_control_distances'].items():
        oracle['distance.'+condition+'.available'] = float(values['available'])
        if values['available']:
            for key in ('JS_nats', 'top50_overlap'):
                oracle['distance.'+condition+'.'+key] = values[key]
    return dict(layout_baseline=layout, **collected, residual_state=residual,
                readout_oracle=oracle,
                source_plus_residual={**collected['source_specific'], **residual})


def image_dependencies(row, group_by_base):
    result = {group_by_base[row['base_id']]}
    if row.get('unrelated_donor'):
        result.add(group_by_base[row['unrelated_donor']])
    return result


def purge_training_bases(train, test, group_by_base):
    """Purge entire training base families that touch any held-out image."""
    test_images = set().union(*(image_dependencies(r, group_by_base) for r in test)) if test else set()
    blocked = {group_by_base[r['base_id']] for r in train if image_dependencies(r, group_by_base) & test_images}
    retained = [r for r in train if group_by_base[r['base_id']] not in blocked]
    assert not any(image_dependencies(r, group_by_base) & test_images for r in retained)
    return retained, dict(held_out_image_families=sorted(test_images), purged_train_families=sorted(blocked))


def task_label(state, task):
    if state.get('tier') != 1 and not (state.get('tier') == 2 and state.get('strong_tier2')):
        return None
    name = state['state']
    if task == 'FAITHFUL_READ_vs_PRIOR_FILL':
        return {'FAITHFUL_READ': 0, 'PRIOR_FILL': 1}.get(name)
    if task == 'FAITHFUL_READ_vs_WRONG_SOURCE_READ':
        return {'FAITHFUL_READ': 0, 'WRONG_SOURCE_READ': 1}.get(name)
    if task == 'correct_source_vs_wrong_source':
        return {'T': 0, 'X': 1, 'P': 1}.get(state.get('source_identity'))
    if task == 'grounded_vs_ungrounded':
        # Here grounded means visual-source-coupled, not necessarily faithful
        # to demanded T. Wrong-source and stale-source reads still use vision.
        if name == 'PRIOR_FILL': return 1
        if state.get('source_identity') in ('T', 'X', 'P'): return 0
        return None
    raise ValueError('Task outside frozen design')
