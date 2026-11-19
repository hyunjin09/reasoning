import numpy as np
import pytest
from PIL import Image
from visual_reasoning.stage6a.stimuli import rect_mask, apply_stress, translate_mask


def test_target_mask_preserves_all_outside_pixels():
    raw=np.arange(30*40*3,dtype=np.uint8).reshape(30,40,3)
    mask=rect_mask((40,30),(10,8,18,15))
    changed=np.asarray(apply_stress(Image.fromarray(raw),mask,'mask'))
    assert np.array_equal(changed[~mask],raw[~mask])
    assert np.all(changed[mask]==127)


def test_sham_translation_preserves_area_and_shape_without_wrap():
    mask=rect_mask((40,30),(10,8,18,15));sham=translate_mask(mask,20,10)
    assert sham.sum()==mask.sum()==56
    assert not (sham & mask).any()
    with pytest.raises(ValueError,match='outside'):
        translate_mask(mask,35,0)


def test_polygon_like_mask_and_noop_are_exact():
    raw=np.arange(30*40*3,dtype=np.uint8).reshape(30,40,3)
    mask=np.zeros((30,40),bool);mask[3:8,3:8]=True;mask[8,4]=True
    native=Image.fromarray(raw)
    assert np.array_equal(np.asarray(apply_stress(native,mask,'intact')),raw)
    for condition in ('mild','strong'):
        out=np.asarray(apply_stress(native,mask,condition))
        assert np.array_equal(out[~mask],raw[~mask])
        assert not np.array_equal(out[mask],raw[mask])


def test_invalid_rect_rejected():
    with pytest.raises(ValueError):rect_mask((40,30),(39,10,41,20))


def test_sham_image_and_binary_mask_have_distinct_asset_paths():
    from pathlib import Path
    from visual_reasoning.stage6a.stimuli import asset_path
    root=Path('outputs/stage6a/assets/example')
    names=[asset_path(root,'condition',n) for n in ('mask','sham_mask','intact')]
    names.extend(asset_path(root,'roi_mask',n) for n in ('target','sham'))
    assert len(set(names))==5
    with pytest.raises(ValueError):asset_path(root,'unknown','sham')
