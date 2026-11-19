"""Create source crop sheets for explicit score-blind ROI validation."""
import argparse
from PIL import Image,ImageDraw,ImageFont
from scripts.stage5a.prepare import OUT,read_json,read_jsonl,write_json
p=argparse.ArgumentParser();p.add_argument('--offset',type=int,default=0);p.add_argument('--count',type=int,default=48);args=p.parse_args()
screen={r['base_problem_id']:r for r in reversed(read_jsonl(OUT/'cohort/prospective_screen_manifest.jsonl'))}
rows=[]
for path in sorted((OUT/'cohort/review').glob('manual_[0-9][0-9][0-9][0-9].json')):
 for record in read_json(path):
  for key,f in record['facts'].items():rows.append((path,record,key,f))
selected=rows[args.offset:args.offset+args.count]
if not selected:raise SystemExit('No sources in requested slice')
sheet=Image.new('RGB',(1080,150*((len(selected)+5)//6)),'#eeeeee');d=ImageDraw.Draw(sheet);font=ImageFont.load_default(size=13);manifest=[]
for i,(path,r,k,f) in enumerate(selected):
 x=i%6*180;y=i//6*150;box=f['roi'];source=screen[r['base']]['source_image']
 with Image.open(source) as im:
  native=im.convert('RGB');crop=native.crop(box);crop=crop.resize((max(1,int(crop.width*min(3,168/crop.width,100/crop.height))),max(1,int(crop.height*min(3,168/crop.width,100/crop.height)))))
 d.text((x+4,y+3),f"{args.offset+i} b{r['base']} {k}={f['value']}",fill='black',font=font);sheet.paste(crop,(x+5,y+25));d.text((x+4,y+130),str(box),fill='black',font=font)
 manifest.append({'index':args.offset+i,'base':r['base'],'source':k,'roi':box,'annotation_path':str(path),'image':source,'manual_roi_review':'pending'})
target=OUT/f'cohort/review/roi_{args.offset:04d}';sheet.save(str(target)+'.png');write_json(str(target)+'.json',manifest)
print({'total_sources':len(rows),'slice':[args.offset,args.offset+len(selected)]})
