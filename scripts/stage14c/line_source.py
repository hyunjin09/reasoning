"""Pixel-derived draft for simple two-segment line plots; requires visual QC."""
import numpy as np


def read_vertical_orders(image):
    rgb=np.asarray(image.convert('RGB'),dtype=float)
    red=(rgb[:,:,0]>120)&(rgb[:,:,0]>1.5*rgb[:,:,1])&(rgb[:,:,0]>1.5*rgb[:,:,2])
    blue=(rgb[:,:,2]>120)&(rgb[:,:,2]>1.5*rgb[:,:,1])&(rgb[:,:,2]>1.5*rgb[:,:,0])
    if min(red.sum(),blue.sum())<20:raise ValueError('Missing observed colored polyline')
    positions={};span=image.width-1
    # Sample just inside endpoints; central slice remains at the common bend.
    for name,mask in [('red',red),('blue',blue)]:
        ys=[]
        for fraction in [.01,.5,.99]:
            x=int(round(fraction*span));radius=max(1,int(.003*span))
            y,_=np.where(mask[:,max(0,x-radius):min(image.width,x+radius+1)])
            if not len(y):raise ValueError('Missing sampled endpoint/bend')
            ys.append(float(np.median(y)))
        positions[name]=ys
    gaps=np.array(positions['blue'])-positions['red']
    if np.any(np.abs(gaps)<.012*image.height):raise ValueError('Ambiguous order; manual source review required')
    return dict(orders=['above' if d<0 else 'below' for d in gaps],pixel_y_samples=positions,
                coordinate_origin='top-left',automated_source_draft=True,visual_QC_required=True)
