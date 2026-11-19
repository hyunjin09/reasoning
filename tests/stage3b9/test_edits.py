import numpy as np
from PIL import Image, ImageDraw

from visual_reasoning.stage3b9.edits import (
    changed_mask_from_conditions,
    edge_connected_foreground_mask,
    render_preserving_crossing_strokes,
)


def test_edge_connected_mask_keeps_crossing_line_but_not_enclosed_glyph():
    region = np.full((20, 40, 3), 255, dtype=np.uint8)
    region[9:11, :, :] = 0
    region[3:7, 17:23, :] = 0
    keep = edge_connected_foreground_mask(region, (255, 255, 255))
    assert keep[9:11].all()
    assert not keep[3:7, 17:23].any()


def test_render_is_exact_outside_roi_and_preserves_crossing_stroke():
    source = Image.new("RGB", (100, 60), "white")
    draw = ImageDraw.Draw(source)
    draw.line((0, 30, 99, 30), fill="black", width=2)
    draw.rectangle((42, 15, 48, 22), fill="black")
    result = render_preserving_crossing_strokes(
        source,
        "7",
        roi_xyxy=(30, 10, 70, 45),
        text_anchor=(12, 2),
        font_size=14,
    )
    before = np.asarray(source)
    after = np.asarray(result)
    outside = np.ones((60, 100), dtype=bool)
    outside[10:45, 30:70] = False
    assert np.array_equal(before[outside], after[outside])
    assert np.array_equal(before[30:32, 30:70], after[30:32, 30:70])
    assert not np.array_equal(before[15:23, 42:49], after[15:23, 42:49])


def test_changed_mask_supports_dynamic_condition_names():
    original = np.zeros((3, 4, 3), dtype=np.uint8)
    first = original.copy()
    second = original.copy()
    first[1, 2] = 255
    second[2, 3] = 128
    mask = changed_mask_from_conditions(
        {"O": original, "C1": first, "C2_sham": second}, original_condition="O"
    )
    expected = np.zeros((3, 4), dtype=bool)
    expected[1, 2] = True
    expected[2, 3] = True
    assert np.array_equal(mask, expected)
