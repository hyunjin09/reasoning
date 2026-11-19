import numpy as np
import pytest
from PIL import Image, ImageDraw, ImageFont
from visual_reasoning.stage7a.edits import render_text_pair


def test_comma_and_decimal_source_edit_preserves_other_field_and_table_rules():
    image = Image.new('RGB', (240, 110), 'white')
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=18)
    draw.text((12, 12), '5,936', fill='black', font=font)
    draw.text((130, 12), '419.00', fill='black', font=font)
    draw.line((0, 50, 239, 50), fill='blue', width=2)
    box = [8, 8, 100, 40]
    images, audit = render_text_pair(image, box, '5,936', '17,100')
    for changed in images.values():
        assert np.array_equal(np.asarray(changed)[:, 100:], np.asarray(image)[:, 100:])
        assert np.array_equal(np.asarray(changed)[40:], np.asarray(image)[40:])
    assert audit['strings'] == ['5,936', '17,100']
    assert not np.array_equal(np.asarray(images['sham']), np.asarray(images['semantic']))


def test_invalid_or_unrenderable_source_is_rejected():
    image = Image.new('RGB', (20, 20), 'white')
    with pytest.raises(ValueError):
        render_text_pair(image, [-1, 2, 10, 10], '1', '2')
    with pytest.raises(ValueError):
        render_text_pair(image, [2, 2, 4, 4], '1111111', '2222222')


def test_semantic_control_cannot_equal_sham():
    with pytest.raises(ValueError):
        render_text_pair(Image.new('RGB', (30, 30), 'white'), [3, 3, 27, 27], '5', '5')


def test_light_text_on_dark_document_preserves_polarity():
    native = Image.new('RGB', (180, 50), '#222222')
    ImageDraw.Draw(native).text((10, 8), '877-7260', fill='white', font=ImageFont.load_default(size=20))
    outputs, audit = render_text_pair(native, [7, 5, 150, 35], '877-7260', '877-7261', light_foreground=True)
    assert max(audit['background']) < 50
    for view in outputs.values():
        assert np.asarray(view)[8:33, 10:145].max() > 230
