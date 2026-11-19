"""Prepare deterministic local digit controls for the reviewed CharXiv446 event.

These are scientific pixel interventions specified in native coordinates. Digit
patches come from the same source figure and retain their original rasterization.
This writes candidate controls only; it cannot certify semantics or select a pilot.
"""
import numpy as np
from PIL import Image

from scripts.stage7a.common import ROOT, read_json, read_jsonl, sha, write_json
from scripts.stage7a_bench.image_inputs_v2 import load_asset
from scripts.stage7a_bench.local_edit_validation_v2 import validate_local_variant
from scripts.stage7a_bench.source_value_policy_v2 import numeric_replacement

OUT = ROOT / 'outputs/stage7a_bench_v2'


def main():
    source_path = OUT / 'causal_pilot/source_reviews/charxiv__images%2F446.jpg__image_present__e01_v2.json'
    annotation = read_json(source_path)
    policy = read_json(ROOT / annotation['source_value_policy']['path'])
    assert sha(ROOT / annotation['source_value_policy']['path']) == annotation['source_value_policy']['sha256']
    assert sha(ROOT / policy['implementation_path']) == policy['implementation_sha256']
    rows = read_jsonl(OUT / 'cohort/benchmark_manifests/charxiv_image_present_native.jsonl')
    row = next(r for r in rows if r['event_id'] == annotation['event_id'])
    assert len(row['image_assets']) == 1
    native_image = load_asset(row['image_assets'][0])
    native = np.array(native_image)
    assert native_image.size == (1024, 370)
    # Same-size source glyph patches; the leading digit and decimal dot in
    # each recipient remain unchanged. All variants use the same operation.
    specs = {
        'T_semantic': dict(source='T', original='1.9', value='1.4',
            donor=[119, 64, 126, 76], recipient=[504, 184, 511, 196],
            donor_identity='DACE/Cooperative first digit4 in4.5'),
        'T_sham': dict(source='T', original='1.9', value='1.9',
            donor=[504, 304, 511, 316], recipient=[504, 184, 511, 196],
            donor_identity='DIOR/Socialcomparison final digit9 in1.9'),
        'X_semantic': dict(source='X', original='1.5', value='1.0',
            donor=[504, 124, 511, 136], recipient=[397, 184, 404, 196],
            donor_identity='DIOR/Hard final digit0 in1.0'),
        'X_sham': dict(source='X', original='1.5', value='1.5',
            donor=[128, 64, 135, 76], recipient=[397, 184, 404, 196],
            donor_identity='DACE/Cooperative final digit5 in4.5'),
    }
    dest = OUT / 'causal_pilot/edit_bank/charxiv446_numeric_v1'
    if dest.exists():
        raise RuntimeError('Candidate edit bank already exists; do not overwrite reviewed controls')
    controls = {}
    for name, spec in specs.items():
        if name.endswith('semantic'):
            assert numeric_replacement(spec['original'], lower='0', upper='100') == spec['value']
        x0, y0, x1, y1 = spec['donor']
        u0, v0, u1, v1 = spec['recipient']
        assert (x1-x0, y1-y0) == (u1-u0, v1-v0)
        variant = native.copy()
        variant[v0:v1, u0:u1] = native[y0:y1, x0:x1]
        local = validate_local_variant(native, variant, [spec['recipient']])
        dest.mkdir(parents=True, exist_ok=True)
        path = dest / (name + '.png')
        Image.fromarray(variant).save(path)
        # Validate the saved artifact, including exact decoded RGB equality.
        with Image.open(path) as saved:
            assert np.array_equal(np.array(saved.convert('RGB')), variant)
        controls[name] = dict(**spec, path=str(path.relative_to(ROOT)), sha256=sha(path),
            **local, independently_reviewed=False)
    write_json(dest / 'candidate_manifest.json', dict(status='PIXEL_VALID_SEMANTICS_PENDING',
        event_id=row['event_id'], source_annotation_path=str(source_path.relative_to(ROOT)),
        source_annotation_sha256=sha(source_path), source_asset=row['image_assets'][0],
        source_value_policy=annotation['source_value_policy'], controls=controls,
        dependency_sha256={p: sha(ROOT / p) for p in (
            'scripts/stage7a_bench/charxiv446_edit_bank_v2.py',
            'scripts/stage7a_bench/local_edit_validation_v2.py')},
        causal_scores_used=False, pilot_selected=False, semantic_review_pending=True), freeze=True)
    print('CANDIDATE_EDITS_PREPARED', len(controls), 'MANUAL_REVIEW_PENDING')


if __name__ == '__main__':
    main()
