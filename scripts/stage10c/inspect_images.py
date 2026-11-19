"""Read-only scientific contact sheet of frozen source and control patches."""
import sys,io,base64
from PIL import Image,ImageDraw
from scripts.stage10c.common import ROOT,load
rows=load(ROOT/'stage10c_frozen_candidate_split.json')['rows'];controls={r['trajectory_id']:r for r in load(ROOT/'audit/roi_control_draft.json')['rows']}
start=int(sys.argv[1]);canvas=Image.new('RGB',(1500,1200),'white');d=ImageDraw.Draw(canvas)
for j,r in enumerate(rows[start:start+6]):
 im=Image.open(r['corpus']['image']).convert('RGB');im.thumbnail((485,535))
 x=(j%3)*500;y=(j//3)*600;canvas.paste(im,(x,y+45));d.text((x+5,y+5),r['trajectory_id']+' '+r['split'],fill='black')
 c=controls[r['trajectory_id']];t,h,w=c['grid']
 for key,color in [('control_indices','blue'),('target_indices','red')]:
  indices=c[key];xx=[i%w for i in indices];yy=[i//w for i in indices]
  box=(x+min(xx)/w*im.width,y+45+min(yy)/h*im.height,x+(max(xx)+1)/w*im.width,y+45+(max(yy)+1)/h*im.height)
  d.rectangle(box,outline=color,width=2)
 d.text((x+5,y+585),'Red=target; Blue=control bounding box',fill='black')
b=io.BytesIO();canvas.save(b,format='PNG');print(base64.b64encode(b.getvalue()).decode())
