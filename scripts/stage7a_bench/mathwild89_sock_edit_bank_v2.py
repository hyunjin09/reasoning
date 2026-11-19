"""Prepare fixed2↔7 sock-label controls; direct review remains mandatory."""
import numpy as np
from PIL import Image

from scripts.stage7a.common import ROOT, read_json, read_jsonl, sha, write_json
from scripts.stage7a_bench.image_inputs_v2 import load_asset
from scripts.stage7a_bench.local_edit_validation_v2 import validate_local_variant

OUT = ROOT / 'outputs/stage7a_bench_v2'


from scripts.stage7a_bench.mathwild216_label_edit_bank_v2 import extract_original

def main():
    ap = OUT / 'causal_pilot/source_reviews/mathvision_wild__89__photo__e01_v1.json'
    annotation = read_json(ap)
    row = read_jsonl(OUT / 'cohort/benchmark_manifests/mathvision_wild_photo_native.jsonl')[113]
    assert row['event_id'] == annotation['event_id']
    assert annotation['candidates'] == dict(correct='2', foil='7', target_semantic='7',
        alternative_original='7', alternative_semantic='2')
    asset = row['source_asset_identity'][0]
    with load_asset(asset) as im:
        native = np.array(im)
    assert native.shape == (1640, 3648, 3)
    extracted = {}
    for role in ('T', 'X'):
        x0, y0, x1, y1 = annotation['sources'][role][0]['pixels']
        extracted[role] = extract_original(native[y0:y1, x0:x1])
    dest = OUT / 'causal_pilot/edit_bank/mathwild89_sock_digit_swap_v1'
    if dest.exists():
        raise FileExistsError('Preserve existing source-control bank')
    pending, controls = {}, {}
    literals = dict(T='2', X='7')
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
    dependencies = [ROOT / 'scripts/stage7a_bench/mathwild89_sock_edit_bank_v2.py', ROOT / 'scripts/stage7a_bench/mathwild216_label_edit_bank_v2.py',
                    ROOT / 'scripts/stage7a_bench/local_edit_validation_v2.py']
    write_json(dest / 'candidate_manifest.json', dict(status='PIXEL_VALID_SEMANTICS_PENDING',
        event_id=row['event_id'], source_annotation_path=str(ap.relative_to(ROOT)),
        source_annotation_sha256=sha(ap), source_asset=asset, controls=controls,
        source_value_policy=annotation['source_value_policy'], source_constraint_review=annotation['source_constraint_review'],
        dependency_sha256={str(p.relative_to(ROOT)): sha(p) for p in dependencies},
        unavailable_controls={}, causal_scores_used=False, pilot_selected=False,
        semantic_review_pending=True), freeze=True)
    print('FOUR_LITERAL_CONTROLS_PREPARED', 'MANUAL_REVIEW_PENDING')


if __name__ == '__main__':
    main()
