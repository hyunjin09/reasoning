"""Prepare the reviewed first-net A→F contrast and its matched local sham.

The target F remains unchanged. Its original ink supplies the upright F donor;
the alternative recipient uses its original ink bounds and paper background.
The source-only rotation audit establishes task consistency separately from
pixel locality. Edited images still require direct semantic review.
"""
import numpy as np
from PIL import Image

from scripts.stage7a.common import ROOT, read_json, read_jsonl, sha, write_json
from scripts.stage7a_bench.image_inputs_v2 import load_asset
from scripts.stage7a_bench.local_edit_validation_v2 import validate_local_variant
from scripts.stage7a_bench.mathwild216_label_edit_bank_v2 import extract_original

OUT = ROOT / 'outputs/stage7a_bench_v2'


def main():
    annotation_path = OUT / 'causal_pilot/source_reviews/mathvision_wild__742__photo__e02_v1.json'
    annotation = read_json(annotation_path)
    row = read_jsonl(OUT / 'cohort/benchmark_manifests/mathvision_wild_photo_native.jsonl')[56]
    assert row['event_id'] == annotation['event_id']
    assert annotation['candidates'] == dict(correct='F', foil='A', target_semantic='A',
        alternative_original='A', alternative_semantic='F')
    reference = annotation['source_constraint_review']
    assert sha(ROOT / reference['path']) == reference['sha256']
    proof = read_json(ROOT / reference['path'])
    assert proof['T_semantic_valid'] is False and proof['X_semantic_valid'] is True
    native = np.array(load_asset(row['source_asset_identity'][0]))
    assert native.shape == (2404, 3981, 3)
    recipient = [657, 1536, 741, 1609]
    donor_box = [1355, 1287, 1447, 1360]
    x0, y0, x1, y1 = recipient
    sham, fit = extract_original(native[y0:y1, x0:x1])
    u0, v0, u1, v1 = donor_box
    rotated_F, donor_fit = extract_original(native[v0:v1, u0:u1])
    upright_F = np.rot90(rotated_F)
    a, b, c, d = fit['ink_bounds']
    dest = OUT / 'causal_pilot/edit_bank/mathwild742_alternative_letter_v1'
    if dest.exists():
        raise FileExistsError('Preserve existing source-control bank')
    pending, controls = {}, {}
    for kind, mask, literal in [('semantic', upright_F, 'F'), ('sham', sham, 'A')]:
        resized = np.clip(np.array(Image.fromarray(mask.astype(np.float32)).resize(
            (c-a, d-b), Image.Resampling.BICUBIC)), 0, 1)
        alpha = np.zeros((y1-y0, x1-x0), dtype=float)
        alpha[b:d, a:c] = resized
        patch = np.rint(np.array(fit['background_rgb']) * (1-alpha[..., None])).astype(np.uint8)
        variant = native.copy()
        variant[y0:y1, x0:x1] = patch
        name = 'X_' + kind
        pending[name] = variant
        controls[name] = dict(source='X', original='A', value=literal, recipient=recipient,
            donor_source='T' if kind == 'semantic' else 'X', renderer_fit=fit,
            **validate_local_variant(native, variant, [recipient]), independently_reviewed=False)
    dest.mkdir(parents=True)
    for name, variant in pending.items():
        path = dest / (name + '.png')
        Image.fromarray(variant).save(path)
        with Image.open(path) as saved:
            assert np.array_equal(np.array(saved.convert('RGB')), variant)
        controls[name].update(path=str(path.relative_to(ROOT)), sha256=sha(path))
    dependencies = [ROOT / 'scripts/stage7a_bench' / name for name in
        ('mathwild742_edit_bank_v2.py', 'mathwild216_label_edit_bank_v2.py', 'local_edit_validation_v2.py')]
    write_json(dest / 'candidate_manifest.json', dict(status='PIXEL_VALID_SEMANTICS_PENDING',
        event_id=row['event_id'], source_annotation_path=str(annotation_path.relative_to(ROOT)),
        source_annotation_sha256=sha(annotation_path), source_asset=row['source_asset_identity'][0],
        controls=controls, source_value_policy=None, source_constraint_review=reference,
        donor_extraction=dict(box=donor_box, fit=donor_fit, quarter_turns_counterclockwise=1),
        dependency_sha256={str(p.relative_to(ROOT)):sha(p) for p in dependencies},
        unavailable_controls={'T':'F-to-A contradicts the shown adjacency to D; no T images generated.'},
        causal_scores_used=False, pilot_selected=False, semantic_review_pending=True), freeze=True)
    print('TWO_ALTERNATIVE_CONTROLS_PREPARED; DIRECT_REVIEW_PENDING')


if __name__ == '__main__':
    main()
