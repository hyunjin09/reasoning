"""Prepare the task-consistent9->4 paint-budget edit and matched9 sham.

Both glyph masks come from the original photo's printed answer choices and
use the same manually reviewed recipient ink bounds. The strong glare removed
inside the target rectangle must be qualified in independent sham review.
"""
import numpy as np
from PIL import Image

from scripts.stage7a.common import ROOT, read_json, read_jsonl, sha, write_json
from scripts.stage7a_bench.image_inputs_v2 import load_asset
from scripts.stage7a_bench.local_edit_validation_v2 import validate_local_variant
from scripts.stage7a_bench.mathwild216_label_edit_bank_v2 import extract_original
from scripts.stage7a_bench.source_value_policy_v2 import numeric_replacement

OUT = ROOT / 'outputs/stage7a_bench_v2'
DONORS = {'9': [744, 1011, 808, 1109], '4': [2780, 1010, 2850, 1110]}
INK_BOUNDS = [946, 155, 990, 218]


def main():
    ap = OUT / 'causal_pilot/source_reviews/mathvision_wild__1727__photo__e00_v1.json'
    annotation = read_json(ap)
    assert numeric_replacement('9', lower='0', upper=None) == '4'
    assert annotation['candidates']['target_semantic'] == '4'
    policy = annotation['source_value_policy']
    assert sha(ROOT / policy['path']) == policy['sha256']
    row = read_jsonl(OUT / 'cohort/benchmark_manifests/mathvision_wild_photo_native.jsonl')[14]
    assert row['event_id'] == annotation['event_id']
    asset = row['source_asset_identity'][0]
    with load_asset(asset) as image:
        native = np.array(image)
    assert native.shape == (1325, 4032, 3)
    box = annotation['sources']['T'][0]['pixels']
    x0, y0, x1, y1 = box
    a, b, c, d = INK_BOUNDS
    assert x0 <= a < c <= x1 and y0 <= b < d <= y1
    background = np.median(native[y0:y1, x1-3:x1].reshape(-1, 3), axis=0)
    dest = OUT / 'causal_pilot/edit_bank/mathwild1727_target_budget_v1'
    if dest.exists():
        raise FileExistsError('Preserve existing source-control bank')
    pending, controls = {}, {}
    for kind, value in [('semantic', '4'), ('sham', '9')]:
        dx0, dy0, dx1, dy1 = DONORS[value]
        donor, donor_fit = extract_original(native[dy0:dy1, dx0:dx1])
        resized = np.clip(np.array(Image.fromarray(donor.astype(np.float32)).resize(
            (c-a, d-b), Image.Resampling.BICUBIC)), 0, 1)
        alpha = np.zeros((y1-y0, x1-x0), dtype=float)
        alpha[b-y0:d-y0, a-x0:c-x0] = resized
        patch = np.rint(background * (1-alpha[..., None])).astype(np.uint8)
        variant = native.copy()
        variant[y0:y1, x0:x1] = patch
        name = 'T_' + kind
        pending[name] = variant
        controls[name] = dict(source='T', original='9', value=value, recipient=box,
            renderer_fit=dict(background_rgb=background.tolist(),
                ink_bounds_native=INK_BOUNDS, donor_box=DONORS[value], donor_fit=donor_fit,
                fit_uses_original_pixels_only=True, native_glare_inside_mask_repainted=True),
            **validate_local_variant(native, variant, [box]), independently_reviewed=False)
    dest.mkdir(parents=True)
    for name, variant in pending.items():
        path = dest / (name + '.png')
        Image.fromarray(variant).save(path)
        with Image.open(path) as saved:
            assert np.array_equal(np.array(saved.convert('RGB')), variant)
        controls[name].update(path=str(path.relative_to(ROOT)), sha256=sha(path))
    dependencies = [ROOT / 'scripts/stage7a_bench' / name for name in
        ['mathwild1727_edit_bank_v2.py', 'mathwild216_label_edit_bank_v2.py',
         'local_edit_validation_v2.py', 'source_value_policy_v2.py']]
    write_json(dest / 'candidate_manifest.json', dict(status='PIXEL_VALID_SEMANTICS_PENDING',
        event_id=row['event_id'], source_annotation_path=str(ap.relative_to(ROOT)),
        source_annotation_sha256=sha(ap), source_asset=asset, controls=controls,
        source_value_policy=policy,
        dependency_sha256={str(p.relative_to(ROOT)): sha(p) for p in dependencies},
        unavailable_controls=dict(X='Changing optionA9->4 alone removes the correct9 choice and duplicatesD4'),
        causal_scores_used=False, pilot_selected=False, semantic_review_pending=True), freeze=True)
    print('TARGET_PAINT_BUDGET_PAIR_PREPARED', 'GLARE_AND_SEMANTIC_REVIEW_PENDING')


if __name__ == '__main__':
    main()
