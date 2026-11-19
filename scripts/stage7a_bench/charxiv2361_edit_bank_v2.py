"""Prepare source-reviewed digit substitutions for CharXiv2361.

This fixed scientific intervention copies same-figure raster glyphs. It creates
candidate images only; independent visual review must precede causal use.
"""
import numpy as np
from PIL import Image

from scripts.stage7a.common import ROOT, read_json, read_jsonl, sha, write_json
from scripts.stage7a_bench.image_inputs_v2 import load_asset
from scripts.stage7a_bench.local_edit_validation_v2 import validate_local_variant
from scripts.stage7a_bench.source_value_policy_v2 import numeric_replacement

OUT = ROOT / 'outputs/stage7a_bench_v2'


def main():
    source_path = OUT / 'causal_pilot/source_reviews/charxiv__images%2F2361.jpg__image_present__e00_v1.json'
    annotation = read_json(source_path)
    policy_path = ROOT / annotation['source_value_policy']['path']
    policy = read_json(policy_path)
    assert sha(policy_path) == annotation['source_value_policy']['sha256']
    assert sha(ROOT / policy['implementation_path']) == policy['implementation_sha256']
    rows = read_jsonl(OUT / 'cohort/benchmark_manifests/charxiv_image_present_native.jsonl')
    row = next(r for r in rows if r['event_id'] == annotation['event_id'])
    assert len(row['image_assets']) == 1
    native_image = load_asset(row['image_assets'][0])
    assert native_image.size == (1024, 413)
    native = np.array(native_image)
    # Values are vertical: their final decimal digit is the uppermost glyph.
    # Same-source semantic/sham controls share the exact recipient rectangle.
    specs = {
        'T_semantic': dict(source='T', original='75.68', value='75.63',
            donor=[336, 13, 354, 28], recipient=[117, 13, 135, 28],
            donor_identity='PCA final digit3 in73.23'),
        'T_sham': dict(source='T', original='75.68', value='75.68',
            donor=[773, 13, 791, 28], recipient=[117, 13, 135, 28],
            donor_identity='COF final digit8 in64.08'),
        'X_semantic': dict(source='X', original='75.71', value='75.76',
            donor=[446, 13, 465, 28], recipient=[191, 13, 210, 28],
            donor_identity='ECOD final digit6 in72.76'),
        'X_sham': dict(source='X', original='75.71', value='75.71',
            donor=[409, 13, 428, 28], recipient=[191, 13, 210, 28],
            donor_identity='HBOS final digit1 in72.81'),
    }
    dest = OUT / 'causal_pilot/edit_bank/charxiv2361_numeric_v1'
    if dest.exists():
        raise RuntimeError('Candidate edit bank already exists; do not overwrite')
    controls = {}
    for name, spec in specs.items():
        if name.endswith('semantic'):
            assert numeric_replacement(spec['original'], lower='0', upper='100') == spec['value']
        x0, y0, x1, y1 = spec['donor']
        u0, v0, u1, v1 = spec['recipient']
        assert (x1-x0, y1-y0) == (u1-u0, v1-v0)
        variant = native.copy()
        variant[v0:v1, u0:u1] = native[y0:y1, x0:x1]
        locality = validate_local_variant(native, variant, [spec['recipient']])
        dest.mkdir(parents=True, exist_ok=True)
        path = dest / (name + '.png')
        Image.fromarray(variant).save(path)
        with Image.open(path) as saved:
            assert np.array_equal(np.array(saved.convert('RGB')), variant)
        controls[name] = dict(**spec, path=str(path.relative_to(ROOT)), sha256=sha(path),
            **locality, independently_reviewed=False)
    write_json(dest / 'candidate_manifest.json', dict(status='PIXEL_VALID_SEMANTICS_PENDING',
        event_id=row['event_id'], source_annotation_path=str(source_path.relative_to(ROOT)),
        source_annotation_sha256=sha(source_path), source_asset=row['image_assets'][0],
        source_value_policy=annotation['source_value_policy'], controls=controls,
        dependency_sha256={str(p.relative_to(ROOT)): sha(p) for p in
            (ROOT / 'scripts/stage7a_bench/charxiv2361_edit_bank_v2.py',
             ROOT / 'scripts/stage7a_bench/local_edit_validation_v2.py')},
        causal_scores_used=False, pilot_selected=False, semantic_review_pending=True), freeze=True)
    print('CANDIDATE_EDITS_PREPARED', len(controls), 'MANUAL_REVIEW_PENDING')


if __name__ == '__main__':
    main()
