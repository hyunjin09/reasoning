"""Prepare the reviewed wrong-distractor cell and its matched editing sham."""
import numpy as np
from PIL import Image, ImageDraw

from scripts.stage7a.common import ROOT, read_json, read_jsonl, sha, write_json
from scripts.stage7a_bench.image_inputs_v2 import load_asset
from scripts.stage7a_bench.local_edit_validation_v2 import validate_local_variant

OUT = ROOT / 'outputs/stage7a_bench_v2'


def main():
    ap = OUT / 'causal_pilot/source_reviews/mathvision_wild__66__photo__e02_v1.json'
    annotation = read_json(ap)
    reference = annotation['literal_rule_reference']
    assert sha(ROOT / reference['path']) == reference['sha256']
    assert read_json(ROOT / reference['path']) == annotation['literal_candidate_rule']
    assert annotation['candidates'] == dict(correct='white', foil='red',
        target_semantic='red', alternative_original='red', alternative_semantic='white')
    row = read_jsonl(OUT / 'cohort/benchmark_manifests/mathvision_wild_photo_native.jsonl')[22]
    assert row['event_id'] == annotation['event_id']
    asset = row['source_asset_identity'][0]
    with load_asset(asset) as im:
        native = np.array(im)
    assert native.shape == (1640, 3648, 3)
    recipient = [3003, 896, 3078, 968]
    polygon = [(3004, 899), (3071, 897), (3075, 961), (3007, 965)]
    mask_image = Image.new('1', (3648, 1640))
    ImageDraw.Draw(mask_image).polygon(polygon, fill=1)
    mask = np.array(mask_image, dtype=bool)
    colors = dict(red=np.median(native[913:951, 3016:3060], axis=(0, 1)),
                  white=np.median(native[905:944, 3092:3137], axis=(0, 1)))
    dest = OUT / 'causal_pilot/edit_bank/mathwild66_alternative_color_v1'
    if dest.exists():
        raise FileExistsError('Preserve existing source-control bank')
    pending, controls = {}, {}
    for kind, value in [('semantic', 'white'), ('sham', 'red')]:
        variant = native.copy()
        color = np.rint(colors[value]).astype(np.uint8)
        variant[mask] = color
        name = 'X_' + kind
        pending[name] = variant
        controls[name] = dict(source='X', original='red', value=value,
            recipient=recipient, rendering=dict(operation='Uniform native-color polygon repaint',
                polygon=polygon, color_rgb=color.tolist(), original_pixels_only=True,
                color_selection='Median of original E red-cell or adjacent E white-cell interior',
                donor_boxes=dict(red=[3016, 913, 3060, 951], white=[3092, 905, 3137, 944]),
                qualification='Preserves red outline; texture flattening and edge coverage need manual review'),
            **validate_local_variant(native, variant, [recipient]), independently_reviewed=False)
    dest.mkdir(parents=True)
    for name, variant in pending.items():
        path = dest / (name + '.png')
        Image.fromarray(variant).save(path)
        with Image.open(path) as saved:
            assert np.array_equal(np.array(saved.convert('RGB')), variant)
        controls[name].update(path=str(path.relative_to(ROOT)), sha256=sha(path))
    dependencies = [ROOT / 'scripts/stage7a_bench/mathwild66_color_edit_bank_v2.py',
                    ROOT / 'scripts/stage7a_bench/local_edit_validation_v2.py']
    write_json(dest / 'candidate_manifest.json', dict(status='PIXEL_VALID_SEMANTICS_PENDING',
        event_id=row['event_id'], source_annotation_path=str(ap.relative_to(ROOT)),
        source_annotation_sha256=sha(ap), source_asset=asset, controls=controls,
        source_value_policy=None, literal_candidate_rule=annotation['literal_candidate_rule'],
        literal_rule_reference=reference,
        dependency_sha256={str(p.relative_to(ROOT)): sha(p) for p in dependencies},
        unavailable_controls={'T': 'White-to-red edit destroys the sole correct D pattern'},
        causal_scores_used=False, pilot_selected=False, semantic_review_pending=True), freeze=True)
    print('ALTERNATIVE_COLOR_PAIR_PREPARED_MANUAL_REVIEW_PENDING')


if __name__ == '__main__':
    main()
