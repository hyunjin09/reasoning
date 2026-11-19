"""Prepare matched title-count redraws using only original source pixels.

Font placement/contrast is fitted to the original literal, never to model
outputs. Semantic and sham use the same fitted renderer. Pixel validation
does not certify semantic consistency; a separate full-image review is required.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from scripts.stage7a.common import ROOT, read_json, read_jsonl, sha, write_json
from scripts.stage7a_bench.image_inputs_v2 import load_asset
from scripts.stage7a_bench.local_edit_validation_v2 import validate_local_variant
from scripts.stage7a_bench.source_value_policy_v2 import numeric_replacement

OUT = ROOT / 'outputs/stage7a_bench_v2'
FONT = ROOT / '.venv/lib/python3.12/site-packages/matplotlib/mpl-data/fonts/ttf/DejaVuSans.ttf'


def glyph_mask(text, shape, size, position):
    height, width = shape
    font = ImageFont.truetype(str(FONT), size)
    x, y = position
    box = font.getbbox(text)
    if not (0 <= x + box[0] < x + box[2] <= width and
            0 <= y + box[1] < y + box[3] <= height):
        return None
    im = Image.new('L', (width, height), 0)
    ImageDraw.Draw(im).text(position, text, font=font, fill=255)
    return np.asarray(im, dtype=np.float64) / 255


def fit_original(patch, literal):
    # A bounded source-only fit in native pixels; no raster rescaling.
    observed = 1 - patch.mean(axis=2) / 255
    best = None
    for size in range(14, 23):
        for y in range(-6, 5):
            for x in range(7):
                mask = glyph_mask(literal, patch.shape[:2], size, (x, y))
                if mask is None or not mask.any():
                    continue
                contrast = float(np.clip(np.sum(mask * observed) / np.sum(mask * mask), 0, 1))
                mse = float(np.mean((mask * contrast - observed) ** 2))
                candidate = (mse, size, x, y, contrast)
                if best is None or candidate < best:
                    best = candidate
    if best is None or best[0] > 0.08 or best[4] < 0.3:
        raise ValueError('Original source literal cannot be fitted within the fixed rendering bounds')
    mse, size, x, y, contrast = best
    return dict(original_literal=literal, normalized_pixel_mse=mse,
                font_size=size, position=[x, y], ink_contrast=contrast,
                fit_uses_original_pixels_only=True)


def render_literal(patch, literal, fit):
    mask = glyph_mask(literal, patch.shape[:2], fit['font_size'], fit['position'])
    if mask is None:
        raise ValueError('Replacement would clip; do not alter its fitted geometry')
    gray = np.rint(255 * (1 - mask * fit['ink_contrast'])).astype(np.uint8)
    return np.repeat(gray[:, :, None], 3, axis=2)


def main():
    assert FONT.resolve().is_relative_to(ROOT / '.venv')
    annotation_path = OUT / 'causal_pilot/source_reviews/charxiv__images%2F1690.jpg__image_present__e00_v1.json'
    annotation = read_json(annotation_path)
    policy_path = ROOT / annotation['source_value_policy']['path']
    policy = read_json(policy_path)
    assert sha(policy_path) == annotation['source_value_policy']['sha256']
    assert sha(ROOT / policy['implementation_path']) == policy['implementation_sha256']
    row = next(r for r in read_jsonl(OUT / 'cohort/benchmark_manifests/charxiv_image_present_native.jsonl')
               if r['event_id'] == annotation['event_id'])
    assert len(row['image_assets']) == 1
    with load_asset(row['image_assets'][0]) as image:
        native = np.array(image)
    assert native.shape == (491, 1024, 3)
    dest = OUT / 'causal_pilot/edit_bank/charxiv1690_numeric_v1'
    if dest.exists():
        raise RuntimeError('Candidate bank already exists; preserve it')
    pending, controls = {}, {}
    for source, original in [('T', '292'), ('X', '9360')]:
        box = annotation['sources'][source][0]['pixels']
        x0, y0, x1, y1 = box
        patch = native[y0:y1, x0:x1]
        fit = fit_original(patch, original)
        changed = numeric_replacement(original, lower='0', upper=None)
        for kind, value in [('semantic', changed), ('sham', original)]:
            name = source + '_' + kind
            variant = native.copy()
            variant[y0:y1, x0:x1] = render_literal(patch, value, fit)
            locality = validate_local_variant(native, variant, [box])
            pending[name] = variant
            controls[name] = dict(source=source, original=original, value=value,
                recipient=box, renderer_fit=fit, **locality, independently_reviewed=False)
    dest.mkdir(parents=True)
    for name, variant in pending.items():
        path = dest / (name + '.png')
        Image.fromarray(variant).save(path)
        with Image.open(path) as saved:
            assert np.array_equal(np.asarray(saved.convert('RGB')), variant)
        controls[name].update(path=str(path.relative_to(ROOT)), sha256=sha(path))
    write_json(dest / 'candidate_manifest.json', dict(status='PIXEL_VALID_SEMANTICS_PENDING',
        event_id=row['event_id'], source_annotation_path=str(annotation_path.relative_to(ROOT)),
        source_annotation_sha256=sha(annotation_path), source_asset=row['image_assets'][0],
        source_value_policy=annotation['source_value_policy'], controls=controls,
        font_path=str(FONT.relative_to(ROOT)), font_sha256=sha(FONT),
        dependency_sha256={str(p.relative_to(ROOT)): sha(p) for p in
            (ROOT / 'scripts/stage7a_bench/charxiv1690_edit_bank_v2.py',
             ROOT / 'scripts/stage7a_bench/local_edit_validation_v2.py')},
        causal_scores_used=False, pilot_selected=False, semantic_review_pending=True), freeze=True)
    print('CANDIDATE_EDITS_PREPARED', len(controls), 'MANUAL_REVIEW_PENDING')


if __name__ == '__main__':
    main()
