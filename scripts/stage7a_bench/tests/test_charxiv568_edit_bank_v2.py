import numpy as np
import pytest

from scripts.stage7a_bench.charxiv568_edit_bank_v2 import transplant_black_glyph


def test_same_opacity_survives_a_different_cell_color_with_exact_outside_pixels():
    native = np.full((10, 20, 3), [240, 180, 120], dtype=np.uint8)
    native[:, 10:] = [100, 150, 200]
    native[3:7, 3:7] = [120, 90, 60]  # Half-opacity black ink.
    native[4, 4] = 0  # Opaque core, as in the reviewed raster glyphs.
    changed, audit = transplant_black_glyph(native, [1, 1, 9, 9], [11, 1, 19, 9])
    expected = np.broadcast_to([50, 75, 100], (4, 4, 3)).copy()
    expected[1, 1] = 0
    assert np.array_equal(changed[3:7, 13:17], expected)
    assert np.array_equal(changed[:, :11], native[:, :11])
    assert np.array_equal(changed[:, 19:], native[:, 19:])
    assert np.array_equal(changed[[0, 9]], native[[0, 9]])
    assert audit['recipient_background_rgb'] == [100, 150, 200]


def test_unequal_glyph_shapes_and_empty_donor_are_rejected():
    native = np.full((10, 20, 3), 240, dtype=np.uint8)
    with pytest.raises(ValueError, match='dimensions'):
        transplant_black_glyph(native, [1, 1, 9, 9], [11, 1, 18, 9])
    with pytest.raises(ValueError, match='dark glyph'):
        transplant_black_glyph(native, [1, 1, 9, 9], [11, 1, 19, 9])
