"""Conservative numeric-only edits; units and geometry outside the edit stay exact.

Component proposals are feasibility aids, never semantic validation. Every accepted
native/sham/counterfactual crop must subsequently receive a manual image review.
"""
import re
import numpy as np
from scipy.ndimage import label,find_objects
from PIL import Image,ImageDraw,ImageFont


def numeric_edit(native,fact):
    original=str(fact['value']);alternate=str(fact['counterfactual'])
    if not all(re.fullmatch(r'\d+(?:\.\d+)?',s) for s in (original,alternate)):
        raise ValueError('Only explicit unsigned decimal label edits are supported')
    image=np.asarray(native.convert('RGB'));height,width=image.shape[:2]
    rx,ry,rx1,ry1=fact.get('edit_roi',fact['roi'])
    if not (0<=rx<rx1<=width and 0<=ry<ry1<=height):raise ValueError('Invalid numeric review region')
    region=image[ry:ry1,rx:rx1];brightness=region.astype(float).mean(2)
    bright=brightness>=np.quantile(brightness,.8)
    background=np.median(region[bright],axis=0).astype(np.uint8)
    foreground=brightness<float(background.mean())-45
    labels,count=label(foreground,structure=np.ones((3,3),int));objects=find_objects(labels)
    edge=set(np.unique(np.concatenate((labels[0],labels[-1],labels[:,0],labels[:,-1]))))
    components=[]
    for index,slices in enumerate(objects,1):
        if index in edge or slices is None:continue
        yy,xx=slices;area=int((labels[slices]==index).sum())
        if area<2:continue
        components.append({'id':index,'box':[xx.start,yy.start,xx.stop,yy.stop],'area':area})
    components.sort(key=lambda c:(c['box'][0],c['box'][1]))
    needed=len(original)
    if len(components)<needed:raise ValueError(f'Only {len(components)} isolated components for {needed} numeric characters')
    chosen=components[:needed];selected={c['id'] for c in chosen}
    x0=max(0,min(c['box'][0] for c in chosen)-2);y0=max(0,min(c['box'][1] for c in chosen)-2)
    x1=min(region.shape[1],max(c['box'][2] for c in chosen)+2);y1=min(region.shape[0],max(c['box'][3] for c in chosen)+2)
    foreign=set(np.unique(labels[y0:y1,x0:x1]))-{0}-selected
    if foreign:raise ValueError('Numeric edit rectangle touches a protected/unselected component')
    box=[rx+x0,ry+y0,rx+x1,ry+y1];bw=x1-x0;bh=y1-y0
    for size in range(bh,3,-1):
        font=ImageFont.load_default(size=size);bounds=[font.getbbox(s) for s in (original,alternate)]
        if all(v[2]-v[0]<=bw-2 and v[3]-v[1]<=bh-2 for v in bounds):break
    else:raise ValueError('Both numeric candidates do not fit the same edit rectangle')
    left=min(v[0] for v in bounds);top=min(v[1] for v in bounds)
    w=max(v[2] for v in bounds)-left;h=max(v[3] for v in bounds)-top
    anchor=[box[0]+(bw-w)//2-left,box[1]+(bh-h)//2-top]
    outputs={}
    for key,text in [('sham',original),('semantic',alternate)]:
        out=native.convert('RGB').copy();draw=ImageDraw.Draw(out)
        draw.rectangle((box[0],box[1],box[2]-1,box[3]-1),fill=tuple(map(int,background)))
        draw.text(tuple(anchor),text,font=font,fill=(0,0,0));outputs[key]=out
    mask=np.zeros((height,width),bool);mask[box[1]:box[3],box[0]:box[2]]=True
    for out in outputs.values():
        changed=np.any(np.asarray(out)!=image,axis=2)
        assert changed.any() and not (changed & ~mask).any()
    if np.array_equal(np.asarray(outputs['sham']),np.asarray(outputs['semantic'])):
        raise ValueError('Sham and semantic images are equal')
    return outputs,{'edit_roi':box,'review_roi':fact['roi'],'component_review_roi':[rx,ry,rx1,ry1],
                    'components':components,'selected_component_ids':sorted(selected),'font_size':size,
                    'text_anchor':anchor,'background_color':background.tolist(),'original_rendered':original,
                    'counterfactual_rendered':alternate,'outside_numeric_edit_exact':True,
                    'shared_font_anchor_background':True,'manual_semantic_review':'pending'}
