"""Matched literal field edits; semantic validity still requires source review."""
import numpy as np
from PIL import ImageDraw, ImageFont


def render_text_pair(native, box, original, alternate, *, light_foreground=False):
    if original == alternate:
        raise ValueError('Semantic edit must differ from original')
    x0, y0, x1, y1 = map(int, box)
    if not (0 <= x0 < x1 <= native.width and 0 <= y0 < y1 <= native.height):
        raise ValueError('Invalid source box')
    image = np.asarray(native.convert('RGB'))
    region = image[y0:y1, x0:x1]
    brightness = region.mean(2)
    background_pixels = (brightness <= np.quantile(brightness,.2)) if light_foreground else (brightness >= np.quantile(brightness,.8))
    background = np.median(region[background_pixels], axis=0).astype('uint8')
    width, height = x1-x0, y1-y0
    strings = [original, alternate]
    for size in range(height, 3, -1):
        font = ImageFont.load_default(size=size)
        bounds = [font.getbbox(text) for text in strings]
        if all(b[2]-b[0] <= width-2 and b[3]-b[1] <= height-2 for b in bounds):
            break
    else:
        raise ValueError('Both strings must fit one legible matched source rectangle')
    left, top = min(b[0] for b in bounds), min(b[1] for b in bounds)
    bw, bh = max(b[2] for b in bounds)-left, max(b[3] for b in bounds)-top
    anchor = (x0+(width-bw)//2-left, y0+(height-bh)//2-top)
    mask = np.zeros(image.shape[:2], bool)
    mask[y0:y1, x0:x1] = True
    outputs = {}
    changes = {}
    for key, text in zip(['sham', 'semantic'], strings):
        out = native.convert('RGB').copy()
        draw = ImageDraw.Draw(out)
        draw.rectangle((x0, y0, x1-1, y1-1), fill=tuple(map(int, background)))
        draw.text(anchor, text, font=font, fill='white' if light_foreground else 'black')
        changed = np.any(np.asarray(out) != image, axis=2)
        if not changed.any() or (changed & ~mask).any():
            raise ValueError('Empty edit or drawing outside the source rectangle')
        outputs[key] = out
        changes[key] = int(changed.sum())
    if np.array_equal(np.asarray(outputs['sham']), np.asarray(outputs['semantic'])):
        raise ValueError('Semantic edit has no rendered distinction')
    return outputs, dict(roi=box, strings=strings, font_size=size, anchor=anchor,
                         background=background.tolist(), outside_roi_exact=True,
                         matched_font_anchor_background=True, changed_pixels=changes,
                         light_foreground=light_foreground, semantic_review='pending manual source/crop review')
