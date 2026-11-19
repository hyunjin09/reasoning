"""One pre-score diagnostic: clipped glyphs versus glyph/geometry connections."""
import argparse
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label,find_objects
from scripts.stage4a.prepare_config import OUT,read_jsonl,write_json
from visual_reasoning.stage3a.edits import _text_background
from visual_reasoning.stage3b9.edits import edge_connected_foreground_mask


def main():
    records=[];panels=[]
    parser=argparse.ArgumentParser()
    parser.add_argument('--bases',default='7,132,757,352,356,358,359,360,378,19,263')
    parser.add_argument('--output-name',default='components')
    args=parser.parse_args();wanted=set(args.bases.split(','))
    for item in read_jsonl(OUT/'cohort/manual_annotations.jsonl'):
        if item['base_problem_id'] not in wanted:continue
        image=Image.open(item['source_image']).convert('RGB');array=np.asarray(image)
        for x,fact in item['facts'].items():
            box=fact['roi_xyxy'];x0,y0,x1,y1=box;bg=np.array(_text_background(image,tuple(box),fact))
            margin=max(15,(y1-y0)//2);left=max(0,x0-margin);top=max(0,y0-margin);right=min(image.width,x1+margin);bottom=min(image.height,y1+margin)
            crop=array[top:bottom,left:right];foreground=np.linalg.norm(crop.astype(float)-bg,axis=-1)>=24
            labels,count=label(foreground,structure=np.ones((3,3)));components=[]
            for i,slices in enumerate(find_objects(labels),1):
                if slices is None:continue
                sy,sx=slices;cb=[left+sx.start,top+sy.start,left+sx.stop,top+sy.stop]
                if cb[0]>=x1 or cb[2]<=x0 or cb[1]>=y1 or cb[3]<=y0:continue
                mask=labels==i;area=int(mask.sum());ys,xs=np.nonzero(mask)
                intersect=int(((xs+left>=x0)&(xs+left<x1)&(ys+top>=y0)&(ys+top<y1)).sum())
                components.append({'box':cb,'area':area,'area_inside_roi':intersect,
                    'fully_enclosed':cb[0]>x0 and cb[1]>y0 and cb[2]<x1 and cb[3]<y1,
                    'touches_diagnostic_crop_edge':sx.start==0 or sy.start==0 or sx.stop==crop.shape[1] or sy.stop==crop.shape[0]})
            region=array[y0:y1,x0:x1];keep=edge_connected_foreground_mask(region,bg)
            ink=np.linalg.norm(region.astype(float)-bg,axis=-1)>=24
            record={'base_problem_id':item['base_problem_id'],'fact':x,'value':fact['original_value'],'roi_xyxy':box,
                    'retained_foreground_fraction':float(keep.sum()/max(1,ink.sum())),'components':components}
            records.append(record)
            panel=Image.fromarray(crop.copy());draw=ImageDraw.Draw(panel);draw.rectangle([x0-left,y0-top,x1-left-1,y1-top-1],outline='red')
            panel=panel.resize((min(350,panel.width*4),min(240,panel.height*4)))
            panels.append((f"{item['base_problem_id']}{x} {fact['original_value']} retained{record['retained_foreground_fraction']:.2f}",panel))
    out=OUT/'cohort/render_diagnostic';out.mkdir(exist_ok=True)
    write_json(out/(args.output_name+'.json'),{'causal_scores_available':False,'records':records})
    canvas=Image.new('RGB',(1400,((len(panels)+3)//4)*280),'white');draw=ImageDraw.Draw(canvas)
    for i,(title,panel) in enumerate(panels):
        x=i%4*350;y=i//4*280;draw.text((x+4,y+3),title,fill='black');canvas.paste(panel,(x,y+30))
    canvas.save(out/(args.output_name+'.png'))
    for r in records:
        if r['retained_foreground_fraction']>.25:print(r)


if __name__=='__main__':main()
