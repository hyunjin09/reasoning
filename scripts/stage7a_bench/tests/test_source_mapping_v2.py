import numpy as np
import pytest

from scripts.stage7a_bench.source_mapping_v2 import map_source_boxes
from visual_reasoning.stage3b7.roi import map_changed_pixels_to_tokens


def segment(slot, start, size=(13, 11), grid=(3, 4)):
    return dict(slot=slot, image_size=list(size),
        visual_mapping={'merged_grid_shape':[1,*grid]},
        visual_token_indices=list(range(start,start+grid[0]*grid[1])))


def metadata(*segments):
    return dict(no_image=False, visual_images=list(segments),
        visual_token_indices=[p for s in segments for p in s['visual_token_indices']])


def box(slot, bounds, size=(13,11)):
    return dict(slot=slot, pixels=bounds, source_size=list(size))


def test_rectangle_mapping_equals_original_pixel_mask_rule_at_odd_sizes():
    meta=metadata(segment('image_1',10))
    for bounds in [[0,0,13,11],[1,2,7,8],[12,10,13,11],[3,3,4,4]]:
        mask=np.zeros((11,13),bool)
        x0,y0,x1,y1=bounds
        mask[y0:y1,x0:x1]=True
        expected=map_changed_pixels_to_tokens(mask,merged_rows=3,merged_cols=4)
        result=map_source_boxes(meta,{'T':[box('image_1',bounds)]})
        assert result['groups']['T']==[10+i for i in expected]


def test_multiple_images_and_document_pages_use_their_absolute_positions():
    meta=metadata(segment('page_1',10),segment('page_8',70))
    result=map_source_boxes(meta,{'T':[box('page_8',[0,0,1,1])],
                                 'X':[box('page_1',[0,0,1,1])]})
    assert result['groups']['T']==[70] and result['groups']['X']==[10]
    assert result['target_alternative_token_disjoint'] is True
    assert result['groups']['G']==meta['visual_token_indices']


def test_repeated_same_image_slot_maps_every_occurrence():
    meta=metadata(segment('image_1',10),segment('image_1',70))
    result=map_source_boxes(meta,{'T':[box('image_1',[0,0,1,1])]})
    assert result['groups']['T']==[10,70]
    assert result['box_audits']['T'][0]['matched_occurrences']==2


def test_disjoint_pixels_can_share_a_visual_token_and_block_separation():
    meta=metadata(segment('image_1',10))
    result=map_source_boxes(meta,{'T':[box('image_1',[0,0,1,1])],
                                 'X':[box('image_1',[1,0,2,1])]})
    assert result['target_alternative_token_disjoint'] is False
    assert result['token_overlaps']['T_X']==[10]
    assert result['semantic_identifiability_certified'] is False


def test_missing_slot_wrong_size_invalid_boxes_and_global_override_rejected():
    meta=metadata(segment('image_1',10))
    for source in [box('image_2',[0,0,1,1]),box('image_1',[0,0,1,1],(12,11)),
                   box('image_1',[-1,0,1,1]),box('image_1',[0,0,0,1]),
                   box('image_1',[0,0,14,1]),box('image_1',[0.,0,1,1])]:
        with pytest.raises(ValueError): map_source_boxes(meta,{'T':[source]})
    with pytest.raises(ValueError): map_source_boxes(meta,{'G':[box('image_1',[0,0,1,1])]})


def test_text_only_has_no_fabricated_global_or_target_source():
    meta=dict(no_image=True,visual_token_indices=[])
    assert map_source_boxes(meta,{})['groups']=={}
    with pytest.raises(ValueError): map_source_boxes(meta,{'T':[box('image_1',[0,0,1,1])]})


def test_canonical_single_image_metadata_and_missing_target_preserved():
    one=segment('image_1',10)
    meta={k:v for k,v in one.items() if k!='slot'}
    result=map_source_boxes(meta,{'X':[box('image_1',[0,0,1,1])]})
    assert set(result['groups'])=={'X','G'}
    assert result['target_alternative_token_disjoint'] is None
