"""Apply unchanged Stage7A metrics and rules to frozen benchmark pilot evidence.

Legacy discovery/synthetic cohort labels are not new benchmark identities.
Image-present conditions share the intact fixed-prefix role; their actual
photo/screenshot/benchmark condition remains in the returned record.
"""
from copy import deepcopy

from visual_reasoning.stage7a.metrics import compile_metrics
from visual_reasoning.stage7a.classification import classify
from scripts.stage7a_bench.native_prior_convergence_v10 import load_native_convergence


def compile_benchmark_metrics(entry, result, distributions):
    if entry.get('causal_pilot_frozen') is not True or entry.get('pilot_stratum') not in ('failure', 'faithful'):
        raise ValueError('Interpretation requires an explicitly frozen pilot and stratum')
    if result.get('id') != entry['id']:
        raise ValueError('Causal result identity differs from frozen event')
    if result.get('complete') is not True or not result.get('checks') or not all(
            value is True for value in result['checks'].values()):
        raise ValueError('Causal result must be complete with all checks passed')
    if result.get('passive_features_collected') is not False:
        raise ValueError('Causal interpretation cannot use passive feature selection')
    groups = entry['source_groups']
    expected = {'N'} | {s+'_W2' for s in groups} | {s+'_W8' for s in ('T', 'X') if s in groups}
    if set(result['arms']) != expected:
        raise ValueError('Every frozen source needs W2 and every available T/X needs W8')
    controls = result['controls']
    for role in ('T', 'X'):
        pair = {role+'_semantic', role+'_sham'}
        if pair & set(controls) and not pair <= set(controls):
            raise ValueError('Semantic effects require a matched sham')
    if any(a.get('finite') is not True for a in [*result['arms'].values(), *controls.values()]):
        raise ValueError('Causal scores must be finite')
    if entry['row'].get('no_image') or not groups.get('G'):
        raise ValueError('Benchmark source-causal interpretation requires a real visual input')
    adapted = deepcopy(entry)
    adapted.update(group_id=entry['analysis_family_id'], split='benchmark_pilot',
        dataset=entry['benchmark'], cohort=entry['pilot_stratum'], condition='intact')
    adapted['reviewed_claim'].setdefault('kind', 'native_singleton_visual_value')
    metrics = compile_metrics(adapted, result, distributions)
    metrics.update(condition=entry['condition'], analysis_family_id=entry['analysis_family_id'],
        native_family_id=entry.get('native_family_id'),
        fixed_prefix_native_role='intact',
        identity_adaptation='Verified source family; benchmark pilot; actual native condition preserved',
        thresholds_retuned=False, passive_features_used=False)
    return metrics


def classify_benchmark(entry, metrics, thresholds, *, native_convergence_reference=None):
    # Only revalidated raw control generations and full-response reviews can
    # supply this gate; an unverified caller flag/similarity score cannot.
    convergence = load_native_convergence(entry, native_convergence_reference)
    result = classify(entry, metrics, thresholds, native_prior_convergence=convergence['converges'])
    result['native_prior_convergence_available'] = convergence['available']
    result['native_convergence'] = convergence
    result['prior_convergence_unavailable_reason'] = None if convergence['available'] else (
        'Benchmark image/no-image paired screening is not a reviewed matched native '
        'mask/unrelated/no-image convergence certificate.')
    if not entry['source_groups'].get('X') and not entry['source_separation_valid']:
        # The inherited historical corpus always had X. Preserve the original
        # diagnostic while correcting its premise for absent benchmark sources.
        result['inherited_classifier_reasons'] = list(result['reasons'])
        result['reasons'] = [r for r in result['reasons'] if not r.startswith('T and X share visual tokens;')]
        note = 'Primary alternative is unavailable; token overlap is not established.'
        result['source_identifiability_note'] = note
        result['reasons'].append(note)
    return result
