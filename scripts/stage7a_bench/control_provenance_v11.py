"""Bind reviewed local image controls to a native causal candidate.

Missing semantic/sham pairs remain absent. This module does not choose events,
relax source definitions, or infer that an edited image has a causal effect.
"""
from copy import deepcopy

import numpy as np

from scripts.stage7a.common import ROOT, read_json, sha
from scripts.stage7a_bench.causal_provenance_v2 import stage_path
from scripts.stage7a_bench.image_inputs_v2 import describe, load_asset
from scripts.stage7a_bench.local_edit_validation_v2 import validate_local_variant
from scripts.stage7a_bench.document_controls_v11 import checked_source_page, override_row


def verify_control_records(entry, manifest, review):
    annotation = entry['source_annotation']
    if (manifest.get('event_id') != entry['event_id'] or review.get('event_id') != entry['event_id'] or
            review.get('status') != 'MANUALLY_REVIEWED_LOCAL_CONTROLS' or
            manifest.get('causal_scores_used') is not False or
            review.get('causal_or_passive_scores_used') is not False or
            review.get('threshold_changed') is not False):
        raise ValueError('Control identity or pre-causal review mismatch')
    row = entry['row']
    native_assets = row.get('image_assets', [])
    if row.get('document_path'):
        native_assets = [checked_source_page(entry, manifest['source_asset'])]
    if row.get('image_path') and native_assets:
        raise ValueError('Local controls require an unambiguous file or explicit image-asset input')
    if row.get('image_path'):
        native = entry['native_input']
        native_assets = [dict(kind='file', path=row['image_path'], slot='image_1',
            bytes_sha256=row['image_sha256'], decoded_sha256=native['decoded_image_sha256'],
            size=native['image_size'])]
    if (manifest.get('source_asset') not in native_assets or
            manifest.get('source_value_policy') != annotation.get('source_value_policy')):
        raise ValueError('Control source image or value policy differs from native candidate')
    redundancy = review.get('redundant_encoding_review', {})
    if not redundancy.get('status') or not redundancy.get('note'):
        raise ValueError('Explicit redundant-encoding review is required')
    controls, judgments = manifest['controls'], review['controls']
    if not controls or set(controls) != set(judgments):
        raise ValueError('Each supplied control requires a corresponding independent review')
    allowed = {s+'_'+kind for s in ('T', 'X') for kind in ('semantic', 'sham')}
    if not set(controls) <= allowed:
        raise ValueError('Unknown source-control role')
    values = annotation['candidates']
    for source in ('T', 'X'):
        names = {source+'_semantic', source+'_sham'}
        if not names & set(controls):
            continue
        if not names <= set(controls) or not entry['source_groups'].get(source):
            raise ValueError('Semantic controls require a matched sham and actual source')
        original = values['correct' if source == 'T' else 'alternative_original']
        changed = values['target_semantic' if source == 'T' else 'alternative_semantic']
        for name in names:
            control, judgment = controls[name], judgments[name]
            expected = changed if name.endswith('semantic') else original
            if (control['source'] != source or control['original'] != original or control['value'] != expected or
                    any(judgment.get(k) != control[k] for k in ('source', 'path', 'sha256', 'recipient')) or
                    judgment.get('original_literal') != original or judgment.get('reviewed_literal') != expected or
                    any(judgment.get(k) is not True for k in ('literal_correct', 'source_identity_preserved',
                        'other_source_unchanged', 'semantics_valid', 'sham_rendering_matched'))):
                raise ValueError('Control literal, orientation, mask or semantic review mismatch')


def load_reviewed_controls(entry):
    reference = entry['source_annotation'].get('control_review')
    if not reference:
        return {}, dict(status='UNAVAILABLE', reason='No frozen source-control review')
    review_path = stage_path(reference['path'], 'causal_pilot/edit_bank')
    if sha(review_path) != reference['sha256']:
        raise ValueError('Source-control review changed')
    review = read_json(review_path)
    manifest_path = stage_path(review['candidate_manifest']['path'], 'causal_pilot/edit_bank')
    if sha(manifest_path) != review['candidate_manifest']['sha256']:
        raise ValueError('Candidate edit manifest changed')
    manifest = read_json(manifest_path)
    verify_control_records(entry, manifest, review)
    native_asset = manifest['source_asset']
    native = np.array(load_asset(native_asset))
    variants, audits = {}, {}
    for name, control in manifest['controls'].items():
        path = stage_path(control['path'], 'causal_pilot/edit_bank')
        if sha(path) != control['sha256']:
            raise ValueError('Reviewed control image changed')
        asset = describe(dict(kind='file', path=str(path), slot=native_asset['slot']), path.read_bytes())
        variant = np.array(load_asset(asset))
        locality = validate_local_variant(native, variant, [control['recipient']])
        for field in ('changed_pixels', 'outside_mask_changed_pixels', 'native_size',
                      'native_decoded_sha256', 'variant_decoded_sha256'):
            if locality[field] != control[field]:
                raise ValueError('Control pixel audit changed: ' + field)
        x0, y0, x1, y1 = control['recipient']
        boxes = entry['source_annotation']['sources'][control['source']]
        if not any(b['slot'] == native_asset['slot'] and b['source_size'] == locality['native_size'] and
                   b['pixels'][0] <= x0 < x1 <= b['pixels'][2] and
                   b['pixels'][1] <= y0 < y1 <= b['pixels'][3] for b in boxes):
            raise ValueError('Edited pixels lie outside the annotated source footprint')
        row = deepcopy(entry['row'])
        if row.get('document_path'):
            row = override_row(entry, native_asset, asset)
        elif row.get('image_path'):
            row.update(image_path=str(path), image_sha256=sha(path))
        else:
            row['image_assets'] = [asset if a == native_asset else a for a in row['image_assets']]
        variants[name] = row
        audits[name] = dict(path=str(path.relative_to(ROOT)), sha256=sha(path),
            source=control['source'], literal=control['value'], pixel_locality=locality,
            manual_review=deepcopy(review['controls'][name]))
    return variants, dict(status='REVIEWED_LOCAL_CONTROLS_VERIFIED',
        review_path=str(review_path.relative_to(ROOT)), review_sha256=sha(review_path),
        candidate_manifest_sha256=sha(manifest_path), controls=audits,
        redundant_encoding_review=review['redundant_encoding_review'],
        causal_validity=None, pilot_admitted=False)
