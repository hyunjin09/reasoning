"""Full-resolution coordinate overlays for manual ROI review; originals unchanged."""
import argparse
from PIL import Image,ImageDraw,ImageFont
from scripts.stage5a.prepare import OUT,read_jsonl
p=argparse.ArgumentParser();p.add_argument('bases',nargs='+');a=p.parse_args()
screen={r['base_problem_id']:r for r in reversed(read_jsonl(OUT/'cohort/prospective_screen_manifest.jsonl'))}
for b in a.bases:
 with Image.open(screen[b]['source_image']) as im:
  im=im.convert('RGB');scale=min(3,1000/im.width,900/im.height)
  grid=im.resize((round(im.width*scale),round(im.height*scale)))
  d=ImageDraw.Draw(grid);font=ImageFont.load_default(size=14)
  step=50 if max(im.size)<1000 else 200
  for x in range(0,im.width,step):
   u=round(x*scale);d.line((u,0,u,grid.height),fill='#bbbbbb',width=1);d.text((u+1,0),str(x),fill='red',font=font)
  for y in range(0,im.height,step):
   v=round(y*scale);d.line((0,v,grid.width,v),fill='#bbbbbb',width=1);d.text((0,v+1),str(y),fill='red',font=font)
  grid.save(OUT/f'cohort/review/{b}_coordinate_review.png')
