"""Prepare option E30->35 and sham30 from the original photographed digits.

Changing the given angle would remove the correct answer from the unchanged
options. Only the independent wrong option receives a local control pair.
"""
import numpy as np
from PIL import Image

from scripts.stage7a.common import ROOT, read_json, read_jsonl, sha, write_json
from scripts.stage7a_bench.image_inputs_v2 import load_asset
from scripts.stage7a_bench.local_edit_validation_v2 import validate_local_variant
from scripts.stage7a_bench.mathwild216_label_edit_bank_v2 import extract_original
from scripts.stage7a_bench.source_value_policy_v2 import numeric_replacement

OUT = ROOT / 'outputs/stage7a_bench_v2'
RECIPIENT = [2390, 1128, 2435, 1209]
DONORS = {'0': RECIPIENT, '5': [974, 1151, 1027, 1224]}


def main():
    ap = OUT / 'causal_pilot/source_reviews/mathvision_wild__1512__photo__e03_v1.json'
    annotation = read_json(ap)
    assert numeric_replacement('30', lower='0', upper='180') == '35'
    assert annotation['candidates'] == dict(correct='30', foil='35',
        target_semantic='35', alternative_original='30', alternative_semantic='35')
    policy = annotation['source_value_policy']
    assert sha(ROOT / policy['path']) == policy['sha256']
    row = read_jsonl(OUT / 'cohort/benchmark_manifests/mathvision_wild_photo_native.jsonl')[29]
    assert row['event_id'] == annotation['event_id']
    asset = row['source_asset_identity'][0]
    with load_asset(asset) as image:
        native = np.array(image)
    assert native.shape == (1959, 4032, 3)
    x0, y0, x1, y1 = RECIPIENT
    _, fit = extract_original(native[y0:y1, x0:x1])
    a, b, c, d = fit['ink_bounds']
    dest = OUT / 'causal_pilot/edit_bank/mathwild1512_alternative_angle_v1'
    if dest.exists():
        raise FileExistsError('Preserve existing source-control bank')
    pending, controls = {}, {}
    for kind, digit, value in [('semantic', '5', '35'), ('sham', '0', '30')]:
        dx0, dy0, dx1, dy1 = DONORS[digit]
        donor, donor_fit = extract_original(native[dy0:dy1, dx0:dx1])
        resized = np.clip(np.array(Image.fromarray(donor.astype(np.float32)).resize(
            (c-a, d-b), Image.Resampling.BICUBIC)), 0, 1)
        alpha = np.zeros((y1-y0, x1-x0), dtype=float)
        alpha[b:d, a:c] = resized
        variant = native.copy()
        variant[y0:y1, x0:x1] = np.rint(
            np.array(fit['background_rgb']) * (1-alpha[..., None])).astype(np.uint8)
        name = 'X_' + kind
        pending[name] = variant
        controls[name] = dict(source='X', original='30', value=value,
            recipient=RECIPIENT, renderer_fit=dict(recipient_fit=fit,
                donor_box=DONORS[digit], donor_fit=donor_fit,
                original_pixels_only=True,
                qualification='Flattened moire and fitted digit need direct review'),
            **validate_local_variant(native, variant, [RECIPIENT]), independently_reviewed=False)
    dest.mkdir(parents=True)
    for name, variant in pending.items():
        path = dest / (name + '.png')
        Image.fromarray(variant).save(path)
        with Image.open(path) as saved:
            assert np.array_equal(np.array(saved.convert('RGB')), variant)
        controls[name].update(path=str(path.relative_to(ROOT)), sha256=sha(path))
    dependencies = [ROOT / 'scripts/stage7a_bench' / name for name in
        ['mathwild1512_edit_bank_v2.py', 'mathwild216_label_edit_bank_v2.py',
         'local_edit_validation_v2.py', 'source_value_policy_v2.py']]
    write_json(dest / 'candidate_manifest.json', dict(status='PIXEL_VALID_SEMANTICS_PENDING',
        event_id=row['event_id'], source_annotation_path=str(ap.relative_to(ROOT)),
        source_annotation_sha256=sha(ap), source_asset=asset, controls=controls,
        source_value_policy=policy,
        dependency_sha256={str(p.relative_to(ROOT)): sha(p) for p in dependencies},
        unavailable_controls={'T': 'Given35 yields17.5, absent from unchanged options'},
        causal_scores_used=False, pilot_selected=False, semantic_review_pending=True), freeze=True)
    print('ALTERNATIVE_ANGLE_PAIR_PREPARED_MANUAL_REVIEW_PENDING')


if __name__ == '__main__':
    main()
