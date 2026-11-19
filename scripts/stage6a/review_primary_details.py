"""Fuller pre-score review sheets, with normalized coordinate ticks for ROI authoring."""
import argparse
import json
import textwrap
from PIL import Image, ImageDraw
from scripts.stage6a.inventory import OUT
from scripts.stage6a.review_candidates import open_image


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--dataset', required=True)
    p.add_argument('--start', type=int, default=0)
    p.add_argument('--count', type=int, default=6)
    a = p.parse_args()
    rows = [json.loads(l) for l in (OUT / 'cohort/primary_c1_review_queue.jsonl').read_text().splitlines()]
    rows = [r for r in rows if r['dataset'] == a.dataset][a.start:a.start+a.count]
    sheet = Image.new('RGB', (1500, 680*((len(rows)+1)//2)), 'white')
    draw = ImageDraw.Draw(sheet)
    for i, r in enumerate(rows):
        image = open_image(r); original = image.size
        image.thumbnail((690, 490))
        ox = (i % 2) * 750 + 35
        oy = (i // 2) * 680 + 40
        sheet.paste(image, (ox, oy))
        for j in range(11):
            x = ox + round(image.width*j/10); y = oy + round(image.height*j/10)
            draw.text((x-5,oy-17),str(j/10),fill='red')
            draw.text((ox-30,y-5),str(j/10),fill='red')
            if 0 < j < 10:
                draw.line((x,oy,x,oy+image.height), fill=(220,190,190), width=1)
                draw.line((ox,y,ox+image.width,y), fill=(220,190,190), width=1)
        draw.text((ox,oy-36),f"{a.start+i} {r['base_id']} native={original} T={r['proposed_target']}",fill='black')
        question = r['question'].split('Choices:')[0]
        draw.multiline_text((ox,oy+500), '\n'.join(textwrap.wrap(question,100))[:800], fill='black')
        draw.text((ox,oy+620), 'Original answer: '+str(r['answer'])[:100],fill='black')
    dest = OUT / 'review' / f"primary_{a.dataset}_{a.start:03d}.png"
    sheet.save(dest)
    print(dest)


if __name__ == '__main__':
    main()
