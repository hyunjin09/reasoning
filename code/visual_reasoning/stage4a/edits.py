"""Controlled independent two-label factorial for the Stage4A scientific assay."""
from decimal import Decimal
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from visual_reasoning.stage3a.edits import _render,_checked_roi,_text_background
from visual_reasoning.stage3b9.edits import render_preserving_crossing_strokes,edge_connected_foreground_mask

CONDITIONS=('OO','AO','OB','AB','A_sham','B_sham')


def surface(value):
    return format(Decimal(str(value)).normalize(),'f')


def masks_for(facts,shape):
    height,width=shape[:2];masks={}
    for x in ['A','B']:
        x0,y0,x1,y1=_checked_roi(facts[x]['roi_xyxy'],width,height)
        masks[x]=np.zeros((height,width),dtype=bool);masks[x][y0:y1,x0:x1]=True
    if np.any(masks['A'] & masks['B']):raise ValueError('A/B source pixels overlap')
    return masks


def fit_spec(fact):
    rx,ry,rx1,ry1=fact['roi_xyxy']
    x0,y0,x1,y1=fact.get('render_box_xyxy',fact['roi_xyxy']);width=x1-x0;height=y1-y0
    if not (rx<=x0<x1<=rx1 and ry<=y0<y1<=ry1):raise ValueError('Render box escapes source ROI')
    strings=[fact.get('render_prefix','')+surface(fact[k])+fact.get('render_suffix','') for k in ['original_value','counterfactual_value']]
    for size in range(int(fact.get('font_size',height)),3,-1):
        font=ImageFont.load_default(size=size);boxes=[font.getbbox(t) for t in strings]
        if all(b[2]-b[0]<=width-2 and b[3]-b[1]<=height-2 for b in boxes):break
    else:raise ValueError('Label does not fit declared edit ROI')
    # Same font and anchor for semantic and sham; fit both before rendering.
    left=min(b[0] for b in boxes);top=min(b[1] for b in boxes)
    bw=max(b[2] for b in boxes)-left;bh=max(b[3] for b in boxes)-top
    return {**fact,'font_size':size,'text_anchor':[x0-rx+(width-bw)//2-left,y0-ry+(height-bh)//2-top],
            'background_mode':'roi_bright_median'}


def render_factorial(native,facts):
    original=np.asarray(native.convert('RGB')).copy();masks=masks_for(facts,original.shape)
    specs={x:fit_spec(facts[x]) for x in ['A','B']}
    images={'OO':original}
    for x,condition in [('A','AO'),('B','OB')]:
        for name,key in [(condition,'counterfactual_value'),(x+'_sham','original_value')]:
            spec=specs[x];text=facts[x].get('render_prefix','')+surface(facts[x][key])+facts[x].get('render_suffix','')
            if fact_renderer:=spec.get('renderer'):
                if fact_renderer!='preserve_crossing_strokes':raise ValueError(fact_renderer)
                rendered=render_preserving_crossing_strokes(native,text,roi_xyxy=spec['roi_xyxy'],
                           text_anchor=spec['text_anchor'],font_size=spec['font_size'])
            else:rendered=_render(native,text,spec)
            images[name]=np.asarray(rendered).copy()
    images['AB']=original.copy()
    for x,condition in [('A','AO'),('B','OB')]:images['AB'][masks[x]]=images[condition][masks[x]]
    return images,specs


def validate_factorial(arrays,facts):
    if set(arrays)!=set(CONDITIONS):raise ValueError('Incorrect factorial conditions')
    if len({a.shape for a in arrays.values()})!=1:return {'passed':False,'reason':'shape mismatch'}
    native=arrays['OO'];masks=masks_for(facts,native.shape);checks={};diffs={}
    for name,target in [('AO','A'),('OB','B'),('A_sham','A'),('B_sham','B')]:
        diff=np.any(native!=arrays[name],axis=-1)
        checks[name+'_outside_exact']=not np.any(diff & ~masks[target])
        diffs[name]=int(diff.sum());checks[name+'_changed']=diffs[name]>0
        if facts[target].get('renderer')=='preserve_crossing_strokes':
            box=facts[target]['roi_xyxy'];x0,y0,x1,y1=box
            region=native[y0:y1,x0:x1]
            bg=_text_background(Image.fromarray(native),tuple(box),facts[target])
            keep=edge_connected_foreground_mask(region,bg)
            checks[name+'_protected_strokes_exact']=np.array_equal(region[keep],arrays[name][y0:y1,x0:x1][keep])
    union=masks['A']|masks['B']
    checks['AB_outside_union_exact']=np.array_equal(native[~union],arrays['AB'][~union])
    checks['AB_A_equals_AO']=np.array_equal(arrays['AB'][masks['A']],arrays['AO'][masks['A']])
    checks['AB_B_equals_OB']=np.array_equal(arrays['AB'][masks['B']],arrays['OB'][masks['B']])
    checks['AO_differs_from_A_sham']=not np.array_equal(arrays['AO'],arrays['A_sham'])
    checks['OB_differs_from_B_sham']=not np.array_equal(arrays['OB'],arrays['B_sham'])
    return {'passed':all(checks.values()),'checks':{k:bool(v) for k,v in checks.items()},'changed_pixels':diffs}


def review_sheet(arrays,facts,path):
    width=260;height=360;sheet=Image.new('RGB',(width*6,height),'white');draw=ImageDraw.Draw(sheet)
    for i,name in enumerate(CONDITIONS):
        image=Image.fromarray(arrays[name]);small=image.copy();small.thumbnail((250,210))
        x=i*width;draw.text((x+5,4),name,fill='black');sheet.paste(small,(x+5,25))
        for j,fact in enumerate(['A','B']):
            crop=image.crop(facts[fact]['roi_xyxy']);crop.thumbnail((110,100))
            scale=min(4,110/max(crop.size));crop=crop.resize((round(crop.width*scale),round(crop.height*scale)))
            draw.text((x+5+j*125,242),fact,fill='black');sheet.paste(crop,(x+5+j*125,265))
    sheet.save(path)
