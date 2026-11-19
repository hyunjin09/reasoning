"""Prepare matched count-label redraws for the reviewed dataset-split figure.

The existing source-only font fit is used unchanged. The matched white patch
also removes local hatching in X; this is explicit candidate rendering, not
semantic certification or a measured sham-effect result.
"""
import numpy as np
from PIL import Image

from scripts.stage7a.common import ROOT, read_json, read_jsonl, sha, write_json
from scripts.stage7a_bench.charxiv1690_edit_bank_v2 import FONT, fit_original, render_literal
from scripts.stage7a_bench.image_inputs_v2 import load_asset
from scripts.stage7a_bench.local_edit_validation_v2 import validate_local_variant
from scripts.stage7a_bench.source_value_policy_v2 import numeric_replacement

OUT = ROOT / 'outputs/stage7a_bench_v2'


def main():
    assert FONT.resolve().is_relative_to(ROOT / '.venv')
    ap = OUT / 'causal_pilot/source_reviews/charxiv__images%2F249.jpg__image_present__e03_v1.json'
    annotation = read_json(ap)
    pp = ROOT / annotation['source_value_policy']['path']
    assert sha(pp) == annotation['source_value_policy']['sha256']
    policy = read_json(pp)
    assert sha(ROOT / policy['implementation_path']) == policy['implementation_sha256']
    row = next(r for r in read_jsonl(OUT / 'cohort/benchmark_manifests/charxiv_image_present_native.jsonl')
               if r['event_id'] == annotation['event_id'])
    assert len(row['image_assets']) == 1
    with load_asset(row['image_assets'][0]) as image:
        native = np.array(image)
    assert native.shape == (524, 1023, 3)
    dest = OUT / 'causal_pilot/edit_bank/charxiv249_numeric_v1'
    if dest.exists():
        raise FileExistsError('Preserve the existing candidate edit bank')
    pending, controls = {}, {}
    for source, original in [('T', '50'), ('X', '300')]:
        box = annotation['sources'][source][0]['pixels']
        x0, y0, x1, y1 = box
        patch = native[y0:y1, x0:x1]
        fit = fit_original(patch, original)
        changed = numeric_replacement(original, lower='0', upper=None)
        for kind, value in [('semantic', changed), ('sham', original)]:
            name = source + '_' + kind
            variant = native.copy()
            variant[y0:y1, x0:x1] = render_literal(patch, value, fit)
            pending[name] = variant
            controls[name] = dict(source=source, original=original, value=value,
                recipient=box, renderer_fit=fit,
                **validate_local_variant(native, variant, [box]), independently_reviewed=False)
    dest.mkdir(parents=True)
    for name, variant in pending.items():
        path = dest / (name + '.png')
        Image.fromarray(variant).save(path)
        with Image.open(path) as saved:
            assert np.array_equal(np.array(saved.convert('RGB')), variant)
        controls[name].update(path=str(path.relative_to(ROOT)), sha256=sha(path))
    dependencies = ['charxiv249_edit_bank_v2.py', 'charxiv1690_edit_bank_v2.py', 'local_edit_validation_v2.py']
    write_json(dest / 'candidate_manifest.json', dict(status='PIXEL_VALID_SEMANTICS_PENDING',
        event_id=row['event_id'], source_annotation_path=str(ap.relative_to(ROOT)),
        source_annotation_sha256=sha(ap), source_asset=row['image_assets'][0],
        source_value_policy=annotation['source_value_policy'], controls=controls,
        font_path=str(FONT.relative_to(ROOT)), font_sha256=sha(FONT),
        dependency_sha256={str((ROOT / 'scripts/stage7a_bench' / n).relative_to(ROOT)):
                           sha(ROOT / 'scripts/stage7a_bench' / n) for n in dependencies},
        causal_scores_used=False, pilot_selected=False, semantic_review_pending=True), freeze=True)
    print('CANDIDATE_EDITS_PREPARED', len(controls), 'MANUAL_REVIEW_PENDING')


if __name__ == '__main__':
    main()
