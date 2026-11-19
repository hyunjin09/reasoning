"""Map reviewed native-pixel rectangles using the unchanged Stage7A grid rule.

Geometry alone never certifies source semantics, edit validity or readout truth.
Repeated presentations of the same image slot are all mapped; distinct slots
and redundant document pages still require explicit source annotation.
"""
from itertools import combinations


def map_source_boxes(meta, sources):
    if set(sources) - {'T', 'X', 'X2', 'I'}:
        raise ValueError('Only explicitly annotated T/X/X2/I sources; G is derived')
    visual = meta['visual_token_indices']
    if any(type(p) is not int or p < 0 for p in visual) or len(set(visual)) != len(visual):
        raise ValueError('Native visual-token positions must be unique nonnegative integers')
    if not visual:
        if sources:
            raise ValueError('No visual input exists for the requested source boxes')
        return dict(groups={}, token_overlaps={}, box_audits={},
            target_alternative_token_disjoint=None, semantic_identifiability_certified=False)
    if meta.get('no_image'):
        raise ValueError('No-image metadata contains visual tokens')
    segments = meta.get('visual_images') or [dict(slot='image_1',
        image_size=meta['image_size'], visual_mapping=meta['visual_mapping'],
        visual_token_indices=visual, decoded_image_sha256=meta.get('decoded_image_sha256'))]
    if [p for s in segments for p in s['visual_token_indices']] != visual:
        raise ValueError('Image segments do not exactly partition native visual positions')
    slots = {}
    for segment in segments:
        size = segment['image_size']
        shape = segment['visual_mapping']['merged_grid_shape']
        if (len(size) != 2 or len(shape) != 3 or
            any(type(v) is not int or v <= 0 for v in [*size, *shape]) or shape[0] != 1):
            raise ValueError('Expected static-image pixel dimensions and merged grid')
        if len(segment['visual_token_indices']) != shape[1] * shape[2]:
            raise ValueError('Image token count does not match its merged grid')
        previous = slots.setdefault(segment['slot'], [])
        if previous and any(segment.get(k) != previous[0].get(k)
                            for k in ('image_size', 'decoded_image_sha256')):
            raise ValueError('Repeated physical image slot has inconsistent identity')
        previous.append(segment)
    groups, audits = {}, {}
    for role, boxes in sources.items():
        if not boxes:
            raise ValueError('Omit unavailable roles; do not provide an empty source')
        positions, audits[role] = set(), []
        for box in boxes:
            matches = slots.get(box['slot'])
            if not matches:
                raise ValueError('Source box references an absent image/page slot')
            bounds = box['pixels']
            if len(bounds) != 4 or any(type(v) is not int for v in bounds):
                raise ValueError('Source rectangle requires four native integer pixel coordinates')
            x0, y0, x1, y1 = bounds
            per_occurrence = []
            for segment in matches:
                width, height = segment['image_size']
                if box['source_size'] != [width, height]:
                    raise ValueError('Reviewed source size differs from native input')
                if not (0 <= x0 < x1 <= width and 0 <= y0 < y1 <= height):
                    raise ValueError('Empty or out-of-bounds source rectangle')
                _, rows, cols = segment['visual_mapping']['merged_grid_shape']
                # Exact closed pixel support of [x0,x1) x [y0,y1), equivalent
                # to map_changed_pixels_to_tokens without a full-image mask.
                local = [r * cols + c
                    for r in range(y0 * rows // height, (y1 - 1) * rows // height + 1)
                    for c in range(x0 * cols // width, (x1 - 1) * cols // width + 1)]
                absolute = [segment['visual_token_indices'][i] for i in local]
                positions.update(absolute)
                per_occurrence.append(dict(local_tokens=local, absolute_tokens=absolute))
            audits[role].append(dict(slot=box['slot'], pixels=bounds,
                source_size=box['source_size'], matched_occurrences=len(matches),
                occurrences=per_occurrence))
        groups[role] = sorted(positions)
    overlaps = {a+'_'+b: sorted(set(groups[a]) & set(groups[b]))
                for a, b in combinations(sorted(groups), 2)}
    disjoint = not bool(set(groups['T']) & set(groups['X'])) if 'T' in groups and 'X' in groups else None
    return dict(groups={**groups, 'G': visual}, token_overlaps=overlaps, box_audits=audits,
        target_alternative_token_disjoint=disjoint, semantic_identifiability_certified=False,
        mapping_rule='Native pixels map by floor(pixel_coordinate * merged_cells / native_size), identical to Stage7A.',
        interpretation='Token overlap blocks independent-source claims even when pixel boxes are disjoint. Missing sources stay absent. Geometry does not establish semantic independence.',
        causal_or_passive_scores_used=False)
