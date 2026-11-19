"""Verify and score reviewed availability controls with the native prefix.

These context comparisons do not establish fresh native claim convergence.
Mask uses the inherited full-target fill of127. Unrelated images come from
another verified frozen source family; no-image preserves the exact question.
"""
from copy import deepcopy
import gc

import numpy as np
import torch

from scripts.stage7a.common import read_json, read_jsonl, sha
from scripts.stage7a_bench.causal_controls_v11 import verify_local_control_geometry
from scripts.stage7a_bench.causal_prefix_v11 import make_benchmark_root
from scripts.stage7a_bench.causal_provenance_v2 import stage_path, verified_families
from scripts.stage7a_bench.image_inputs_v2 import load_asset, prepare_condition
from visual_reasoning.stage7a.assay import score_bundle


def native_assets(entry):
    row = entry['row']
    if row.get('document_path') or row.get('no_image'):
        raise ValueError('Reviewed prior image controls require an image-bearing native row')
    if row.get('image_path'):
        if row.get('image_assets'):
            raise ValueError('Ambiguous native file and image assets')
        meta = entry['native_input']
        return [dict(kind='file', path=row['image_path'], slot='image_1',
            bytes_sha256=row['image_sha256'], decoded_sha256=meta['decoded_image_sha256'],
            size=meta['image_size'])]
    assets = row.get('image_assets', [])
    if not assets or len({a['slot'] for a in assets}) != len(assets):
        raise ValueError('Expected uniquely named native image assets')
    return assets


def variant_row(entry, role, assets):
    row = deepcopy(entry['row'])
    row.update(event_id=entry['event_id']+'__fixed_'+role, condition=role,
        no_image=role == 'no_image', image_path=None, image_assets=deepcopy(assets),
        source_asset_identity=deepcopy(assets),
        target_availability='masked' if role == 'mask' else 'unavailable')
    row.pop('image_sha256', None)
    return row


def verify_prior_controls(entry, review, donors, families):
    assets = native_assets(entry)
    boxes = entry['source_annotation']['sources'].get('T', [])
    if (review.get('status') != 'MANUALLY_REVIEWED_FIXED_PRIOR_CONTROLS' or
            review.get('event_id') != entry['event_id'] or
            review.get('native_input_sha256') != entry['provenance']['input']['sha256'] or
            review.get('semantic_review_sha256') != entry['semantic_review_sha256'] or
            review.get('causal_or_passive_scores_used') is not False or
            review.get('control_outputs_used') is not False or
            review.get('native_assets') != assets or review.get('target_boxes') != boxes):
        raise ValueError('Prior control native identity or independent review mismatch')
    controls = review.get('controls', {})
    if not controls or set(controls) - {'mask', 'unrelated', 'no_image'}:
        raise ValueError('Unknown or empty fixed prior control bank')
    allowed = dict(mask={'assets', 'all_target_encodings_erased', 'review_note'},
        unrelated={'donors', 'target_evidence_absent', 'review_note'},
        no_image={'review_note'})
    variants, audit = {}, {'native_convergence_certified':False}
    for role, control in controls.items():
        if (set(control) != allowed[role] or not isinstance(control.get('review_note'), str)
                or not control['review_note'].strip()):
            raise ValueError('Unexpected prior control field or missing review note')
        changed = []
        if role == 'mask':
            if not boxes or control['all_target_encodings_erased'] is not True:
                raise ValueError('Mask requires actual target boxes and complete erasure review')
            changed = control['assets']
            if [a['slot'] for a in changed] != [a['slot'] for a in assets]:
                raise ValueError('Target mask changed image slots or order')
            changed_pixels = 0
            for original, replacement in zip(assets, changed):
                raw, masked = np.array(load_asset(original)), np.array(load_asset(replacement))
                if raw.shape != masked.shape:
                    raise ValueError('Target mask changed native image dimensions')
                mask = np.zeros(raw.shape[:2], dtype=bool)
                for box in boxes:
                    if box['slot'] != original['slot']:
                        continue
                    if box['source_size'] != original['size']:
                        raise ValueError('Target mask source size mismatch')
                    x0, y0, x1, y1 = box['pixels']
                    if (any(type(v) is not int for v in box['pixels']) or
                            not 0 <= x0 < x1 <= raw.shape[1] or
                            not 0 <= y0 < y1 <= raw.shape[0]):
                        raise ValueError('Invalid target mask rectangle')
                    mask[y0:y1, x0:x1] = True
                if not np.array_equal(raw[~mask], masked[~mask]) or not np.all(masked[mask] == 127):
                    raise ValueError('Mask must erase all target pixels to127 and preserve every outside pixel')
                changed_pixels += int(np.any(raw != masked, axis=-1).sum())
            if set(b['slot'] for b in boxes) - {a['slot'] for a in assets} or not changed_pixels:
                raise ValueError('Target mask is absent or has no changed pixels')
            audit[role] = dict(outside_target_exact=True, all_target_pixels_equal_127=True,
                changed_pixels=changed_pixels, review_note=control['review_note'])
        elif role == 'unrelated':
            if control['target_evidence_absent'] is not True:
                raise ValueError('Unrelated donor requires reviewed absence of target evidence')
            assignments = control['donors']
            if [d['slot'] for d in assignments] != [a['slot'] for a in assets]:
                raise ValueError('Unrelated donors must replace every native image slot in order')
            if families.get(entry['base_id']) != entry['analysis_family_id']:
                raise ValueError('Native family differs from the verified source-family audit')
            native_hashes = {a['decoded_sha256'] for a in assets}
            for assignment in assignments:
                base = assignment['base_id']
                if base not in donors or base not in families or families[base] == entry['analysis_family_id']:
                    raise ValueError('Unrelated donor must belong to another frozen source family')
                selected = [a for a in donors[base].get('image_assets', [])
                            if a['slot'] == assignment['donor_slot']]
                if len(selected) != 1 or selected[0]['decoded_sha256'] in native_hashes:
                    raise ValueError('Unrelated donor is missing, ambiguous or duplicates native pixels')
                load_asset(selected[0])
                changed.append(dict(selected[0], slot=assignment['slot']))
            audit[role] = dict(donors=deepcopy(assignments),
                donor_families=[families[d['base_id']] for d in assignments],
                review_note=control['review_note'])
        else:
            audit[role] = dict(no_images=True, unchanged_question=True,
                review_note=control['review_note'])
        variants['fixed_'+role] = variant_row(entry, role, changed)
    return variants, audit


def load_prior_controls(entry):
    reference = entry['source_annotation'].get('fixed_prior_control_review')
    if not reference:
        return {}, dict(status='UNAVAILABLE', reason='No frozen reviewed prior control bank')
    path = stage_path(reference['path'], 'causal_pilot/prior_controls')
    if sha(path) != reference['sha256']:
        raise ValueError('Prior control review changed')
    review = read_json(path)
    manifest_ref = entry['provenance']['manifest']
    manifest = stage_path(manifest_ref['path'], 'cohort/benchmark_manifests')
    if sha(manifest) != manifest_ref['sha256']:
        raise ValueError('Prior donor manifest changed')
    rows = read_jsonl(manifest)
    donors = {row['base_id']:row for row in rows}
    if len(donors) != len(rows):
        raise ValueError('Ambiguous donor base in native manifest')
    family_ref = entry['provenance']['source_family_audit']
    family_path = stage_path(family_ref['path'], 'audit')
    if sha(family_path) != family_ref['sha256']:
        raise ValueError('Prior donor source-family audit changed')
    families = verified_families(read_json(family_path), manifest_ref['path'],
                                manifest_ref['sha256'], entry['benchmark'])
    originals = native_assets(entry)
    for asset in review.get('controls', {}).get('mask', {}).get('assets', []):
        if asset in originals:
            continue
        if asset.get('kind') != 'file':
            raise ValueError('Derived mask must be a reviewed image file')
        stage_path(asset['path'], 'causal_pilot/prior_controls')
    variants, audits = verify_prior_controls(entry, review, donors, families)
    return variants, dict(status='REVIEWED_FIXED_PRIOR_CONTROLS_VERIFIED',
        review_path=str(path), review_sha256=sha(path),
        controls=audits, native_convergence_certified=False)


def verify_fixed_input(entry, native, variant, changed):
    if any(changed.get(k) != variant[k] for k in ('event_id', 'condition', 'no_image', 'prompt')):
        raise ValueError('Fixed control input differs from reviewed variant')
    if changed['prompt'] != entry['row']['prompt']:
        raise ValueError('Fixed prior control changed the native question')
    if variant['no_image']:
        if (changed.get('visual_token_indices') or changed.get('image_assets') or
                changed.get('image_path') or variant.get('image_assets') or variant.get('image_path')):
            raise ValueError('No-image fixed control contains an image')
    elif not changed.get('visual_token_indices') or changed.get('image_assets') != variant['image_assets']:
        raise ValueError('Fixed image control has missing or changed assets')
    elif variant['condition'] == 'mask':
        adapted = dict(changed, event_id=native['event_id'], condition=native['condition'])
        verify_local_control_geometry(entry, native, adapted)


def requested_native_banks(entries):
    """Only a source annotation frozen before scores requests fresh responses.

    A fixed-prefix control bank alone does not request three long generations.
    The annotation must state why matched native convergence is needed.
    """
    banks = {}
    for entry in entries:
        request = entry['source_annotation'].get('fresh_native_prior_control_request')
        if request is None:
            continue
        if (request.get('required') is not True or
                request.get('causal_or_passive_scores_used') is not False or
                not isinstance(request.get('reason'), str) or not request['reason'].strip()):
            raise ValueError('Fresh native controls need an explicit pre-score source-annotation request')
        variants, provenance = load_prior_controls(entry)
        if set(variants) != {'fixed_mask', 'fixed_unrelated', 'fixed_no_image'}:
            raise ValueError('Requested fresh native controls lack a complete reviewed image bank')
        banks[entry['id']] = (variants, provenance)
    return banks


@torch.inference_mode()
def score_prior_controls(model, processor, entry, native_meta, device):
    if (entry.get('causal_pilot_frozen') is not True or
            entry.get('selection_used_causal_or_passive_scores') is not False):
        raise ValueError('Prior scoring requires a pilot frozen without causal/passive selection')
    variants, provenance = load_prior_controls(entry)
    controls, distributions, audits = {}, {}, {}
    for name, variant in variants.items():
        prepared, root = None, None
        try:
            prepared, meta = prepare_condition(processor, variant, device)
            verify_fixed_input(entry, native_meta, variant, meta)
            root, replay = make_benchmark_root(model, prepared, variant, entry['event'])
            prepared = None
            score, distribution = score_bundle(model, root, entry['event'], entry['source_groups'])
            if score.get('finite') is not True:
                raise ValueError('Nonfinite fixed prior score: ' + name)
            controls[name], distributions[name] = score, distribution
            audits[name] = dict(input=meta, replay=replay,
                scope='Same frozen native reasoning prefix; no fresh response generated')
        finally:
            prepared, root = None, None
            gc.collect()
            if torch.device(device).type == 'cuda':
                torch.cuda.empty_cache()
    return dict(controls=controls, distributions=distributions, control_audits=audits,
        provenance=provenance, native_convergence_certified=False,
        checks=dict(fixed_prior_inputs_verified=True, fixed_prior_scores_finite=True),
        passive_features_collected=False)
