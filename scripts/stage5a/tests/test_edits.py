import numpy as np
import pytest
from PIL import Image,ImageDraw,ImageFont
from visual_reasoning.stage5a.edits import numeric_edit


def test_numeric_proposal_keeps_units_and_geometry_exact_and_matches_sham_pipeline():
    native=Image.new('RGB',(180,70),'white');d=ImageDraw.Draw(native);font=ImageFont.load_default(size=24)
    d.text((20,12),'12 cm',font=font,fill='black');d.line((0,55,179,55),fill='blue',width=3)
    edited,audit=numeric_edit(native,{'value':'12','counterfactual':'14','roi':[12,5,125,48]})
    assert audit['edit_roi'][2]<60
    for im in edited.values():
        assert np.array_equal(np.asarray(native)[:,60:],np.asarray(im)[:,60:])
        assert np.array_equal(np.asarray(native)[50:],np.asarray(im)[50:])
    assert not np.array_equal(np.asarray(edited['semantic']),np.asarray(edited['sham']))


def test_unisolated_numeric_label_is_unavailable_instead_of_erasing_geometry():
    native=Image.new('RGB',(80,50),'white');d=ImageDraw.Draw(native)
    d.line((0,20,79,20),fill='black',width=3)
    with pytest.raises(ValueError):numeric_edit(native,{'value':'12','counterfactual':'14','roi':[0,0,80,50]})
