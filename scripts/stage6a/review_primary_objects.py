"""Pre-inference C3 target-mask/sham sheets and natural-negative image review."""
import argparse
import json
from PIL import Image,ImageDraw
from scripts.stage6a.inventory import OUT
from scripts.stage6a.review_candidates import open_image
from scripts.stage6a.build_object_candidates import polygon_mask
from visual_reasoning.stage6a.stimuli import apply_stress,translate_mask


def main():
    p=argparse.ArgumentParser();p.add_argument('--present',action='store_true');a=p.parse_args()
    rows=[r for r in map(json.loads,(OUT/'c3_object_stress/pope_manifest.jsonl').read_text().splitlines()) if r['phase']=='primary' and r['present']==a.present]
    chunk_size=4 if a.present else 12
    for start in range(0,len(rows),chunk_size):
        chunk=rows[start:start+chunk_size]
        sheet=Image.new('RGB',(1500,420*len(chunk) if a.present else 420*((len(chunk)+2)//3)),'white');draw=ImageDraw.Draw(sheet)
        for i,row in enumerate(chunk):
            im=open_image(row)
            if a.present:
                mask=polygon_mask(im.size,row['target_annotations']);s=row['sham_translation'];sham=translate_mask(mask,s['dx'],s['dy'])
                images=[im,apply_stress(im,mask,'mask'),apply_stress(im,sham,'mask')]
            else:images=[im]
            for j,image in enumerate(images):
                x=j*500 if a.present else (i%3)*500;y=i*420 if a.present else (i//3)*420
                image.thumbnail((490,360));sheet.paste(image,(x+5,y+50))
                draw.text((x+5,y+4),f"{start+i} {row['base_id']}",fill='black')
                draw.text((x+5,y+22),['native','all annotated target pixels masked','matched sham'][j] if a.present else 'POPE and COCO negative: '+row['category'],fill='black')
        path=OUT/f'review/c3_{"present" if a.present else "absent"}_{start:03d}.png';sheet.save(path)
    print('Created review sheets:',len(rows),'present=',a.present)


if __name__=='__main__':main()
