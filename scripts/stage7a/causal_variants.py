"""Apply the frozen availability manipulation equally to CF and render sham."""
import numpy as np
from PIL import Image
from scripts.stage7a.common import OUT, sha, write_json
from visual_reasoning.stage6a.stimuli import apply_stress


def fixed_prefix_variants(entry, native_rows):
    """Resolve frozen controls without inventing masks for absent objects."""
    row = entry['row']
    available, unavailable = [], {}
    for condition in entry['fixed_prefix_controls']:
        event_id = row['base_id'] + '__' + condition
        if event_id not in native_rows:
            original = native_rows.get(row['base_id'] + '__intact', {})
            absent_object_mask = (condition == 'mask' and row['cohort'] == 'C3'
                                  and row.get('present') is False
                                  and original.get('target_availability') == 'queried_object_absent')
            if not absent_object_mask:
                raise KeyError('Unexpected missing fixed-prefix control: ' + event_id)
            unavailable['fixed_' + condition] = dict(
                available=False, native_condition_id=event_id,
                reason='Frozen cohort has no target mask for an absent queried object')
        else:
            available.append((condition, native_rows[event_id]))
    return available, unavailable


def semantic_variant(row, source, kind, reviewed_sha256):
    if row['condition'] in ('no_image', 'unrelated'):
        raise ValueError('Original source is absent from this condition')
    if row['condition'] == 'mask' and source == 'T':
        raise ValueError('Semantic target pixels are erased by the full mask')
    if source not in row['fields'] or kind not in ('sham', 'semantic'):
        raise ValueError('Unreviewed semantic variant')
    assets = OUT / 'assets' / row['base_id']
    source_path = assets / f'condition__{source}_{kind}.png'
    assert sha(source_path) == reviewed_sha256, 'Semantic source changed after pixel review'
    image = Image.open(source_path).convert('RGB')
    condition = row['condition']
    if condition in ('strong', 'mask', 'sham_mask'):
        mask_role = 'I' if condition == 'sham_mask' else 'T'
        mask = np.asarray(Image.open(assets / f'roi_mask__{mask_role}.png')) > 0
        image = apply_stress(image, mask, 'mask' if condition == 'sham_mask' else condition)
    native = np.asarray(Image.open(row['image_path']).convert('RGB'))
    changed = np.any(np.asarray(image) != native, axis=-1)
    source_mask = np.asarray(Image.open(assets / f'roi_mask__{source}.png')) > 0
    assert not changed[~source_mask].any(), 'Variant changes pixels outside its semantic source'
    dest = OUT / 'causal_assets' / row['base_id'] / f'{condition}__{source}_{kind}.png'
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        assert np.array_equal(np.asarray(Image.open(dest)), np.asarray(image))
    else:
        image.save(dest)
    audit = dict(path=str(dest), sha256=sha(dest), reviewed_source_path=str(source_path),
                 reviewed_source_sha256=sha(source_path), native_image_sha256=sha(row['image_path']),
                 same_availability_manipulation=True, outside_source_exact=True,
                 changed_pixels=int(changed.sum()), condition=condition, source=source, kind=kind)
    write_json(dest.with_suffix('.json'), audit, freeze=True)
    return {**row, 'image_path': str(dest), 'image_sha256': audit['sha256']}, audit
