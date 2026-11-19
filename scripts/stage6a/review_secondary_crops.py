"""Check secondary-source rectangles and display their native pixels for review."""
import argparse
import json
from PIL import Image,ImageDraw
from scripts.stage6a.inventory import OUT
from scripts.stage6a.prepare_candidates import write


def intersects(a,b):return max(a[0],b[0])<min(a[2],b[2]) and max(a[1],b[1])<min(a[3],b[3])


def main():
    p=argparse.ArgumentParser();p.add_argument('--remaining-strata',action='store_true');p.add_argument('--pending',action='store_true');a=p.parse_args()
    stem='c1_secondary_remaining' if a.remaining_strata else 'c1_secondary'
    assert not a.pending or a.remaining_strata
    definitions=json.loads((OUT/(f'review/{stem}_pending.json' if a.pending else f'config/{stem}_sources.json')).read_text())
    if a.pending:stem+='_pending'
    order='c1_secondary_remaining_review_order' if a.remaining_strata else 'c1_secondary_source_review_order'
    bases={r['base_id']:r for r in map(json.loads,(OUT/f'cohort/{order}.jsonl').read_text().splitlines())}
    tiles=[];checks=[]
    for key,record in definitions.items():
        row=bases[key];image=Image.open(row['image_path']).convert('RGB');rects=[row['target']['roi']]
        for source in record['sources']:
            roi=source['roi'];assert 0<=roi[0]<roi[2]<=image.width and 0<=roi[1]<roi[3]<=image.height
            assert not any(intersects(roi,prior) for prior in rects),(key,roi,rects)
            rects.append(roi);crop=image.crop(roi)
            tiles.append((key,source,crop));checks.append(dict(base_id=key,source_id=source['source_id'],roi=roi,bounds_and_disjointness='PASS',visual_crop_review=record['status']))
    for start in range(0,len(tiles),12):
        chunk=tiles[start:start+12];sheet=Image.new('RGB',(1200,185*((len(chunk)+2)//3)),'white');draw=ImageDraw.Draw(sheet)
        for i,(key,source,crop) in enumerate(chunk):
            ox=i%3*400;oy=i//3*185;draw.text((ox+8,oy+3),key+' '+source['source_id']+'='+source['value'],fill='black')
            draw.text((ox+8,oy+20),source['entity'][:48],fill='black')
            factor=min(4,380/crop.width,135/crop.height);crop=crop.resize((int(crop.width*factor),int(crop.height*factor)))
            sheet.paste(crop,(ox+8,oy+45))
        path=OUT/f'review/{stem}_crops_{start:03d}.png';sheet.save(path);print(path)
    write(OUT/f'audit/{stem}_roi_checks.jsonl',checks)


if __name__=='__main__':main()
