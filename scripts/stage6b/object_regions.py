"""Project saved COCO segmentation geometry into each native image token grid."""
from collections import defaultdict
import numpy as np
from pycocotools import mask as coco_mask
from visual_reasoning.stage3b7.roi import map_changed_pixels_to_tokens


def category_footprints(regions,input_meta):
    if not input_meta['visual_token_indices']:return {},[]
    width,height=input_meta['image_size'];_,rows,cols=input_meta['visual_mapping']['merged_grid_shape']
    masks={};audit=[]
    for region in regions:
        seg=region['segmentation']
        if isinstance(seg,list):rle=coco_mask.merge(coco_mask.frPyObjects(seg,height,width))
        elif isinstance(seg['counts'],list):rle=coco_mask.frPyObjects(seg,height,width)
        else:rle=seg
        pixels=coco_mask.decode(rle).astype(bool)
        assert pixels.shape==(height,width)
        category=region['category'];masks.setdefault(category,np.zeros((height,width),dtype=bool))
        masks[category]|=pixels
    groups={}
    for category,pixels in sorted(masks.items()):
        local=map_changed_pixels_to_tokens(pixels,merged_rows=rows,merged_cols=cols)
        yy,xx=np.nonzero(pixels)
        direct=sorted(set((yy*rows//height*cols+xx*cols//width).tolist()))
        assert local==direct
        if not local:continue
        groups['COCO_CATEGORY:'+category]=[input_meta['visual_token_indices'][i] for i in local]
        audit.append({'category':category,'mask_pixels':int(pixels.sum()),'visual_tokens':len(local),
            'direct_projection_exact':True,'source':'Saved source-native COCO polygon/RLE union, no attention selection'})
    return groups,audit
