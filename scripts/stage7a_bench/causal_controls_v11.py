"""Score reviewed local edits with the frozen native reasoning prefix.

This is fixed-prefix source-control evidence. It neither generates a new
response nor supplies the matched native convergence gate for PRIOR_FILL.
"""
import gc

import torch

from scripts.stage7a_bench.causal_prefix_v11 import make_benchmark_root
from scripts.stage7a_bench.control_provenance_v11 import load_reviewed_controls
from scripts.stage7a_bench.document_controls_v11 import prepare_control_condition, verify_document_control_geometry
from scripts.stage7a_bench.source_mapping_v2 import map_source_boxes
from visual_reasoning.stage7a.assay import score_bundle


def verify_local_control_geometry(entry, native, changed):
    if native.get('no_image') is not False or changed.get('no_image') is not False:
        raise ValueError('Local image controls require actual native and edited visual inputs')
    for key in ('event_id', 'condition', 'prompt', 'prompt_token_ids',
                'visual_token_indices', 'image_grid_thw'):
        if native[key] != changed[key]:
            raise ValueError('Local control changed native input geometry: ' + key)
    if native.get('image_order', ['image_1']) != changed.get('image_order', ['image_1']):
        raise ValueError('Local control changed image order')
    if (native['event_id'] != entry['event_id'] or
            native['prompt'] != entry['row']['prompt'] or
            native['condition'] != entry['row']['condition']):
        raise ValueError('Native input identity differs from frozen entry')
    fields = ('slot', 'image_grid_thw', 'image_size', 'visual_token_indices')
    def images(meta):
        return meta.get('visual_images') or [dict(slot='image_1',
            image_grid_thw=meta['image_grid_thw'], image_size=meta['image_size'],
            visual_token_indices=meta['visual_token_indices'])]
    left, right = images(native), images(changed)
    if not left or len(left) != len(right) or any(
            any(a[k] != b[k] for k in fields) for a, b in zip(left, right)):
        raise ValueError('Local control changed an image slot, size or token segment')
    for meta in (native, changed):
        if map_source_boxes(meta, entry['source_annotation']['sources'])['groups'] != entry['source_groups']:
            raise ValueError('Source mapping differs from the frozen native event')


@torch.inference_mode()
def score_reviewed_local_controls(model, processor, entry, native_meta, device):
    if (entry.get('causal_pilot_frozen') is not True or
            entry.get('selection_used_causal_or_passive_scores') is not False):
        raise ValueError('Local-control scoring requires a pilot frozen without causal/passive selection')
    variants, provenance = load_reviewed_controls(entry)
    controls, distributions, audits = {}, {}, {}
    for name, variant in variants.items():
        prepared, meta = prepare_control_condition(processor, variant, device)
        verify_local_control_geometry(entry, native_meta, meta)
        if variant.get('document_path'):
            verify_document_control_geometry(native_meta, meta, variant)
        root, replay = make_benchmark_root(model, prepared, variant, entry['event'])
        del prepared
        control, distribution = score_bundle(model, root, entry['event'], entry['source_groups'])
        del root
        if control.get('finite') is not True:
            raise ValueError('Nonfinite local source-control score: ' + name)
        controls[name] = control
        if name.endswith('_sham'):
            distributions[name] = distribution
        audits[name] = dict(input=meta, replay=replay,
            scope='Same frozen native reasoning prefix; reviewed local image edit; no fresh generation')
        gc.collect()
        if torch.device(device).type == 'cuda':
            torch.cuda.empty_cache()
    return dict(controls=controls, distributions=distributions,
        control_audits=audits, control_provenance=provenance,
        semantic_controls_available=bool(variants),
        checks=dict(local_control_input_geometry_exact=True, local_controls_all_finite=True),
        passive_features_collected=False)
