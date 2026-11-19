"""Prepare native-cell color controls; manual semantics remain a separate gate."""
from pathlib import Path

import numpy as np
from PIL import Image

from scripts.stage7a.common import ROOT, read_json, read_jsonl, sha, write_json
from scripts.stage7a_bench.image_inputs_v2 import load_asset
from scripts.stage7a_bench.local_edit_validation_v2 import validate_local_variant

OUT = ROOT / 'outputs/stage7a_bench_v2'


def main():
    annotation_path = OUT / 'causal_pilot/source_reviews/charxiv__images%2F1794.jpg__image_present__e00_v1.json'
    annotation = read_json(annotation_path)
    reference = annotation['literal_rule_reference']
    rule_path = ROOT / reference['path']
    assert sha(rule_path) == reference['sha256']
    assert read_json(rule_path) == annotation['literal_candidate_rule']
    assert annotation['candidates'] == dict(correct='blue', foil='red',
        target_semantic='red', alternative_original='red', alternative_semantic='blue')
    row = next(r for r in read_jsonl(OUT / 'cohort/benchmark_manifests/charxiv_image_present_native.jsonl')
               if r['event_id'] == annotation['event_id'])
    with load_asset(row['image_assets'][0]) as image:
        native = np.array(image)
    assert native.shape == (646, 1023, 3)
    recipients = dict(T=[488, 134, 523, 169], X=[229, 392, 264, 428])
    colors = {}
    for source, box in recipients.items():
        x0, y0, x1, y1 = box
        footprint = annotation['sources'][source][0]
        a, b, c, d = footprint['pixels']
        assert footprint['source_size'] == [1023, 646]
        assert a <= x0 < x1 <= c and b <= y0 < y1 <= d
        values, counts = np.unique(native[y0:y1, x0:x1].reshape(-1, 3),
                                   axis=0, return_counts=True)
        colors[source] = values[np.argmax(counts)].tolist()
    dest = OUT / 'causal_pilot/edit_bank/charxiv1794_color_v1'
    if dest.exists():
        raise FileExistsError('Preserve existing candidate edit bank')
    pending, controls = {}, {}
    for source, original, other in [('T', 'blue', 'X'), ('X', 'red', 'T')]:
        for kind in ('semantic', 'sham'):
            donor = other if kind == 'semantic' else source
            color = colors[donor]
            variant = native.copy()
            x0, y0, x1, y1 = recipients[source]
            variant[y0:y1, x0:x1] = color
            name = source + '_' + kind
            pending[name] = variant
            controls[name] = dict(source=source, original=original,
                value=('red' if source == 'T' else 'blue') if kind == 'semantic' else original,
                recipient=recipients[source],
                rendering=dict(operation='Uniform native RGB cell-interior repaint',
                    color_rgb=color, color_source=donor,
                    color_selection='Most frequent native RGB triplet in the independently reviewed donor cell interior',
                    paired_operation='Identical recipient and constant-fill operation; sham uses the original cell category',
                    qualification='Homogenizes JPEG texture and slight within-cell edge colors; unchanged sham-effect gate applies'),
                **validate_local_variant(native, variant, [recipients[source]]),
                independently_reviewed=False)
    dest.mkdir(parents=True)
    for name, variant in pending.items():
        path = dest / (name + '.png')
        Image.fromarray(variant).save(path)
        with Image.open(path) as saved:
            assert np.array_equal(np.array(saved.convert('RGB')), variant)
        controls[name].update(path=str(path.relative_to(ROOT)), sha256=sha(path))
    dependencies = [Path(__file__).resolve(), ROOT / 'scripts/stage7a_bench/local_edit_validation_v2.py']
    write_json(dest / 'candidate_manifest.json', dict(status='PIXEL_VALID_SEMANTICS_PENDING',
        event_id=row['event_id'], source_annotation_path=str(annotation_path.relative_to(ROOT)),
        source_annotation_sha256=sha(annotation_path), source_asset=row['image_assets'][0],
        source_value_policy=None, literal_candidate_rule=annotation['literal_candidate_rule'],
        literal_rule_reference=reference, controls=controls,
        dependency_sha256={str(p.relative_to(ROOT)): sha(p)
                           for p in dependencies},
        causal_scores_used=False, pilot_selected=False, semantic_review_pending=True), freeze=True)
    print('CANDIDATE_COLOR_EDITS_PREPARED', len(controls), 'MANUAL_REVIEW_PENDING')


if __name__ == '__main__':
    main()
