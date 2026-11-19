"""Prepare reviewed warning-cell category contrasts before any causal scores."""
from pathlib import Path

import numpy as np
from PIL import Image

from scripts.stage7a.common import ROOT, read_json, read_jsonl, sha, write_json
from scripts.stage7a_bench.image_inputs_v2 import load_asset
from scripts.stage7a_bench.local_edit_validation_v2 import validate_local_variant

OUT = ROOT / 'outputs/stage7a_bench_v2'


def main():
    rows = read_jsonl(OUT / 'cohort/benchmark_manifests/charxiv_image_present_native.jsonl')
    row = rows[64]
    annotation_path = OUT / 'causal_pilot/source_reviews' / (row['event_id'] + '__e01_v1.json')
    annotation = read_json(annotation_path)
    assert annotation['event_id'] == row['event_id']
    assert annotation['demanded_source_id'] == 'Alaska_onset3_warning_color'
    assert annotation['alternative']['source_id'] == 'Missouri_onset3_warning_color'
    reference = annotation['literal_rule_reference']
    assert sha(ROOT / reference['path']) == reference['sha256']
    assert read_json(ROOT / reference['path']) == annotation['literal_candidate_rule']
    assert annotation['candidates'] == dict(correct='dark purple', foil='red',
        target_semantic='red', alternative_original='red', alternative_semantic='dark purple')
    with load_asset(row['image_assets'][0]) as image:
        native = np.array(image)
    assert native.shape == (1024, 767, 3)
    recipients = dict(T=[629, 727, 652, 733], X=[629, 493, 652, 499])
    interiors = dict(T=[632, 728, 649, 731], X=[632, 494, 649, 497])
    colors = {}
    for source, box in recipients.items():
        x0, y0, x1, y1 = box
        footprint = annotation['sources'][source][0]
        a, b, c, d = footprint['pixels']
        assert footprint['source_size'] == [767, 1024]
        assert a <= x0 < x1 <= c and b <= y0 < y1 <= d
        a, b, c, d = interiors[source]
        assert x0 <= a < c <= x1 and y0 <= b < d <= y1
        colors[source] = np.rint(np.median(native[b:d, a:c].reshape(-1, 3), axis=0)).astype('uint8').tolist()
    dest = OUT / 'causal_pilot/edit_bank/charxiv_warning_color_v1'
    if dest.exists():
        raise FileExistsError('Preserve existing warning-cell bank')
    pending, controls = {}, {}
    for source, original, other in [('T', 'dark purple', 'X'), ('X', 'red', 'T')]:
        for kind in ('semantic', 'sham'):
            donor = other if kind == 'semantic' else source
            variant = native.copy()
            x0, y0, x1, y1 = recipients[source]
            variant[y0:y1, x0:x1] = colors[donor]
            name = source + '_' + kind
            pending[name] = variant
            controls[name] = dict(source=source, original=original,
                value=('red' if source == 'T' else 'dark purple') if kind == 'semantic' else original,
                recipient=recipients[source],
                rendering=dict(operation='Uniform RGB repaint of one native warning mark',
                    color_rgb=colors[donor], color_source=donor, color_source_interior=interiors[donor],
                    color_selection='Channelwise median of the reviewed original cell interior; no model outputs or effects',
                    paired_operation='Identical recipient rectangle and constant fill; sham uses original category',
                    qualification='Homogenizes JPEG texture and repaints thin-stroke edges; unchanged sham-effect gate applies'),
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
        dependency_sha256={str(p.relative_to(ROOT)): sha(p) for p in dependencies},
        causal_scores_used=False, pilot_selected=False, semantic_review_pending=True), freeze=True)
    print('CANDIDATE_WARNING_EDITS_PREPARED', len(controls), 'MANUAL_REVIEW_PENDING')


if __name__ == '__main__':
    main()
