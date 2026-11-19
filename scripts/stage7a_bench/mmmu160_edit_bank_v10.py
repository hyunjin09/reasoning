"""Prepare fixed numeric controls for the reviewed Mexico/Nigeria table.

Both variants use the same serif renderer and original ink bounds. Full-image
review must certify literals and task validity before this bank can be used.
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from scripts.stage7a.common import ROOT, read_json, read_jsonl, sha, write_json
from scripts.stage7a_bench.image_inputs_v2 import load_asset
from scripts.stage7a_bench.local_edit_validation_v2 import validate_local_variant
from scripts.stage7a_bench.mathwild216_label_edit_bank_v2 import extract_original
from scripts.stage7a_bench.source_value_policy_v2 import numeric_replacement

OUT = ROOT / 'outputs/stage7a_bench_v2'


def main():
    ap = OUT / 'causal_pilot/source_reviews/mmmu_pro__test_Economics_17__image_present__e02_completion_v10.json'
    annotation = read_json(ap)
    row = read_jsonl(OUT / 'cohort/benchmark_manifests/mmmu_pro_image_present_native.jsonl')[160]
    asset = row['image_assets'][0]
    native = np.array(load_asset(asset))
    font_path = ROOT / '.venv/lib/python3.12/site-packages/matplotlib/mpl-data/fonts/ttf/DejaVuSerif.ttf'
    font = ImageFont.truetype(str(font_path), 96)
    dest = OUT / 'causal_pilot/edit_bank/mmmu160_workers_v10'
    if dest.exists():
        raise FileExistsError('Preserve existing bank')
    controls, pending = {}, {}
    for role, original in [('T', '18'), ('X', '10')]:
        box = annotation['sources'][role][0]['pixels']
        x0, y0, x1, y1 = box
        _, fit = extract_original(native[y0:y1, x0:x1])
        a, b, c, d = fit['ink_bounds']
        replacement = numeric_replacement(original, lower='0', upper=None)
        for kind, value in [('semantic', replacement), ('sham', original)]:
            bounds = font.getbbox(value)
            mask = Image.new('L', (bounds[2]-bounds[0], bounds[3]-bounds[1]))
            ImageDraw.Draw(mask).text((-bounds[0], -bounds[1]), value, font=font, fill=255)
            ink = np.array(mask.resize((c-a, d-b), Image.Resampling.LANCZOS))/255
            alpha = np.zeros((y1-y0, x1-x0))
            alpha[b:d, a:c] = ink
            variant = native.copy()
            variant[y0:y1, x0:x1] = np.rint(np.array(fit['background_rgb'])*(1-alpha[..., None])).astype(np.uint8)
            name = role+'_'+kind
            pending[name] = variant
            controls[name] = dict(source=role, original=original, value=value,
                recipient=box, renderer_fit=fit, renderer_font_sha256=sha(font_path),
                **validate_local_variant(native, variant, [box]), independently_reviewed=False)
    dest.mkdir(parents=True)
    for name, variant in pending.items():
        path = dest / (name+'.png')
        Image.fromarray(variant).save(path)
        controls[name].update(path=str(path.relative_to(ROOT)), sha256=sha(path))
    write_json(dest / 'candidate_manifest.json', dict(status='PIXEL_VALID_SEMANTICS_PENDING',
        event_id=row['event_id'], source_annotation_path=str(ap.relative_to(ROOT)),
        source_annotation_sha256=sha(ap), source_asset=asset,
        source_value_policy=annotation['source_value_policy'], controls=controls,
        renderer=dict(path=str(Path(__file__).relative_to(ROOT)), sha256=sha(__file__),
            note='Same allowed project-local serif font for semantic and sham; original ink bounds and background. Typeface matching requires direct review.'),
        unavailable_controls={}, causal_scores_used=False, pilot_selected=False,
        semantic_review_pending=True), freeze=True)


if __name__ == '__main__':
    main()
