"""Prepare matched glyph edits for the correct G-to-N coefficient read."""
import numpy as np
from PIL import Image

from scripts.stage7a.common import ROOT, read_json, read_jsonl, sha, write_json
from scripts.stage7a_bench.charxiv568_edit_bank_v2 import transplant_black_glyph
from scripts.stage7a_bench.image_inputs_v2 import load_asset
from scripts.stage7a_bench.local_edit_validation_v2 import validate_local_variant
from scripts.stage7a_bench.source_value_policy_v2 import numeric_replacement

OUT = ROOT / 'outputs/stage7a_bench_v2'


def main():
    ap = OUT / 'causal_pilot/source_reviews/charxiv__images%2F568.jpg__image_present__e01_v1.json'
    annotation = read_json(ap)
    pp = ROOT / annotation['source_value_policy']['path']
    assert sha(pp) == annotation['source_value_policy']['sha256']
    policy = read_json(pp)
    assert sha(ROOT / policy['implementation_path']) == policy['implementation_sha256']
    row = next(r for r in read_jsonl(OUT / 'cohort/benchmark_manifests/charxiv_image_present_native.jsonl')
               if r['event_id'] == annotation['event_id'])
    with load_asset(row['image_assets'][0]) as image:
        native = np.array(image)
    assert native.shape == (1024, 1024, 3)
    specs = {
        'T_semantic': dict(source='T', original='-0.0466', value='-0.0461',
            donor=[249, 654, 261, 672], recipient=[499, 772, 511, 790],
            donor_identity='Penultimate1 of fromV/toT0.6817'),
        'T_sham': dict(source='T', original='-0.0466', value='-0.0466',
            donor=[355, 187, 367, 205], recipient=[499, 772, 511, 790],
            donor_identity='Middle6 of fromY/toV1.0654'),
        'X_semantic': dict(source='X', original='0.2338', value='0.2333',
            donor=[377, 71, 389, 89], recipient=[611, 772, 623, 790],
            donor_identity='Last3 of fromY/toS0.3673'),
        'X_sham': dict(source='X', original='0.2338', value='0.2338',
            donor=[260, 71, 272, 89], recipient=[611, 772, 623, 790],
            donor_identity='Last8 of fromV/toS0.3638'),
    }
    dest = OUT / 'causal_pilot/edit_bank/charxiv568_correct_numeric_v1'
    if dest.exists():
        raise FileExistsError('Preserve existing candidate edit bank')
    pending, controls = {}, {}
    for name, spec in specs.items():
        if name.endswith('semantic'):
            assert numeric_replacement(spec['original'], lower=None, upper=None) == spec['value']
        variant, rendering = transplant_black_glyph(native, spec['donor'], spec['recipient'])
        pending[name] = variant
        controls[name] = dict(**spec, **validate_local_variant(native, variant, [spec['recipient']]),
                              rendering=rendering, independently_reviewed=False)
    dest.mkdir(parents=True)
    for name, variant in pending.items():
        path = dest / (name + '.png')
        Image.fromarray(variant).save(path)
        with Image.open(path) as saved:
            assert np.array_equal(np.array(saved.convert('RGB')), variant)
        controls[name].update(path=str(path.relative_to(ROOT)), sha256=sha(path))
    dependencies = ['charxiv568_correct_edit_bank_v2.py', 'charxiv568_edit_bank_v2.py', 'local_edit_validation_v2.py']
    write_json(dest / 'candidate_manifest.json', dict(status='PIXEL_VALID_SEMANTICS_PENDING',
        event_id=row['event_id'], source_annotation_path=str(ap.relative_to(ROOT)),
        source_annotation_sha256=sha(ap), source_asset=row['image_assets'][0],
        source_value_policy=annotation['source_value_policy'], controls=controls,
        dependency_sha256={str((ROOT / 'scripts/stage7a_bench' / n).relative_to(ROOT)):
                           sha(ROOT / 'scripts/stage7a_bench' / n) for n in dependencies},
        causal_scores_used=False, pilot_selected=False, semantic_review_pending=True), freeze=True)
    print('CANDIDATE_EDITS_PREPARED', len(controls), 'MANUAL_REVIEW_PENDING')


if __name__ == '__main__':
    main()
