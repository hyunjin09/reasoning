"""Prepare source-only second-review/reread packets; never certify acceptance."""
import argparse
import base64
import hashlib
import io
import json
import math
from pathlib import Path

import pyarrow.parquet as pq
from PIL import Image, ImageDraw

BASE = Path('outputs/stage14c')


def inputs():
    cohort = [json.loads(x) for x in (BASE/'source/cohort_manifest.jsonl').read_text().splitlines()]
    reviews = [r for p in sorted((BASE/'source/primary_reviews').glob('*.json'))
               for r in json.loads(p.read_text())['rows']]
    assert sorted(r['review_rank'] for r in reviews) == list(range(len(cohort)))
    return cohort, reviews


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--panel', choices=['MMStar', 'BlindTest', 'reread'], required=True)
    ap.add_argument('--start', type=int, default=0)
    ap.add_argument('--count', type=int, default=20)
    args = ap.parse_args()
    cohort, reviews = inputs()
    if args.panel == 'reread':
        selected = []
        for benchmark in ['MMStar', 'BlindTest']:
            rows = [r for r in cohort if r['benchmark'] == benchmark]
            rows.sort(key=lambda r: (hashlib.sha256(
                f'stage14c-g0-v1-20261008|source-reread|{r["family_id"]}'.encode()).hexdigest(), r['family_id']))
            selected.extend(r['review_rank'] for r in rows[:math.ceil(len(rows)*.1)])
    else:
        selected = [r['review_rank'] for r in reviews
                    if r['benchmark'] == args.panel and r['label'] == 'ELIGIBLE']
    selected = selected[args.start:args.start+args.count]
    spec = json.loads((BASE/'audit/g1_source_inputs_v1.json').read_text())
    tables = {b: pq.read_table(spec['parquets'][b], columns=['image'])
              for b in {cohort[i]['benchmark'] for i in selected}}
    target = BASE/'source/second_review_packets'
    target.mkdir(exist_ok=True)
    canvas = Image.new('RGB', (1800, math.ceil(len(selected)/4)*480), 'white')
    draw = ImageDraw.Draw(canvas)
    metadata = []
    for j, rank in enumerate(selected):
        r = cohort[rank]
        value = tables[r['benchmark']].slice(r['row_index'], 1).to_pylist()[0]['image']
        payload = value['bytes'] if isinstance(value, dict) else base64.b64decode(value) if isinstance(value, str) else value
        im = Image.open(io.BytesIO(payload)); im.thumbnail((440, 440))
        x, y = j%4*450, j//4*480
        canvas.paste(im, (x, y+30))
        draw.text((x+5, y+5), f'{rank}: {r["item_id"]}', fill='black')
        metadata.append(dict(review_rank=rank, question=r['question'], prior=reviews[rank]))
    stem = f'{args.panel}_{args.start:03d}_{args.start+len(selected)-1:03d}'
    canvas.save(target/f'{stem}.png')
    (target/f'{stem}.json').write_text(json.dumps(metadata, indent=2, ensure_ascii=False)+'\n')
    print(target/f'{stem}.png')


if __name__ == '__main__':
    main()
