"""Source-only D1 sheets in frozen manifest order; no model outcomes read."""
import math
from PIL import Image,ImageDraw
from scripts.stage14c.common import *
from scripts.stage14c.input_adapter import source_image

def main():
    tasks=[t for t in all_tasks('D1') if t['model_key']=='I'];assert len(tasks)==300
    dest=ROOT/'source/D1_source_sheets';dest.mkdir(exist_ok=True)
    manifest=[]
    for start in range(0,len(tasks),6):
        group=tasks[start:start+6];canvas=Image.new('RGB',(1800,math.ceil(len(group)/3)*650),'white');d=ImageDraw.Draw(canvas)
        for j,t in enumerate(group):
            ref=t['image_reference']
            if 'path' in ref:
                assert sha(ref['path'])==t['image_sha256'];im=Image.open(ref['path']);im.load()
            else:im=source_image(t)
            im=im.convert('RGB');im.thumbnail((590,600));x=j%3*600;y=j//3*650
            canvas.paste(im,(x,y+40));d.text((x+3,y+4),f"{start+j}: {t['item_id']}",fill='black')
            manifest.append(dict(index=start+j,task_id=t['task_id'],family_id=t['family_id'],image_reference=ref,image_sha256=t['image_sha256'],sheet=f'sheet_{start:03d}.png'))
        p=dest/f'sheet_{start:03d}.png';assert not p.exists();canvas.save(p)
    save(dest/'manifest.json',dict(at=now(),source_only=True,rows=manifest,code_sha256=sha(__file__)))
if __name__=='__main__':main()
