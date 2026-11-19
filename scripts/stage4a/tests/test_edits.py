import numpy as np
from PIL import Image,ImageDraw
from visual_reasoning.stage4a.edits import render_factorial,validate_factorial


def test_factorial_edit_has_independent_pixels_and_detects_cross_contamination():
    native=Image.new('RGB',(200,80),'white')
    ImageDraw.Draw(native).text((10,20),'12',fill='black')
    ImageDraw.Draw(native).text((140,20),'34',fill='black')
    facts={'A':{'roi_xyxy':[8,15,60,50],'original_value':'12','counterfactual_value':'14'},
           'B':{'roi_xyxy':[138,15,190,50],'original_value':'34','counterfactual_value':'36'}}
    arrays,specs=render_factorial(native,facts)
    assert validate_factorial(arrays,facts)['passed']
    arrays['AO'][20,150]=[255,0,0]
    assert not validate_factorial(arrays,facts)['passed']


def test_overlapping_source_pixels_are_rejected():
    native=Image.new('RGB',(40,40),'white')
    fact={'roi_xyxy':[4,4,30,30],'original_value':'1','counterfactual_value':'2'}
    import pytest
    with pytest.raises(ValueError,match='overlap'):
        render_factorial(native,{'A':fact,'B':fact})


def test_render_box_protects_a_diagram_stroke_inside_larger_roi():
    native=Image.new('RGB',(160,70),'white');d=ImageDraw.Draw(native)
    d.line((20,0,20,69),fill='black',width=2)
    d.text((38,23),'12',fill='black');d.text((110,23),'34',fill='black')
    facts={'A':{'roi_xyxy':[15,10,75,60],'render_box_xyxy':[38,23,59,36],
                'original_value':'12','counterfactual_value':'14','renderer':'preserve_crossing_strokes'},
           'B':{'roi_xyxy':[100,10,155,60],'original_value':'34','counterfactual_value':'36'}}
    arrays,_=render_factorial(native,facts)
    assert validate_factorial(arrays,facts)['passed']
    for condition in arrays:assert np.array_equal(arrays[condition][:,20],np.asarray(native)[:,20])
    changed=np.any(arrays['AO']!=np.asarray(native),axis=-1)
    allowed=np.zeros(changed.shape,dtype=bool);allowed[23:36,38:59]=True
    assert not np.any(changed & ~allowed)
    arrays['AO'][25,20]=[255,255,255]
    arrays['AB'][25,20]=[255,255,255]
    assert not validate_factorial(arrays,facts)['passed']
