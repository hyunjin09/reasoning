"""Prepare four matched raster-glyph controls for the wrong G-to-S read.

The same black-ink opacity extraction and recipient-background rendering is
used for semantic and sham variants. This is a scientific pixel intervention,
not a new source image or a causal certificate; all variants need direct review.
"""
import numpy as np
from PIL import Image

from scripts.stage7a.common import ROOT, read_json, read_jsonl, sha, write_json
from scripts.stage7a_bench.image_inputs_v2 import load_asset
from scripts.stage7a_bench.local_edit_validation_v2 import validate_local_variant
from scripts.stage7a_bench.source_value_policy_v2 import numeric_replacement

OUT = ROOT / 'outputs/stage7a_bench_v2'


def background(patch):
    border = np.concatenate((patch[0], patch[-1], patch[1:-1, 0], patch[1:-1, -1]))
    return np.median(border, axis=0)


def transplant_black_glyph(native, donor, recipient):
    x0, y0, x1, y1 = donor
    u0, v0, u1, v1 = recipient
    if (x1-x0, y1-y0) != (u1-u0, v1-v0):
        raise ValueError('Semantic and sham glyph patches must preserve native dimensions')
    source = native[y0:y1, x0:x1].astype(np.float64)
    target = native[v0:v1, u0:u1].astype(np.float64)
    source_bg, target_bg = background(source), background(target)
    if np.any(source_bg <= 0) or not np.any(np.max(source, axis=-1) < 90):
        raise ValueError('Expected dark glyph on a nonblack flat cell background')
    opacity = np.clip(1 - np.median(source / source_bg, axis=-1), 0, 1)
    rendered = np.rint(target_bg * (1 - opacity[..., None])).astype(np.uint8)
    variant = native.copy()
    variant[v0:v1, u0:u1] = rendered
    return variant, dict(source_background_rgb=source_bg.tolist(),
        recipient_background_rgb=target_bg.tolist(),
        rendering='Median-channel black-ink opacity on median recipient-border RGB; '
                  'identical transform for semantic and sham; no rescaling or font replacement')


def main():
    annotation_path = OUT / 'causal_pilot/source_reviews/charxiv__images%2F568.jpg__image_present__e00_v1.json'
    annotation = read_json(annotation_path)
    policy_path = ROOT / annotation['source_value_policy']['path']
    policy = read_json(policy_path)
    assert sha(policy_path) == annotation['source_value_policy']['sha256']
    assert sha(ROOT / policy['implementation_path']) == policy['implementation_sha256']
    rows = read_jsonl(OUT / 'cohort/benchmark_manifests/charxiv_image_present_native.jsonl')
    row = next(r for r in rows if r['event_id'] == annotation['event_id'])
    native = np.array(load_asset(row['image_assets'][0]))
    assert native.shape == (1024, 1024, 3)
    specs = {
        'T_semantic':dict(source='T', original='0.198', value='0.193',
            donor=[377, 71, 389, 89], recipient=[489, 71, 501, 89],
            donor_identity='Last3 of fromY/toS0.3673'),
        'T_sham':dict(source='T', original='0.198', value='0.198',
            donor=[260, 71, 272, 89], recipient=[489, 71, 501, 89],
            donor_identity='Last8 of fromV/toS0.3638'),
        'X_semantic':dict(source='X', original='0.4595', value='0.4590',
            donor=[450, 71, 462, 89], recipient=[611, 71, 623, 89],
            donor_identity='Leading0 of fromG/toS0.198'),
        'X_sham':dict(source='X', original='0.4595', value='0.4595',
            donor=[940, 71, 952, 89], recipient=[611, 71, 623, 89],
            donor_identity='Middle5 of fromO/toS0.4573'),
    }
    dest = OUT / 'causal_pilot/edit_bank/charxiv568_numeric_v1'
    if dest.exists():
        raise FileExistsError('Control bank exists; preserve it')
    controls = {}
    for name, spec in specs.items():
        if name.endswith('semantic'):
            assert numeric_replacement(spec['original'], lower=None, upper=None) == spec['value']
        variant, rendering = transplant_black_glyph(native, spec['donor'], spec['recipient'])
        locality = validate_local_variant(native, variant, [spec['recipient']])
        dest.mkdir(parents=True, exist_ok=True)
        path = dest / (name + '.png')
        Image.fromarray(variant).save(path)
        with Image.open(path) as saved:
            assert np.array_equal(np.array(saved.convert('RGB')), variant)
        controls[name] = dict(**spec, path=str(path.relative_to(ROOT)), sha256=sha(path),
            **locality, rendering=rendering, independently_reviewed=False)
    write_json(dest / 'candidate_manifest.json', dict(status='PIXEL_VALID_SEMANTICS_PENDING',
        event_id=row['event_id'], source_annotation_path=str(annotation_path.relative_to(ROOT)),
        source_annotation_sha256=sha(annotation_path), source_asset=row['image_assets'][0],
        source_value_policy=annotation['source_value_policy'], controls=controls,
        dependency_sha256={str(p.relative_to(ROOT)):sha(p) for p in
            (ROOT / 'scripts/stage7a_bench/charxiv568_edit_bank_v2.py',
             ROOT / 'scripts/stage7a_bench/local_edit_validation_v2.py')},
        causal_scores_used=False, pilot_selected=False, semantic_review_pending=True), freeze=True)
    print('CANDIDATE_EDITS_PREPARED', len(controls), 'MANUAL_REVIEW_PENDING')


if __name__ == '__main__':
    main()
