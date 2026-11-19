"""Prepare matched matrix number/color edits; manual semantics stay pending.

The original source supplies neighboring numeric colors. Both variants repaint
the same full cell and use the same source-fitted glyph renderer. No model
output or causal score chooses the replacement, color or rendering parameters.
"""
import numpy as np
from PIL import Image

from scripts.stage7a.common import ROOT, read_json, read_jsonl, sha, write_json
from scripts.stage7a_bench.image_inputs_v2 import load_asset
from scripts.stage7a_bench.local_edit_validation_v2 import validate_local_variant
from scripts.stage7a_bench.source_value_policy_v2 import numeric_replacement
from scripts.stage7a_bench.charxiv1690_edit_bank_v2 import FONT, fit_original, glyph_mask

OUT = ROOT/'outputs/stage7a_bench_v2'


def main():
    annotation_path = OUT/'causal_pilot/source_reviews/charxiv__images%2F1968.jpg__image_present__e00_v1.json'
    assert sha(annotation_path) == 'c0f551076bd79e92dea59220fb5ef282881d9f9f8463488edfd1f86fa774e217'
    annotation = read_json(annotation_path)
    diagnostic_path = OUT/'audit/charxiv_093_native_color_feasibility.json'
    assert sha(diagnostic_path) == '8354347f8c5d772eae8d2c5f874427963be3b38e824fa81e211272def3dff8f8'
    diagnostic = read_json(diagnostic_path)
    policy_path = ROOT/annotation['source_value_policy']['path']
    assert sha(policy_path) == annotation['source_value_policy']['sha256']
    policy = read_json(policy_path)
    assert sha(ROOT/policy['implementation_path']) == policy['implementation_sha256']
    assert FONT.resolve().is_relative_to(ROOT/'.venv')
    row = next(r for r in read_jsonl(OUT/'cohort/benchmark_manifests/charxiv_image_present_native.jsonl')
               if r['event_id'] == annotation['event_id'])
    with load_asset(row['image_assets'][0]) as image:
        native = np.asarray(image)
    assert native.shape == (928,1024,3)
    dest = OUT/'causal_pilot/edit_bank/charxiv1968_numeric_color_v1'
    if dest.exists():
        raise FileExistsError('Preserve the existing control bank')
    pending, controls = {}, {}
    for source, original, glyph_box in [('T','26.5',[63,24,110,47]), ('X','28.1',[63,78,110,101])]:
        box = annotation['sources'][source][0]['pixels']
        x0,y0,x1,y1 = box
        u0,v0,u1,v1 = glyph_box
        assert x0 <= u0 < u1 <= x1 and y0 <= v0 < v1 <= y1
        background = np.array(diagnostic['background_median_rgb'][original], dtype=float)
        patch = native[v0:v1,u0:u1].astype(float)
        # Express white glyph ink over its native colored background as the
        # black-on-white observation expected by the existing source-only fit.
        alpha = np.clip(((patch-background)/(255-background)).mean(axis=2),0,1)
        monochrome = np.repeat(np.rint(255*(1-alpha))[:,:,None],3,axis=2).astype(np.uint8)
        fit = fit_original(monochrome, original)
        changed = numeric_replacement(original, lower=None, upper=None)
        assert changed == annotation['candidates']['target_semantic' if source == 'T' else 'alternative_semantic']
        for kind,value in [('semantic',changed),('sham',original)]:
            color = np.array(diagnostic['proposed_semantic_backgrounds'][source] if kind == 'semantic'
                             else background, dtype=float)
            mask = glyph_mask(value, patch.shape[:2], fit['font_size'], fit['position'])
            if mask is None:
                raise ValueError('Replacement clips the source-fitted glyph region')
            variant = native.copy()
            variant[y0:y1,x0:x1] = np.rint(color).astype(np.uint8)
            glyph = color+mask[:,:,None]*fit['ink_contrast']*(255-color)
            variant[v0:v1,u0:u1] = np.rint(glyph).clip(0,255).astype(np.uint8)
            name = source+'_'+kind
            pending[name] = variant
            controls[name] = dict(source=source, original=original, value=value, recipient=box,
                glyph_recipient=glyph_box, renderer_fit=fit, background_rgb=color.tolist(),
                rendering='Full cell repaint and source-fitted white glyphs; identical operation for semantic and sham',
                qualification='Homogenizes JPEG texture and reconstructs font edges. Target26.0 uses native same-value donor color; '
                              'alternative28.6 interpolates native28.5/29.4 colors. Both color/value encodings change together; '
                              'the original colorbar and other cells stay intact. Mandatory sham-effect gate remains unchanged.',
                **validate_local_variant(native,variant,[box]), independently_reviewed=False)
    dest.mkdir(parents=True)
    for name, variant in pending.items():
        path = dest/(name+'.png')
        Image.fromarray(variant).save(path)
        with Image.open(path) as saved:
            assert np.array_equal(np.array(saved.convert('RGB')),variant)
        controls[name].update(path=str(path.relative_to(ROOT)),sha256=sha(path))
    dependencies = [ROOT/'scripts/stage7a_bench/charxiv1968_edit_bank_v2.py',
                    ROOT/'scripts/stage7a_bench/charxiv1690_edit_bank_v2.py',
                    ROOT/'scripts/stage7a_bench/local_edit_validation_v2.py',diagnostic_path]
    write_json(dest/'candidate_manifest.json',dict(status='PIXEL_VALID_SEMANTICS_PENDING',
        event_id=row['event_id'],source_annotation_path=str(annotation_path.relative_to(ROOT)),
        source_annotation_sha256=sha(annotation_path),source_asset=row['image_assets'][0],
        source_value_policy=annotation['source_value_policy'],controls=controls,
        font_path=str(FONT.relative_to(ROOT)),font_sha256=sha(FONT),
        dependency_sha256={str(p.relative_to(ROOT)):sha(p) for p in dependencies},
        causal_scores_used=False,pilot_selected=False,semantic_review_pending=True),freeze=True)
    print('MATRIX_NUMERIC_COLOR_CANDIDATES',len(controls),'MANUAL_REVIEW_PENDING')


if __name__ == '__main__':
    main()
