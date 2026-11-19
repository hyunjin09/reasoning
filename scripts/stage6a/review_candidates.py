"""Contact sheets for semantic/ROI review, without attention or model outputs."""
import argparse
import io
import json
from functools import lru_cache
from PIL import Image, ImageDraw
from scripts.stage6a.prepare_candidates import OUT, read_arrow


@lru_cache(maxsize=2)
def table(path):return read_arrow(path)


def open_image(row):
    if row.get('image_path'):
        return Image.open(row['image_path']).convert('RGB')
    value=table(row['arrow_path']).column(row['image_column'])[row['arrow_row']].as_py()
    return Image.open(io.BytesIO(value['bytes'])).convert('RGB')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--dataset',required=True);ap.add_argument('--start',type=int,default=0);ap.add_argument('--count',type=int,default=12)
    ap.add_argument('--no-question-digits',action='store_true')
    args=ap.parse_args()
    rows=[json.loads(l) for l in (OUT/'cohort/semantic_candidate_order.jsonl').read_text().splitlines()]
    rows=[r for r in rows if r['dataset']==args.dataset]
    if args.no_question_digits:
        import re
        rows=[r for r in rows if not re.search(r'\d',re.sub(r'<image\d+>','',r['question']))]
    rows=rows[args.start:args.start+args.count]
    sheet=Image.new('RGB',(1600,440*((len(rows)+3)//4)),'white');draw=ImageDraw.Draw(sheet)
    for i,r in enumerate(rows):
        im=open_image(r);size=im.size;im.thumbnail((390,360));x=(i%4)*400;y=(i//4)*440
        sheet.paste(im,(x+(400-im.width)//2,y+40))
        draw.text((x+5,y+4),f"{args.start+i} {r['base_id']} ({size[0]}x{size[1]})",fill='black')
        draw.text((x+5,y+408),r['question'][:60],fill='black')
        print(json.dumps(dict(index=args.start+i,**{k:v for k,v in r.items() if k not in ('arrow_path','image_path','prompt')}),ensure_ascii=False))
    dest=OUT/'review';dest.mkdir(exist_ok=True)
    suffix='_no_question_digits' if args.no_question_digits else ''
    sheet.save(dest/f'{args.dataset}_{args.start:04}{suffix}.png')


if __name__=='__main__':main()
