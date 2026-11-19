"""Render pre-specified document numeral controls for independent visual review."""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from scripts.stage7a.common import ROOT, read_json, sha, write_json
from scripts.stage7a_bench.image_inputs_v2 import describe, load_asset
from scripts.stage7a_bench.local_edit_validation_v2 import validate_local_variant

OUT = ROOT / 'outputs/stage7a_bench_v2'


def paint(native, box, literal, font_path, colored=False):
    x0,y0,x1,y1 = box
    patch = native[y0:y1,x0:x1].astype(float)
    background = np.median(np.concatenate((patch[:,:2],patch[:,-2:]),axis=1),axis=1)[:,None,:]
    contrast = np.linalg.norm(patch-background,axis=-1)
    if colored:
        foreground = np.median(patch[contrast >= np.quantile(contrast,.88)],axis=0)
    else:
        foreground = np.zeros(3)
    direction = foreground-background
    denominator = (direction**2).sum(axis=-1)
    alpha = np.divide(((patch-background)*direction).sum(axis=-1),denominator,
        out=np.zeros(patch.shape[:2]),where=denominator>1)
    yy,xx = np.nonzero(alpha>.3)
    if not len(xx):
        raise ValueError('No original numeral ink')
    a,b,c,d = int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)
    font = ImageFont.truetype(str(font_path),96)
    bounds = font.getbbox(literal)
    mask = Image.new('L',(bounds[2]-bounds[0],bounds[3]-bounds[1]))
    ImageDraw.Draw(mask).text((-bounds[0],-bounds[1]),literal,font=font,fill=255)
    new_alpha = np.zeros(patch.shape[:2])
    new_alpha[b:d,a:c] = np.asarray(mask.resize((c-a,d-b),Image.Resampling.LANCZOS))/255
    result = native.copy()
    result[y0:y1,x0:x1] = np.rint(background+new_alpha[...,None]*direction).clip(0,255).astype(np.uint8)
    return result,dict(ink_bounds=[a,b,c,d],foreground=foreground.tolist(),font_sha256=sha(font_path),
                      rendering='Identical source-derived ink bounds, color, background and font for semantic/sham pair')


def main():
    pool = read_json(OUT / 'causal_pilot/prepared_candidate_indices/mmlong_pool53_precontrols_v15.json')['entries']
    # Recipient footprints and counterfactual values were manually specified
    # before this renderer or any causal scores; no event mining here.
    tasks = [(0,2,('T','X'),'DejaVuSans.ttf',False,' MB/s'),
             (36,0,('T',),'DejaVuSerif.ttf',False,''),
             (128,0,('T',),'DejaVuSans.ttf',True,''),
             (146,2,('T','X'),'DejaVuSerif.ttf',False,''),
             (150,2,('T','X'),'DejaVuSans.ttf',False,''),
             (191,2,('T',),'DejaVuSerif-Bold.ttf',False,''),
             (195,0,('T','X'),'DejaVuSans.ttf',True,'')]
    for n,ci,roles,font_name,colored,suffix in tasks:
        ref = next(e for e in pool if e['native_index']==n and e['claim_index']==ci)
        entry = read_json(ROOT / ref['path'])
        annotation = entry['source_annotation']
        source_path = ROOT / annotation['source_sheet']['path']
        slot = annotation['sources']['T'][0]['slot']
        asset = describe(dict(kind='file',path=str(source_path),slot=slot),source_path.read_bytes())
        native = np.asarray(load_asset(asset))
        font_path = ROOT / '.venv/lib/python3.12/site-packages/matplotlib/mpl-data/fonts/ttf' / font_name
        dest = OUT / f'causal_pilot/edit_bank/mmlong{n:03}_e{ci:02}_numeric_v15'
        if dest.exists():
            raise FileExistsError(dest)
        controls,images = {},{}
        for role in roles:
            source = annotation['sources'][role]
            assert len(source)==1 and source[0]['slot']==slot
            box = source[0]['pixels']
            original = annotation['candidates']['correct' if role=='T' else 'alternative_original']
            changed = annotation['candidates']['target_semantic' if role=='T' else 'alternative_semantic']
            for kind,literal in [('semantic',changed),('sham',original)]:
                name = role+'_'+kind
                variant,fit = paint(native,box,literal+suffix,font_path,colored=colored)
                images[name] = variant
                controls[name] = dict(source=role,original=original,value=literal,
                    rendered_literal=literal+suffix,recipient=box,renderer_fit=fit,
                    **validate_local_variant(native,variant,[box]),independently_reviewed=False)
        dest.mkdir(parents=True)
        for name,variant in images.items():
            path = dest/(name+'.png')
            Image.fromarray(variant).save(path)
            controls[name].update(path=str(path.relative_to(ROOT)),sha256=sha(path))
        write_json(dest/'candidate_manifest.json',dict(status='PIXEL_VALID_SEMANTICS_PENDING',
            event_id=entry['event_id'],source_annotation_path=entry['annotation_path'],
            source_annotation_sha256=sha(ROOT/entry['annotation_path']),source_asset=asset,
            source_value_policy=annotation.get('source_value_policy'),controls=controls,
            renderer=dict(path=str(__import__('pathlib').Path(__file__).relative_to(ROOT)),sha256=sha(__file__)),
            unavailable_controls={r:'No valid reviewed semantic pair; see source-context note.' for r in ('T','X') if r not in roles},
            causal_scores_used=False,pilot_selected=False,semantic_review_pending=True),freeze=True)
        # Native and paired edits enlarged together for visual review, with
        # source fields in their original coordinates retained in full PNGs.
        panels=[]
        for role in roles:
            x0,y0,x1,y1=annotation['sources'][role][0]['pixels']
            crop_box=(max(0,x0-5),max(0,y0-5),min(native.shape[1],x1+5),min(native.shape[0],y1+5))
            for name,arr in [('native',native),(role+'_semantic',images[role+'_semantic']),(role+'_sham',images[role+'_sham'])]:
                crop=Image.fromarray(arr).crop(crop_box)
                scale=min(5,550/crop.width)
                crop=crop.resize((int(crop.width*scale),int(crop.height*scale)))
                panel=Image.new('RGB',(600,max(95,crop.height+30)),'white')
                ImageDraw.Draw(panel).text((5,5),f'{n} {role} {name}',fill='black')
                panel.paste(crop,(5,25));panels.append(panel)
        sheet=Image.new('RGB',(600,sum(i.height for i in panels)),'white');y=0
        for panel in panels:sheet.paste(panel,(0,y));y+=panel.height
        sheet.save(dest/'literal_review_sheet.png')
        print(n,ci,len(controls),'rendered; manual semantic review pending',flush=True)


if __name__=='__main__':
    main()
