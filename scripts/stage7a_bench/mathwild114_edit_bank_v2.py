"""Prepare a target-only numeric/sham pair for the sideways train photograph.

Fit only the original printed31. The fixed31->36 rule preserves this task's
answer and diagram. X12->17 would invalidate its answer choices, so no X
controls are generated. Pixel checks do not replace full-image semantic review.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from scripts.stage7a.common import ROOT, read_json, read_jsonl, sha, write_json
from scripts.stage7a_bench.image_inputs_v2 import load_asset
from scripts.stage7a_bench.local_edit_validation_v2 import validate_local_variant
from scripts.stage7a_bench.source_value_policy_v2 import numeric_replacement

OUT = ROOT / 'outputs/stage7a_bench_v2'
FONT = ROOT / '.venv/lib/python3.12/site-packages/matplotlib/mpl-data/fonts/ttf/DejaVuSerif-Bold.ttf'


def mask(text, size, position, shape):
    height, width = shape
    font = ImageFont.truetype(str(FONT), size)
    box = font.getbbox(text)
    x, y = position
    if not (0 <= x+box[0] < x+box[2] <= width and
            0 <= y+box[1] < y+box[3] <= height):
        return None
    canvas = Image.new('L', (width, height), 0)
    ImageDraw.Draw(canvas).text(position, text, font=font, fill=255)
    return np.asarray(canvas, dtype=float) / 255


def fit_source(upright):
    gray = upright.mean(axis=2)
    low, high = np.percentile(gray, [10, 90])
    if high-low < 40:
        raise ValueError('Insufficient original glyph contrast')
    yy, xx = np.nonzero(gray < (low+high)/2)
    background = np.median(upright[gray >= high], axis=0)
    observed = np.clip(1-upright/background, 0, 1).mean(axis=2)
    best = None
    for size in range(24, 75):
        font = ImageFont.truetype(str(FONT), size)
        box = font.getbbox('31')
        x = round((xx.min()+xx.max()+1-box[0]-box[2])/2)
        y = round((yy.min()+yy.max()+1-box[1]-box[3])/2)
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                m = mask('31', size, (x+dx, y+dy), gray.shape)
                if m is None or not m.any():
                    continue
                contrast = float(np.clip((m*observed).sum()/(m*m).sum(), 0, 1))
                candidate = (float(np.mean((m*contrast-observed)**2)), size, x+dx, y+dy, contrast)
                if best is None or candidate < best:
                    best = candidate
    if best is None:
        raise ValueError('Original glyph does not fit the fixed source footprint')
    error, size, x, y, contrast = best
    return dict(original_literal='31', font_size=size, position=[x, y],
                ink_contrast=contrast, background_rgb=background.tolist(),
                normalized_pixel_mse=error, fit_uses_original_pixels_only=True,
                rotation='Exact90-degree transpose for source fit, inverse transpose for output')


def main():
    assert FONT.resolve().is_relative_to(ROOT / '.venv')
    ap = OUT / 'causal_pilot/source_reviews/mathvision_wild__114__photo__e00_v1.json'
    annotation = read_json(ap)
    policy_path = ROOT / annotation['source_value_policy']['path']
    assert sha(policy_path) == annotation['source_value_policy']['sha256']
    policy = read_json(policy_path)
    assert sha(ROOT / policy['implementation_path']) == policy['implementation_sha256']
    row = read_jsonl(OUT / 'cohort/benchmark_manifests/mathvision_wild_photo_native.jsonl')[5]
    assert row['event_id'] == annotation['event_id']
    asset = row['source_asset_identity'][0]
    with load_asset(asset) as im:
        native = np.array(im)
    assert native.shape == (3648, 1640, 3)
    box = annotation['sources']['T'][0]['pixels']
    x0, y0, x1, y1 = box
    upright = np.array(Image.fromarray(native[y0:y1, x0:x1]).transpose(Image.Transpose.ROTATE_90))
    fit = fit_source(upright)
    changed = numeric_replacement('31', lower='1', upper=None)
    assert changed == annotation['candidates']['target_semantic'] == '36'
    dest = OUT / 'causal_pilot/edit_bank/mathwild114_target_numeric_v1'
    if dest.exists():
        raise FileExistsError('Preserve existing source-control bank')
    pending, controls = {}, {}
    for kind, value in [('semantic', changed), ('sham', '31')]:
        name = 'T_' + kind
        m = mask(value, fit['font_size'], fit['position'], upright.shape[:2])
        if m is None:
            raise ValueError('Replacement clips; do not change the source-only fit')
        patch = np.rint(np.array(fit['background_rgb'])*(1-m[..., None]*fit['ink_contrast'])).astype(np.uint8)
        variant = native.copy()
        variant[y0:y1, x0:x1] = np.array(Image.fromarray(patch).transpose(Image.Transpose.ROTATE_270))
        pending[name] = variant
        controls[name] = dict(source='T', original='31', value=value, recipient=box,
            renderer_fit=fit, **validate_local_variant(native, variant, [box]), independently_reviewed=False)
    dest.mkdir(parents=True)
    for name, variant in pending.items():
        path = dest / (name + '.png')
        Image.fromarray(variant).save(path)
        with Image.open(path) as saved:
            assert np.array_equal(np.array(saved.convert('RGB')), variant)
        controls[name].update(path=str(path.relative_to(ROOT)), sha256=sha(path))
    dependencies = [ROOT / 'scripts/stage7a_bench/mathwild114_edit_bank_v2.py',
                    ROOT / 'scripts/stage7a_bench/local_edit_validation_v2.py']
    write_json(dest / 'candidate_manifest.json', dict(status='PIXEL_VALID_SEMANTICS_PENDING',
        event_id=row['event_id'], source_annotation_path=str(ap.relative_to(ROOT)),
        source_annotation_sha256=sha(ap), source_asset=asset,
        source_value_policy=annotation['source_value_policy'], controls=controls,
        font_path=str(FONT.relative_to(ROOT)), font_sha256=sha(FONT),
        dependency_sha256={str(p.relative_to(ROOT)): sha(p) for p in dependencies},
        unavailable_controls=dict(X='12->17 implies13, absent from unchanged answer choices'),
        causal_scores_used=False, pilot_selected=False, semantic_review_pending=True), freeze=True)
    print('TARGET_PAIR_PREPARED', fit, 'MANUAL_REVIEW_PENDING')


if __name__ == '__main__':
    main()
