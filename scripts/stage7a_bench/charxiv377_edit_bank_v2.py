"""Prepare count edits/shams using the existing same-figure glyph renderer."""
import numpy as np
from PIL import Image

from scripts.stage7a.common import ROOT, read_json, read_jsonl, sha, write_json
from scripts.stage7a_bench.charxiv568_edit_bank_v2 import transplant_black_glyph
from scripts.stage7a_bench.image_inputs_v2 import load_asset
from scripts.stage7a_bench.local_edit_validation_v2 import validate_local_variant
from scripts.stage7a_bench.source_value_policy_v2 import numeric_replacement

OUT = ROOT / 'outputs/stage7a_bench_v2'


def main():
    ap = OUT / 'causal_pilot/source_reviews/charxiv__images%2F377.jpg__image_present__e00_v1.json'
    annotation = read_json(ap)
    pp = ROOT / annotation['source_value_policy']['path']
    assert sha(pp) == annotation['source_value_policy']['sha256']
    policy = read_json(pp)
    assert sha(ROOT / policy['implementation_path']) == policy['implementation_sha256']
    row = next(r for r in read_jsonl(OUT / 'cohort/benchmark_manifests/charxiv_image_present_native.jsonl')
               if r['event_id'] == annotation['event_id'])
    with load_asset(row['image_assets'][0]) as image:
        native = np.array(image)
    assert native.shape == (834, 1024, 3)
    dest = OUT / 'causal_pilot/edit_bank/charxiv377_numeric_v1'
    if dest.exists():
        raise FileExistsError('Preserve existing candidate edit bank')
    specs = {}
    for source, original, recipient in [('T', '3430', [137, 55, 150, 74]),
                                        ('X', '10', [125, 218, 138, 237])]:
        for kind, donor, identity in [('semantic', [530, 136, 543, 155], 'True2/predicted5 count5'),
                                     ('sham', [234, 136, 247, 155], 'Last0 of true2/predicted2 count180')]:
            value = numeric_replacement(original, lower='0', upper=None) if kind == 'semantic' else original
            specs[source + '_' + kind] = dict(source=source, original=original, value=value,
                donor=donor, recipient=recipient, donor_identity=identity)
    pending, controls = {}, {}
    for name, spec in specs.items():
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
    dependencies = ['charxiv377_edit_bank_v2.py', 'charxiv568_edit_bank_v2.py', 'local_edit_validation_v2.py']
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
