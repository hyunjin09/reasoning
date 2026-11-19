"""Read-only-source document review sheets with native pixel coordinate ticks."""
import argparse
import json
from PIL import Image, ImageDraw
from scripts.stage6a.inventory import OUT
from scripts.stage6a.review_candidates import open_image


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--start', type=int, required=True)
    p.add_argument('--count', type=int, default=2)
    a = p.parse_args()
    rows = [json.loads(s) for s in (OUT/'cohort/semantic_candidate_order.jsonl').read_text().splitlines()]
    rows = [r for r in rows if r['dataset']=='DocVQA'][a.start:a.start+a.count]
    sheet = Image.new('RGB', (850*len(rows), 1250), 'white')
    draw = ImageDraw.Draw(sheet)
    for i, row in enumerate(rows):
        native = open_image(row); w,h = native.size
        native.thumbnail((790, 1150)); ox,oy = 850*i+35,55
        sheet.paste(native,(ox,oy))
        draw.text((ox,5),f"{a.start+i} {row['base_id']} native {w}x{h}",fill='black')
        for j in range(11):
            x=ox+round(native.width*j/10);y=oy+round(native.height*j/10)
            draw.text((x-8,oy-18),str(round(w*j/10)),fill='red')
            draw.text((ox-32,y),str(round(h*j/10)),fill='red')
        draw.text((ox,1210),row['question'][:90],fill='black')
        draw.text((ox,1225),'Source answer '+str(row['answer'])[:100],fill='black')
    dest=OUT/'review'/f'doc_fields_{a.start:04d}.png';sheet.save(dest);print(dest)


if __name__=='__main__':main()
