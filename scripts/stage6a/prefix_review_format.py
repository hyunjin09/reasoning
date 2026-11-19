"""Small serialization helpers for explicitly authored semantic review decisions."""


def labels(demands):
    return [dict(demanded_sources=sorted(set(s)),explicit_visual_claim_sources=[],source_claims=[],
        unresolved=False,note='Localized numeric-source claims and demand are assigned explicitly. A named-source lookup can demand that source before a readout; generic formulas, intermediate-only algebra and unspecific task restatements need not do so. This is not an exhaustive geometry-state label.') for s in demands]


def claim(rows,index,source,quote,truth='CORRECT',note='Source-linked numeric assertion reviewed against the source image.'):
    row=rows[index];row['explicit_visual_claim_sources'].append(source)
    row['source_claims'].append(dict(source_id=source,quote=quote,local_visual_correctness=truth,
        numeric_label_correctness='CORRECT',note=note))
