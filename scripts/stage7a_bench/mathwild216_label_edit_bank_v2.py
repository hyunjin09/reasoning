"""Prepare CA/CB label swaps and matched shams from original photo glyphs.

Only the two already reviewed literal rectangles can change. Each recipient
uses its original ink bounds/background; the donor mask is resized into those
bounds. No model scores or new fonts enter rendering. Full-image semantic and
sham review is required after the mechanical locality checks.
"""
import numpy as np
from PIL import Image

from scripts.stage7a.common import ROOT, read_json, read_jsonl, sha, write_json
from scripts.stage7a_bench.image_inputs_v2 import load_asset
from scripts.stage7a_bench.local_edit_validation_v2 import validate_local_variant

OUT = ROOT / 'outputs/stage7a_bench_v2'


def extract_original(patch):
    gray = patch.astype(float).mean(axis=2)
    background = np.median(patch[gray >= np.percentile(gray, 90)], axis=0)
    alpha = np.clip(1 - gray / background.mean(), 0, 1)
    alpha[alpha < .05] = 0
    yy, xx = np.nonzero(alpha > .18)
    if not len(xx):
        raise ValueError('Original printed label has no identifiable ink')
    bounds = [int(xx.min()), int(yy.min()), int(xx.max())+1, int(yy.max())+1]
    x0, y0, x1, y1 = bounds
    return alpha[y0:y1, x0:x1], dict(
        background_rgb=background.tolist(), ink_bounds=bounds,
        fit_uses_original_pixels_only=True,
        operation='Extract original ink, resize to original recipient ink bounds, repaint recipient background')


def main():
    ap = OUT / 'causal_pilot/source_reviews/mathvision_wild__216__photo__e01_v1.json'
    annotation = read_json(ap)
    row = read_jsonl(OUT / 'cohort/benchmark_manifests/mathvision_wild_photo_native.jsonl')[20]
    assert row['event_id'] == annotation['event_id']
    assert annotation['candidates'] == dict(correct='CA', foil='CB', target_semantic='CB',
        alternative_original='CB', alternative_semantic='CA')
    asset = row['source_asset_identity'][0]
    with load_asset(asset) as im:
        native = np.array(im)
    assert native.shape == (1640, 3648, 3)
    extracted = {}
    for role in ('T', 'X'):
        x0, y0, x1, y1 = annotation['sources'][role][0]['pixels']
        extracted[role] = extract_original(native[y0:y1, x0:x1])
    dest = OUT / 'causal_pilot/edit_bank/mathwild216_literal_swap_v1'
    if dest.exists():
        raise FileExistsError('Preserve existing source-control bank')
    pending, controls = {}, {}
    literals = dict(T='CA', X='CB')
    for role, other in [('T', 'X'), ('X', 'T')]:
        box = annotation['sources'][role][0]['pixels']
        x0, y0, x1, y1 = box
        fit = extracted[role][1]
        a, b, c, d = fit['ink_bounds']
        for kind, donor in [('semantic', other), ('sham', role)]:
            name = role + '_' + kind
            mask = Image.fromarray(extracted[donor][0].astype(np.float32))
            resized = np.clip(np.array(mask.resize((c-a, d-b), Image.Resampling.BICUBIC)), 0, 1)
            alpha = np.zeros((y1-y0, x1-x0), dtype=float)
            alpha[b:d, a:c] = resized
            patch = np.rint(np.array(fit['background_rgb']) * (1-alpha[..., None])).astype(np.uint8)
            variant = native.copy()
            variant[y0:y1, x0:x1] = patch
            pending[name] = variant
            controls[name] = dict(source=role, original=literals[role], value=literals[donor],
                recipient=box, donor_source=donor, renderer_fit=fit,
                **validate_local_variant(native, variant, [box]), independently_reviewed=False)
    dest.mkdir(parents=True)
    for name, variant in pending.items():
        path = dest / (name + '.png')
        Image.fromarray(variant).save(path)
        with Image.open(path) as saved:
            assert np.array_equal(np.array(saved.convert('RGB')), variant)
        controls[name].update(path=str(path.relative_to(ROOT)), sha256=sha(path))
    dependencies = [ROOT / 'scripts/stage7a_bench/mathwild216_label_edit_bank_v2.py',
                    ROOT / 'scripts/stage7a_bench/local_edit_validation_v2.py']
    write_json(dest / 'candidate_manifest.json', dict(status='PIXEL_VALID_SEMANTICS_PENDING',
        event_id=row['event_id'], source_annotation_path=str(ap.relative_to(ROOT)),
        source_annotation_sha256=sha(ap), source_asset=asset, controls=controls,
        source_value_policy=None,
        dependency_sha256={str(p.relative_to(ROOT)): sha(p) for p in dependencies},
        unavailable_controls={}, causal_scores_used=False, pilot_selected=False,
        semantic_review_pending=True), freeze=True)
    print('FOUR_LITERAL_CONTROLS_PREPARED', 'MANUAL_REVIEW_PENDING')


if __name__ == '__main__':
    main()
