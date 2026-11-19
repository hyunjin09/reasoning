"""Immutable review packets containing images and complete candidate-claim context."""
import argparse
import json
from PIL import Image, ImageDraw
from scripts.stage6a.inventory import OUT


def main():
    p=argparse.ArgumentParser();p.add_argument('--batch',required=True);p.add_argument('--start',type=int,default=0);p.add_argument('--count',type=int,default=8)
    p.add_argument('--unreviewed',action='store_true');p.add_argument('--final-first',action='store_true')
    a=p.parse_args();assert a.batch.isidentifier()
    rows=[json.loads(s) for s in (OUT/'c4_natural_failure/candidate_hallucination_review.jsonl').read_text().splitlines()]
    if a.unreviewed:
        path=OUT/'c4_natural_failure/c4_claim_reviews.jsonl'
        reviewed={r['claim_id'] for r in map(json.loads,path.read_text().splitlines())} if path.exists() else set()
        rows=[{**r,'candidates':[c for c in r['candidates'] if c['claim_id'] not in reviewed]} for r in rows]
        rows=[r for r in rows if r['candidates']]
    if a.final_first:rows.sort(key=lambda r:(not any(c['section']=='final' for c in r['candidates']),r['base_id']))
    rows=rows[a.start:a.start+a.count]
    dest=OUT/'review'/f'c4_{a.batch}.json';assert not dest.exists()
    dest.write_text(json.dumps(rows,indent=2)+'\n')
    for start in range(0,len(rows),4):
        chunk=rows[start:start+4];sheet=Image.new('RGB',(1320,570*((len(chunk)+1)//2)),'white');draw=ImageDraw.Draw(sheet)
        for i,row in enumerate(chunk):
            ox=(i%2)*660;oy=(i//2)*570;im=Image.open(row['image_path']).convert('RGB');im.thumbnail((640,490))
            sheet.paste(im,(ox+10,oy+55));draw.text((ox+10,oy+3),row['base_id'],fill='black')
            categories=sorted({c['category'] for c in row['candidates']})
            draw.text((ox+10,oy+20),'Review categories: '+', '.join(categories),fill='black')
        path=OUT/'review'/f'c4_{a.batch}_{start:03d}.png';sheet.save(path);print(path)
    print(dest)


if __name__=='__main__':main()
