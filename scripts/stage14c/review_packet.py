"""Create source-only inspection sheets, preserving full originals externally."""
import argparse
import base64
import io
import json
from pathlib import Path
import pyarrow.parquet as pq
from PIL import Image, ImageDraw


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--start',type=int,required=True);ap.add_argument('--count',type=int,default=20);args=ap.parse_args()
    base=Path('outputs/stage14c/source');rows=[json.loads(l) for l in (base/'cohort_manifest.jsonl').read_text().splitlines()][args.start:args.start+args.count]
    spec=json.loads(Path('outputs/stage14c/audit/g1_source_inputs_v1.json').read_text());tables={k:pq.read_table(v,columns=['image']) for k,v in spec['parquets'].items()}
    canvas=Image.new('RGB',(1800,((len(rows)+3)//4)*480),'white');d=ImageDraw.Draw(canvas)
    for n,r in enumerate(rows):
        v=tables[r['benchmark']].slice(r['row_index'],1).to_pylist()[0]['image'];payload=v['bytes'] if isinstance(v,dict) else base64.b64decode(v) if isinstance(v,str) else v
        im=Image.open(io.BytesIO(payload));im.thumbnail((440,440));x=n%4*450;y=n//4*480;canvas.paste(im,(x,y+30));d.text((x+5,y+5),f'{r["review_rank"]}: {r["item_id"]}',fill='black')
    path=base/'review_images'/f'ranks_{args.start}_{args.start+len(rows)-1}.png';canvas.save(path);print(path)


if __name__=='__main__':main()
