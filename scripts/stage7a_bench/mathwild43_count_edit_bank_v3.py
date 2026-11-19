"""Prepare a single-dot removal/addition and matched shams before scoring.

V1 rectangular target edits were rejected for touching adjacent ink.
Use an elliptical target mask and the original target dot as the ink template. The alternative insertion
site was checked in the original wing interior; no other dot or outline may
change. Pixel checks leave exact counts and native-demand eligibility to review.
"""
import numpy as np
from PIL import Image

from scripts.stage7a.common import ROOT, read_json, read_jsonl, sha, write_json
from scripts.stage7a_bench.image_inputs_v2 import load_asset
from scripts.stage7a_bench.local_edit_validation_v2 import validate_local_variant

OUT = ROOT / 'outputs/stage7a_bench_v2'
BOXES = dict(T=[1576, 582, 1600, 607], X=[1401, 573, 1422, 594])


def main():
    ap = OUT / 'causal_pilot/source_reviews/mathvision_wild__43__photo__e01_v1.json'
    annotation = read_json(ap)
    rule = annotation['count_candidate_rule']
    assert sha(ROOT / rule['path']) == rule['sha256']
    row = read_jsonl(OUT / 'cohort/benchmark_manifests/mathvision_wild_photo_native.jsonl')[19]
    assert row['event_id'] == annotation['event_id']
    assert annotation['candidates'] == dict(correct='6', foil='5', target_semantic='5',
        alternative_original='5', alternative_semantic='6')
    asset = row['source_asset_identity'][0]
    with load_asset(asset) as im:
        native = np.array(im)
    assert native.shape == (1080, 1920, 3)
    patches, fits = {}, {}
    for role, (x0, y0, x1, y1) in BOXES.items():
        patch = native[y0:y1, x0:x1]
        gray = patch.astype(float).mean(axis=2)
        background = np.median(patch[gray >= np.percentile(gray, 80)], axis=0)
        patches[role] = patch
        fits[role] = dict(background_rgb=background.tolist(),
            fit_uses_original_pixels_only=True)
    template = np.clip(1-patches['T'].mean(axis=2)/np.mean(fits['T']['background_rgb']), 0, 1)
    template[template < .05] = 0
    resized = np.clip(np.array(Image.fromarray(template.astype(np.float32)).resize(
        (21, 21), Image.Resampling.BICUBIC)), 0, 1)
    yy, xx = np.ogrid[-10:11, -10:11]
    insertion = xx*xx + yy*yy <= 100
    if patches['X'].mean(axis=2)[insertion].min() < 130:
        raise ValueError('Insertion disk contains existing ink or an outline')
    fits['X'].update(insertion_center_native=[1411, 583], insertion_radius=10,
        original_disk_min_gray=float(patches['X'].mean(axis=2)[insertion].min()),
        original_site_review='Clear upper-right wing interior, between existing dots and outline')
    dest = OUT / 'causal_pilot/edit_bank/mathwild43_count_swap_v2'
    if dest.exists():
        raise FileExistsError('Preserve existing source-control bank')
    target_y, target_x = np.ogrid[582:607, 1576:1600]
    target_mask = ((target_x-1587)/11)**2 + ((target_y-594)/12)**2 <= 1
    fits['T'].update(removal_mask='ellipse', center_native=[1587, 594], radii=[11, 12],
        protected_other_ink_pixels=[[1576, 606], [1599, 606]])
    pending, controls = {}, {}
    for role in ('T', 'X'):
        x0, y0, x1, y1 = BOXES[role]
        for kind in ('semantic', 'sham'):
            name = role + '_' + kind
            if role == 'T':
                alpha = template if kind == 'sham' else np.zeros_like(template)
                painted = np.rint(np.array(fits[role]['background_rgb']) *
                    (1-alpha[..., None])).astype(np.uint8)
                patch = patches[role].copy()
                patch[target_mask] = painted[target_mask]
                assert np.array_equal(patch[~target_mask], patches[role][~target_mask])
                original, value = '6', ('5' if kind == 'semantic' else '6')
            else:
                alpha = resized if kind == 'semantic' else np.zeros_like(resized)
                painted = np.rint(np.array(fits[role]['background_rgb']) *
                    (1-alpha[..., None])).astype(np.uint8)
                patch = patches[role].copy()
                patch[insertion] = painted[insertion]
                assert np.array_equal(patch[~insertion], patches[role][~insertion])
                original, value = '5', ('6' if kind == 'semantic' else '5')
            variant = native.copy()
            variant[y0:y1, x0:x1] = patch
            assert np.array_equal(variant[606, 1576], native[606, 1576])
            assert np.array_equal(variant[606, 1599], native[606, 1599])
            pending[name] = variant
            controls[name] = dict(source=role, original=original, value=value,
                recipient=BOXES[role], renderer_fit=fits[role],
                **validate_local_variant(native, variant, [BOXES[role]]),
                independently_reviewed=False)
    dest.mkdir(parents=True)
    for name, variant in pending.items():
        path = dest / (name + '.png')
        Image.fromarray(variant).save(path)
        with Image.open(path) as saved:
            assert np.array_equal(np.array(saved.convert('RGB')), variant)
        controls[name].update(path=str(path.relative_to(ROOT)), sha256=sha(path))
    dependencies = [ROOT / 'scripts/stage7a_bench/mathwild43_count_edit_bank_v3.py',
                    ROOT / 'scripts/stage7a_bench/local_edit_validation_v2.py']
    write_json(dest / 'candidate_manifest.json', dict(status='PIXEL_VALID_SEMANTICS_PENDING',
        event_id=row['event_id'], source_annotation_path=str(ap.relative_to(ROOT)),
        source_annotation_sha256=sha(ap), source_asset=asset, controls=controls,
        source_value_policy=None, count_candidate_rule=rule,
        dependency_sha256={str(p.relative_to(ROOT)): sha(p) for p in dependencies},
        unavailable_controls={}, causal_scores_used=False, pilot_selected=False,
        semantic_review_pending=True), freeze=True)
    print('FOUR_COUNT_CONTROLS_PREPARED', 'MANUAL_REVIEW_PENDING')


if __name__ == '__main__':
    main()
