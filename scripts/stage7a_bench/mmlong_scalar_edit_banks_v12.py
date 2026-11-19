"""Render pre-reviewed numeric PDF-page controls and matched glyph shams.

Only literal recipients change; the rest of each complete page is preserved.
This produces candidates, never semantic approval or causal eligibility.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from scripts.stage7a.common import ROOT, read_json, sha, write_json
from scripts.stage7a_bench.image_inputs_v2 import describe, load_asset
from scripts.stage7a_bench.local_edit_validation_v2 import validate_local_variant

OUT = ROOT / 'outputs/stage7a_bench_v2'


def paint(native, box, text, *, white, font_path):
    x0, y0, x1, y1 = box
    patch = native[y0:y1, x0:x1].astype(float)
    edges = np.concatenate((patch[:, :2], patch[:, -2:]), axis=1)
    background = np.median(edges, axis=1)[:, None, :]
    if white:
        # Directly viewed green bar; ROI stays inside its flat interior.
        background = np.broadcast_to(np.array([0.,176.,80.]), (patch.shape[0],1,3))
    foreground = np.full(3, 255. if white else 0.)
    direction = foreground-background
    denominator = (direction**2).sum(axis=-1)
    alpha = np.divide(((patch-background)*direction).sum(axis=-1), denominator,
        out=np.zeros(patch.shape[:2]), where=denominator > 1)
    yy, xx = np.nonzero(alpha > .3)
    if not len(xx):
        raise ValueError('Original literal ink was not located')
    a, b, c, d = int(xx.min()), int(yy.min()), int(xx.max()+1), int(yy.max()+1)
    font = ImageFont.truetype(str(font_path), 96)
    bounds = font.getbbox(text)
    mask = Image.new('L', (bounds[2]-bounds[0], bounds[3]-bounds[1]))
    ImageDraw.Draw(mask).text((-bounds[0], -bounds[1]), text, font=font, fill=255)
    new_alpha = np.zeros(patch.shape[:2])
    new_alpha[b:d, a:c] = np.array(mask.resize((c-a, d-b), Image.Resampling.LANCZOS))/255
    result = native.copy()
    result[y0:y1, x0:x1] = np.rint(background+new_alpha[..., None]*direction).clip(0, 255).astype(np.uint8)
    return result, dict(ink_bounds=[a,b,c,d], foreground=foreground.tolist(),
        row_background_rgb=background[:,0,:].tolist(), font_sha256=sha(font_path),
        renderer='Identical serif/sans glyph renderer and native ink bounds for semantic and sham')


def main():
    packet = read_json(OUT / 'audit/mmlong_completion_packet01_compile_v11.json')['entries']
    tasks = [
        (172, 0, 7, dict(X=[416,422,438,433]), True),
        (172, 2, 8, dict(T=[706,518,743,535], X=[775,518,813,535]), False),
    ]
    for index, ci, page, recipients, white in tasks:
        reference = next(r for r in packet if r['native_index']==index and r['claim_index']==ci)
        entry = read_json(ROOT / reference['path'])
        annotation = entry['source_annotation']
        source_path = ROOT / annotation['source_sheet']['path']
        asset = describe(dict(kind='file', path=str(source_path), slot=f'page_{page}'), source_path.read_bytes())
        native = np.array(load_asset(asset))
        font_name = 'DejaVuSans.ttf' if white else 'DejaVuSerif.ttf'
        font_path = ROOT / '.venv/lib/python3.12/site-packages/matplotlib/mpl-data/fonts/ttf' / font_name
        dest = OUT / f'causal_pilot/edit_bank/mmlong{index:03}_e{ci:02}_scalar_v12'
        if dest.exists():
            raise FileExistsError('Preserve existing source-control bank')
        controls, pending = {}, {}
        for role, box in recipients.items():
            original = annotation['candidates']['correct' if role=='T' else 'alternative_original']
            replacement = annotation['candidates']['target_semantic' if role=='T' else 'alternative_semantic']
            for kind, literal in [('semantic', replacement), ('sham', original)]:
                rendered = literal.removesuffix('%')
                variant, fit = paint(native, box, rendered, white=white, font_path=font_path)
                name = role+'_'+kind
                pending[name] = variant
                controls[name] = dict(source=role, original=original, value=literal,
                    rendered_literal=rendered, recipient=box, renderer_fit=fit,
                    **validate_local_variant(native, variant, [box]), independently_reviewed=False)
        dest.mkdir(parents=True)
        for name, variant in pending.items():
            path = dest / (name+'.png')
            Image.fromarray(variant).save(path)
            controls[name].update(path=str(path.relative_to(ROOT)), sha256=sha(path))
        write_json(dest / 'candidate_manifest.json', dict(status='PIXEL_VALID_SEMANTICS_PENDING',
            event_id=entry['event_id'], source_annotation_path=entry['annotation_path'],
            source_annotation_sha256=sha(ROOT / entry['annotation_path']), source_asset=asset,
            source_value_policy=annotation.get('source_value_policy'), controls=controls,
            renderer=dict(path=str(__import__('pathlib').Path(__file__).relative_to(ROOT)), sha256=sha(__file__)),
            unavailable_controls={role:'Not supplied; see pre-score source/context validity notes.'
                for role in ('T','X') if role not in recipients},
            causal_scores_used=False, pilot_selected=False, semantic_review_pending=True), freeze=True)
        print(index, ci, 'prepared', len(controls), 'controls; manual review pending', flush=True)


if __name__ == '__main__':
    main()
