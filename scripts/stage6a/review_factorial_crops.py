"""Show authored C2 field rectangles for independent visual boundary checks."""
import json
from PIL import Image, ImageDraw
from scripts.stage6a.inventory import OUT
from scripts.stage6a.review_candidates import open_image


def main():
    rows=json.loads((OUT/'config/primary_c2_authored_semantics.json').read_text())
    pool={r['base_id']:r for r in map(json.loads,(OUT/'cohort/semantic_candidate_order.jsonl').read_text().splitlines())}
    for start in range(0,len(rows),8):
        chunk=list(rows.values())[start:start+8]
        sheet=Image.new('RGB',(1400,180*len(chunk)),'white');draw=ImageDraw.Draw(sheet)
        for i,row in enumerate(chunk):
            im=open_image(pool[row['base_id']])
            for j,key in enumerate(['roi','other_roi']):
                box=row[key];x,y,x1,y1=box
                cropbox=[max(0,x-15),max(0,y-15),min(im.width,x1+15),min(im.height,y1+15)]
                crop=im.crop(cropbox);d=ImageDraw.Draw(crop)
                d.rectangle((x-cropbox[0],y-cropbox[1],x1-cropbox[0]-1,y1-cropbox[1]-1),outline='red',width=1)
                scale=min(650/crop.width,125/crop.height)
                crop=crop.resize((round(crop.width*scale),round(crop.height*scale)))
                ox=j*700+10;oy=i*180
                draw.text((ox,oy+3),row['base_id']+' '+['T','X'][j]+' '+str(box),fill='black')
                draw.text((ox,oy+18),row['answers'][j],fill='black')
                sheet.paste(crop,(ox,oy+42))
        p=OUT/'review'/f'c2_primary_crops_{start:03d}.png';sheet.save(p);print(p)


if __name__=='__main__':main()
