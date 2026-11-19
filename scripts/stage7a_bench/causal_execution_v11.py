"""Execute one verified frozen event, releasing the native root before edits.

The launch boundary must load membership through load_frozen_pilot and verify
the actual-model mechanics certificate. This helper does not admit a pilot,
certify prefix equivalence or classify prior-fill from unavailable controls.
"""
import gc
import time

import torch

from scripts.stage7a_bench.causal_assay_v2 import score_frozen_sources
from scripts.stage7a_bench.causal_controls_v11 import score_reviewed_local_controls
from scripts.stage7a_bench.causal_prefix_v11 import make_benchmark_root
from scripts.stage7a_bench.document_inputs_v2 import prepare_document
from scripts.stage7a_bench.image_inputs_v2 import prepare_condition as prepare_image
from scripts.stage7a_bench.prior_controls_v11 import score_prior_controls
from scripts.stage7a_bench.source_mapping_v2 import map_source_boxes


def release(device):
    gc.collect()
    if torch.device(device).type == 'cuda':
        torch.cuda.empty_cache()


def require_checks(checks):
    if not checks or any(value is not True for value in checks.values()):
        raise RuntimeError('Causal execution checks failed: ' + str(checks))


@torch.inference_mode()
def execute_verified_event(model, processor, entry, device, *, mechanics):
    if (entry.get('causal_pilot_frozen') is not True or
            entry.get('selection_used_causal_or_passive_scores') is not False or
            entry.get('pilot_stratum') not in ('failure', 'faithful')):
        raise ValueError('Execution requires verified frozen pilot membership and stratum')
    started = time.perf_counter()
    row = entry['row']
    prepare = prepare_document if row.get('document_path') else prepare_image
    prepared, root = None, None
    try:
        prepared, meta = prepare(processor, row, device)
        if meta != entry['native_input']:
            raise ValueError('Reconstructed native input differs from frozen metadata')
        if map_source_boxes(meta, entry['source_annotation']['sources'])['groups'] != entry['source_groups']:
            raise ValueError('Reconstructed source mapping differs from frozen groups')
        root, replay = make_benchmark_root(model, prepared, row, entry['event'])
        prepared = None
        sources = score_frozen_sources(model, root, entry, mechanics=mechanics)
        require_checks(sources['checks'])
    finally:
        prepared, root = None, None
        release(device)
    local = score_reviewed_local_controls(model, processor, entry, meta, device)
    require_checks(local['checks'])
    prior = score_prior_controls(model, processor, entry, meta, device)
    require_checks(prior['checks'])
    if any(part['passive_features_collected'] is not False for part in (sources, local, prior)):
        raise ValueError('Passive feature evidence is outside this causal assay')
    distribution_keys = [key for part in (sources, local, prior) for key in part['distributions']]
    if len(distribution_keys) != len(set(distribution_keys)):
        raise ValueError('Native and control distribution keys overlap')
    if set(local['controls']) & set(prior['controls']):
        raise ValueError('Local and prior control names overlap')
    checks = {**sources['checks'], **local['checks'], **prior['checks'], 'native_input_exact':True}
    checks['all_finite'] = all(arm.get('finite') is True for arm in
        [*sources['arms'].values(), *local['controls'].values(), *prior['controls'].values()])
    require_checks(checks)
    result = dict(id=entry['id'], event_id=entry['event_id'], base_id=entry['base_id'],
        benchmark=entry['benchmark'], condition=entry['condition'],
        analysis_family_id=entry['analysis_family_id'], pilot_stratum=entry['pilot_stratum'],
        arms=sources['arms'], controls={**local['controls'], **prior['controls']}, checks=checks,
        control_audits=local['control_audits'], control_provenance=local['control_provenance'],
        semantic_controls_available=local['semantic_controls_available'], prefill_audit=replay,
        fixed_prior_controls=prior['provenance'], fixed_prior_control_audits=prior['control_audits'],
        prior_convergence_certified=False, source_assay_mechanics=mechanics,
        seconds=time.perf_counter()-started, passive_features_collected=False, complete=True,
        completion_scope='All frozen source windows and available reviewed local/prior controls; '
                         'fresh native prior convergence not certified')
    return result, {**sources['distributions'], **local['distributions'], **prior['distributions']}
