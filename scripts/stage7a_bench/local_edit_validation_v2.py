"""Verify pixel locality of scientific controls; semantics require manual review."""
import hashlib

import numpy as np


def validate_local_variant(native, variant, boxes):
    if (native.shape != variant.shape or native.ndim != 3 or native.shape[2] != 3 or
            native.dtype != np.uint8 or variant.dtype != np.uint8):
        raise ValueError('Native RGB uint8 shape must be preserved')
    height, width = native.shape[:2]
    mask = np.zeros((height, width), dtype=bool)
    for box in boxes:
        if (len(box) != 4 or any(type(v) is not int for v in box) or
                not 0 <= box[0] < box[2] <= width or
                not 0 <= box[1] < box[3] <= height):
            raise ValueError('Invalid native-pixel edit box')
        x0, y0, x1, y1 = box
        mask[y0:y1, x0:x1] = True
    changed = np.any(native != variant, axis=2)
    outside = int(np.count_nonzero(changed & ~mask))
    if outside:
        raise ValueError('Control changed pixels outside its reviewed mask')
    count = int(np.count_nonzero(changed))
    if not count:
        raise ValueError('Rendered control is unchanged; not a matched editing sham')
    return dict(native_size=[width, height], changed_pixels=count,
        outside_mask_changed_pixels=outside, mask_pixels=int(mask.sum()),
        native_decoded_sha256=hashlib.sha256(native.tobytes()).hexdigest(),
        variant_decoded_sha256=hashlib.sha256(variant.tobytes()).hexdigest(),
        semantic_validity=None,
        scope='Pixel locality only; source identity, literal content, redundant encodings and sham comparability require independent review.')
