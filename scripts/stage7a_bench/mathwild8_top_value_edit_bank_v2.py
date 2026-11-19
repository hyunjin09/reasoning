"""Render the visible top7->2 and matched7 without altering hidden entries.

The original digit determines placement, ink bounds, contrast and background.
Both controls use the same existing project-local font and fitting procedure.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from scripts.stage7a.common import ROOT, read_json, read_jsonl, sha, write_json
from scripts.stage7a_bench.charxiv1690_edit_bank_v2 import FONT
from scripts.stage7a_bench.image_inputs_v2 import load_asset
from scripts.stage7a_bench.local_edit_validation_v2 import validate_local_variant
from scripts.stage7a_bench.mathwild216_label_edit_bank_v2 import extract_original
from scripts.stage7a_bench.source_value_policy_v2 import numeric_replacement

OUT = ROOT / 'outputs/stage7a_bench_v2'
RECIPIENT = [3029, 589, 3076, 663]


def main():
    ap = OUT / 'causal_pilot/source_reviews/mathvision_wild__8__photo__e00_v1.json'
    annotation = read_json(ap)
    assert numeric_replacement('7', lower='0', upper=None) == '2'
    assert annotation['candidates'] == dict(correct='7', foil='2', target_semantic='2')
    policy = annotation['source_value_policy']
    assert sha(ROOT / policy['path']) == policy['sha256']
    assert FONT.resolve().is_relative_to(ROOT / '.venv')
    row = read_jsonl(OUT / 'cohort/benchmark_manifests/mathvision_wild_photo_native.jsonl')[32]
    assert row['event_id'] == annotation['event_id']
    asset = row['source_asset_identity'][0]
    with load_asset(asset) as image:
        native = np.array(image)
    assert native.shape == (1237, 3648, 3)
    x0, y0, x1, y1 = RECIPIENT
    original_alpha, fit = extract_original(native[y0:y1, x0:x1])
    contrast = float(np.percentile(original_alpha[original_alpha > .18], 90))
    a, b, c, d = fit['ink_bounds']
    font = ImageFont.truetype(str(FONT), 96)
    dest = OUT / 'causal_pilot/edit_bank/mathwild8_top_value_v1'
    if dest.exists():
        raise FileExistsError('Preserve existing source-control bank')
    pending, controls = {}, {}
    for kind, value in [('semantic', '2'), ('sham', '7')]:
        bounds = font.getbbox(value)
        glyph = Image.new('L', (bounds[2]-bounds[0], bounds[3]-bounds[1]), 0)
        ImageDraw.Draw(glyph).text((-bounds[0], -bounds[1]), value, font=font, fill=255)
        resized = np.asarray(glyph.resize((c-a, d-b), Image.Resampling.LANCZOS)) / 255
        alpha = np.zeros((y1-y0, x1-x0), dtype=float)
        alpha[b:d, a:c] = resized * contrast
        variant = native.copy()
        variant[y0:y1, x0:x1] = np.rint(
            np.array(fit['background_rgb']) * (1-alpha[..., None])).astype(np.uint8)
        name = 'T_' + kind
        pending[name] = variant
        controls[name] = dict(source='T', original='7', value=value,
            recipient=RECIPIENT, renderer_fit=dict(recipient_fit=fit,
                native_ink_contrast=contrast, font_base_size=96,
                font_glyph_bounds=list(bounds), fit_uses_original_pixels_only=True,
                operation='Same font glyph fitted to original7 bounds/contrast/background',
                qualification='Font shape, sharpness and flattened paper require direct review'),
            **validate_local_variant(native, variant, [RECIPIENT]), independently_reviewed=False)
    dest.mkdir(parents=True)
    for name, variant in pending.items():
        path = dest / (name + '.png')
        Image.fromarray(variant).save(path)
        with Image.open(path) as saved:
            assert np.array_equal(np.array(saved.convert('RGB')), variant)
        controls[name].update(path=str(path.relative_to(ROOT)), sha256=sha(path))
    dependencies = [ROOT / 'scripts/stage7a_bench' / name for name in
        ['mathwild8_top_value_edit_bank_v2.py', 'charxiv1690_edit_bank_v2.py',
         'mathwild216_label_edit_bank_v2.py', 'local_edit_validation_v2.py',
         'source_value_policy_v2.py']]
    write_json(dest / 'candidate_manifest.json', dict(status='PIXEL_VALID_SEMANTICS_PENDING',
        event_id=row['event_id'], source_annotation_path=str(ap.relative_to(ROOT)),
        source_annotation_sha256=sha(ap), source_asset=asset, controls=controls,
        source_value_policy=policy, font_path=str(FONT.relative_to(ROOT)), font_sha256=sha(FONT),
        dependency_sha256={str(p.relative_to(ROOT)): sha(p) for p in dependencies},
        unavailable_controls={'X': 'No independent alternative source identified'},
        causal_scores_used=False, pilot_selected=False, semantic_review_pending=True), freeze=True)
    print('TARGET_TOP_VALUE_PAIR_PREPARED_MANUAL_REVIEW_PENDING')


if __name__ == '__main__':
    main()
