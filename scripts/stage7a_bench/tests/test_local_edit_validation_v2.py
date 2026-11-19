from copy import deepcopy

import numpy as np
import pytest

from scripts.stage7a_bench.local_edit_validation_v2 import validate_local_variant


def fixture():
    native = np.full((12, 16, 3), 220, dtype=np.uint8)
    variant = native.copy()
    variant[4:7, 5:8] = 30
    return native, variant, [4, 3, 9, 8]


def test_reports_changed_pixels_and_retains_native_dimensions():
    native, variant, box = fixture()
    report = validate_local_variant(native, variant, [box])
    assert report['changed_pixels'] == 9
    assert report['outside_mask_changed_pixels'] == 0
    assert report['native_size'] == [16, 12]
    assert report['semantic_validity'] is None


def test_one_outside_pixel_invalidates_entire_control():
    native, variant, box = fixture()
    variant[0, 0, 0] -= 1
    with pytest.raises(ValueError, match='outside'):
        validate_local_variant(native, variant, [box])


def test_noop_cannot_be_claimed_as_a_rendered_sham():
    native, _, box = fixture()
    with pytest.raises(ValueError, match='unchanged'):
        validate_local_variant(native, native.copy(), [box])


def test_shape_change_rejected_before_pixel_comparison():
    native, variant, box = fixture()
    with pytest.raises(ValueError, match='shape'):
        validate_local_variant(native, variant[:10], [box])


@pytest.mark.parametrize('box', [[-1, 0, 4, 5], [4, 4, 4, 7], [0, 0, 17, 12], [0.5, 0, 4, 4]])
def test_invalid_native_pixel_mask_rejected(box):
    native, variant, _ = fixture()
    with pytest.raises(ValueError, match='box'):
        validate_local_variant(native, variant, [box])


def test_inputs_are_never_modified():
    native, variant, box = fixture()
    originals = deepcopy((native, variant))
    validate_local_variant(native, variant, [box])
    assert np.array_equal(native, originals[0]) and np.array_equal(variant, originals[1])
