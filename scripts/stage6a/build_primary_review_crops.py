"""Materialize only candidate edit crops; no accepted membership or model calls."""
import argparse
import json
import numpy as np
from PIL import Image, ImageDraw
from scripts.stage6a.inventory import OUT
from scripts.stage6a.review_candidates import open_image
from visual_reasoning.stage5a.edits import numeric_edit


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--dataset', default='MathVerse')
    args = parser.parse_args()
    queue = {r['base_id']:r for r in map(json.loads,(OUT/'cohort/primary_c1_review_queue.jsonl').read_text().splitlines())}
    authored = json.loads((OUT/'config/primary_c1_authored_semantics.json').read_text())
    rows = [(k,r) for k,r in authored.items() if queue[k]['dataset']==args.dataset and not r.get('status','').startswith(('deferred','excluded'))]
    sheet = Image.new('RGB',(1200,180*len(rows)),'white'); draw=ImageDraw.Draw(sheet)
    report=[]
    for i,(key,review) in enumerate(rows):
        native=open_image(queue[key]); w,h=native.size
        roi=review.get('roi') or [round(v*(w if j%2==0 else h)) for j,v in enumerate(review['normalized_roi'])]
        fact={**queue[key]['proposed_target'],'roi':roi}
        draw.text((5,i*180+5),key+' '+str(roi)+' '+str(fact),fill='black')
        try:
            edits,audit=numeric_edit(native,fact)
            audit['roi']=roi; audit['base_id']=key; audit['status']='pending_visual_review'
            images=[native,edits['sham'],edits['semantic']]
            for j,im in enumerate(images):
                box=[max(0,roi[0]-15),max(0,roi[1]-15),min(w,roi[2]+15),min(h,roi[3]+15)]
                crop=im.crop(box);scale=min(350/crop.width,125/crop.height)
                crop=crop.resize((round(crop.width*scale),round(crop.height*scale)))
                sheet.paste(crop,(j*400+20,i*180+40))
                draw.text((j*400+20,i*180+160),['native','same-pipeline original','counterfactual'][j],fill='black')
        except ValueError as error:
            audit=dict(base_id=key,roi=roi,status='editability_failure',error=str(error))
            pad=max(15,round((roi[3]-roi[1])*.2))
            crop=native.crop((max(0,roi[0]-pad),max(0,roi[1]-pad),min(w,roi[2]+pad),min(h,roi[3]+pad)))
            scale=min(350/crop.width,120/crop.height)
            crop=crop.resize((round(crop.width*scale),round(crop.height*scale)))
            sheet.paste(crop,(20,i*180+40))
            draw.text((400,i*180+50),str(error),fill='red')
        report.append(audit)
    path=OUT/'review'/f'primary_{args.dataset}_edit_crops.png';sheet.save(path)
    for start in range(0,len(rows),10):
        sheet.crop((0,180*start,1200,min(sheet.height,180*(start+10)))).save(
            OUT/'review'/f'primary_{args.dataset}_edit_crops_{start:03d}.png')
    (OUT/'audit'/f'primary_{args.dataset}_edit_review.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps([r for r in report if r['status']=='editability_failure'],indent=2))


if __name__=='__main__':main()
