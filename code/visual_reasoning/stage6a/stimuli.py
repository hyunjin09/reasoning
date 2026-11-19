"""Deterministic, auditable image manipulations with exact outside-mask isolation."""
import numpy as np
from PIL import Image


def asset_path(directory, kind, name):
    if kind not in ('condition','roi_mask') or '/' in name or '\\' in name:
        raise ValueError('Invalid image asset namespace')
    return directory / f'{kind}__{name}.png'


def rect_mask(size, box):
    width,height=size;x0,y0,x1,y1=map(int,box)
    if not (0<=x0<x1<=width and 0<=y0<y1<=height):
        raise ValueError('Invalid rectangle')
    mask=np.zeros((height,width),bool);mask[y0:y1,x0:x1]=True
    return mask


def translate_mask(mask, dx, dy):
    y,x=np.nonzero(mask);xx=x+int(dx);yy=y+int(dy)
    if not len(x) or xx.min()<0 or yy.min()<0 or xx.max()>=mask.shape[1] or yy.max()>=mask.shape[0]:
        raise ValueError('Translated mask falls outside image')
    result=np.zeros_like(mask);result[yy,xx]=True
    return result


def apply_stress(image, mask, condition, fill=(127,127,127)):
    raw=np.asarray(image.convert('RGB'));result=raw.copy()
    if mask.shape!=raw.shape[:2] or not mask.any():raise ValueError('Invalid image mask')
    if condition=='intact':return Image.fromarray(result)
    if condition not in ('mild','strong','mask'):raise ValueError(condition)
    # Contrast attenuation is confined to the exact target mask; full mask has
    # zero dependence on original target pixels. Same operation applies to sham.
    strength={'mild':0.55,'strong':0.12,'mask':0.0}[condition]
    result[mask]=np.rint(strength*raw[mask]+(1-strength)*np.asarray(fill)).astype(np.uint8)
    return Image.fromarray(result)
