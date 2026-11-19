"""Prepare an X-only original-outline swap; complete-image review is mandatory."""
import numpy as np
from PIL import Image

from scripts.stage7a.common import ROOT, read_json, read_jsonl, sha, write_json
from scripts.stage7a_bench.image_inputs_v2 import load_asset
from scripts.stage7a_bench.local_edit_validation_v2 import validate_local_variant
from scripts.stage7a_bench.mathwild216_label_edit_bank_v2 import extract_original

OUT = ROOT / 'outputs/stage7a_bench_v2'


def main():
    ap = OUT / 'causal_pilot/source_reviews/mathvision_wild__105__photo__e03_v1.json'
    annotation = read_json(ap)
    row = read_jsonl(OUT / 'cohort/benchmark_manifests/mathvision_wild_photo_native.jsonl')[197]
    assert row['event_id'] == annotation['event_id']
    assert annotation['candidates'] == dict(correct='triangle', foil='square',
        target_semantic='square', alternative_original='square', alternative_semantic='triangle')
    asset = row['source_asset_identity'][0]
    with load_asset(asset) as im:
        native = np.array(im)
    assert native.shape == (362, 988, 3)
    extracted = {}
    for role in ('T', 'X'):
        x0, y0, x1, y1 = annotation['sources'][role][0]['pixels']
        # A separate donor crop excludes photographed frame ink; causal ROI is unchanged.
        if role == 'T':
            x0, y0, x1, y1 = (649, 239, 696, 276)
        extracted[role] = extract_original(native[y0:y1, x0:x1])
    dest = OUT / 'causal_pilot/edit_bank/mathwild105_alternative_shape_v2'
    if dest.exists():
        raise FileExistsError('Preserve existing source-control bank')
    box = annotation['sources']['X'][0]['pixels']
    x0, y0, x1, y1 = box
    fit = extracted['X'][1]
    a, b, c, d = fit['ink_bounds']
    pending, controls = {}, {}
    for kind, donor, value in [('semantic', 'T', 'triangle'), ('sham', 'X', 'square')]:
        name = 'X_' + kind
        mask = Image.fromarray(extracted[donor][0].astype(np.float32))
        resized = np.clip(np.array(mask.resize((c-a, d-b), Image.Resampling.BICUBIC)), 0, 1)
        alpha = np.zeros((y1-y0, x1-x0), dtype=float)
        alpha[b:d, a:c] = resized
        patch = np.rint(np.array(fit['background_rgb']) * (1-alpha[..., None])).astype(np.uint8)
        variant = native.copy()
        variant[y0:y1, x0:x1] = patch
        pending[name] = variant
        controls[name] = dict(source='X', original='square', value=value,
            recipient=box, donor_source=donor,
            donor_crop=[649, 239, 696, 276] if donor == 'T' else box, renderer_fit=fit,
            **validate_local_variant(native, variant, [box]), independently_reviewed=False)
    dest.mkdir(parents=True)
    for name, variant in pending.items():
        path = dest / (name + '.png')
        Image.fromarray(variant).save(path)
        with Image.open(path) as saved:
            assert np.array_equal(np.array(saved.convert('RGB')), variant)
        controls[name].update(path=str(path.relative_to(ROOT)), sha256=sha(path))
    dependencies = [ROOT / 'scripts/stage7a_bench/mathwild105_shape_edit_bank_v3.py',
        ROOT / 'scripts/stage7a_bench/mathwild216_label_edit_bank_v2.py',
        ROOT / 'scripts/stage7a_bench/local_edit_validation_v2.py']
    write_json(dest / 'candidate_manifest.json', dict(status='PIXEL_VALID_SEMANTICS_PENDING',
        event_id=row['event_id'], source_annotation_path=str(ap.relative_to(ROOT)),
        source_annotation_sha256=sha(ap), source_asset=asset, controls=controls,
        source_value_policy=None,
        dependency_sha256={str(p.relative_to(ROOT)): sha(p) for p in dependencies},
        unavailable_controls=dict(T='Triangle to square would remove the only valid answer D.'),
        causal_scores_used=False, pilot_selected=False, semantic_review_pending=True), freeze=True)
    print('TWO_X_CONTROLS_PREPARED', 'MANUAL_REVIEW_PENDING')


if __name__ == '__main__':
    main()
