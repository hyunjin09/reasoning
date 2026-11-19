"""Prepare exact rope-count controls using unmodified photographic donors.

Each semantic/sham pair uses the same recipient and half-resolution bilinear
resampling. Full-image manual review must verify knots and rope continuity.
"""
import numpy as np
from PIL import Image

from scripts.stage7a.common import ROOT, read_json, read_jsonl, sha, write_json
from scripts.stage7a_bench.image_inputs_v2 import load_asset
from scripts.stage7a_bench.local_edit_validation_v2 import validate_local_variant

OUT = ROOT / 'outputs/stage7a_bench_v2'
RECIPIENTS = {'T': [798, 987, 862, 1039], 'X': [773, 847, 835, 896]}
DONORS = {
    'T_semantic': [872, 985, 936, 1037],
    'T_sham': RECIPIENTS['T'],
    'X_semantic': [693, 847, 755, 896],
    'X_sham': RECIPIENTS['X'],
}


def main():
    ap = OUT / 'causal_pilot/source_reviews/mathvision_wild__80__photo__e01_v2.json'
    annotation = read_json(ap)
    assert annotation['candidates'] == dict(correct='three', foil='two',
        target_semantic='two', alternative_original='two', alternative_semantic='three')
    rule = annotation['count_candidate_rule']
    assert sha(ROOT / rule['path']) == rule['sha256']
    row = read_jsonl(OUT / 'cohort/benchmark_manifests/mathvision_wild_photo_native.jsonl')[8]
    assert row['event_id'] == annotation['event_id']
    asset = row['source_asset_identity'][0]
    with load_asset(asset) as image:
        native = np.array(image)
    assert native.shape == (1640, 3648, 3)
    dest = OUT / 'causal_pilot/edit_bank/mathwild80_rope_count_v1'
    if dest.exists():
        raise FileExistsError('Preserve existing source-control bank')
    pending, controls = {}, {}
    for name, donor in DONORS.items():
        source, kind = name.split('_')
        recipient = RECIPIENTS[source]
        x0, y0, x1, y1 = recipient
        dx0, dy0, dx1, dy1 = donor
        width, height = x1-x0, y1-y0
        assert (dx1-dx0, dy1-dy0) == (width, height)
        patch = Image.fromarray(native[dy0:dy1, dx0:dx1])
        patch = patch.resize((width//2, height//2), Image.Resampling.BILINEAR)
        patch = patch.resize((width, height), Image.Resampling.BILINEAR)
        variant = native.copy()
        variant[y0:y1, x0:x1] = np.array(patch)
        original = 'three' if source == 'T' else 'two'
        changed = 'two' if source == 'T' else 'three'
        pending[name] = variant
        controls[name] = dict(source=source, original=original,
            value=changed if kind == 'semantic' else original, recipient=recipient,
            original_donor=donor, operation='Original donor patch, half-size bilinear resampling and restoration',
            original_pixels_only=True,
            rendering_qualification='Donor translation and local smoothing require full-image count/continuity and sham review',
            **validate_local_variant(native, variant, [recipient]), independently_reviewed=False)
    dest.mkdir(parents=True)
    for name, variant in pending.items():
        path = dest / (name + '.png')
        Image.fromarray(variant).save(path)
        with Image.open(path) as saved:
            assert np.array_equal(np.array(saved.convert('RGB')), variant)
        controls[name].update(path=str(path.relative_to(ROOT)), sha256=sha(path))
    dependencies = [ROOT / 'scripts/stage7a_bench' / name for name in
        ('mathwild80_rope_edit_bank_v2.py', 'local_edit_validation_v2.py')]
    write_json(dest / 'candidate_manifest.json', dict(status='PIXEL_VALID_SEMANTICS_PENDING',
        event_id=row['event_id'], source_annotation_path=str(ap.relative_to(ROOT)),
        source_annotation_sha256=sha(ap), source_asset=asset, controls=controls,
        count_candidate_rule=rule,
        dependency_sha256={str(p.relative_to(ROOT)): sha(p) for p in dependencies},
        causal_scores_used=False, pilot_selected=False, semantic_review_pending=True), freeze=True)
    print('ROPE_COUNT_PAIRS_PREPARED_MANUAL_REVIEW_PENDING')


if __name__ == '__main__':
    main()
