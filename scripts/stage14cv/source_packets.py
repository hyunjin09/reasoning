"""Bounded source-only visual packets, with no model responses or gold labels."""
import hashlib
import io
from pathlib import Path
from PIL import Image, ImageDraw
import pyarrow.parquet as pq
from scripts.stage14c.common import rows, load, save, sha, now
from scripts.stage14c.line_source import read_vertical_orders

ROOT = Path('outputs/stage14c_v_blindtest_validation')


def main():
    items = rows(ROOT/'cohorts/blindtest_e300_reference_proposal_v1.jsonl')
    ledgers = {r['family_id']: r for r in rows(ROOT/'source_qc/semantic_ledger_proposal_v1.jsonl')}
    table = pq.read_table(items[0]['source']['parquet'], columns=['image'])
    output = ROOT/'source_qc/review_sheets'; output.mkdir(exist_ok=True)
    manifest = []; checks = []
    for start in range(0,300,20):
        canvas = Image.new('RGB',(1500,1320),'white'); draw = ImageDraw.Draw(canvas)
        for slot,r in enumerate(items[start:start+20]):
            s=r['source'];fid=s['family_id'];v=table.slice(s['row_index'],1).to_pylist()[0]['image']
            payload=v['bytes'];assert hashlib.sha256(payload).hexdigest()==s['image_sha256']
            image=Image.open(io.BytesIO(payload)).convert('RGB');image.load()
            orders=list(ledgers[fid]['ledger']['blue_relative_to_red'].values())
            # JSONL sorting makes map order alphabetical; bind positions explicitly.
            orders=[ledgers[fid]['ledger']['blue_relative_to_red'][p] for p in ['left','middle','right']]
            try:
                observed=read_vertical_orders(image);match=observed['orders']==orders
            except ValueError as e:
                observed=dict(error=str(e));match=False
            checks.append(dict(family_id=fid,source_rank=start+slot,image_sha256=s['image_sha256'],
                frozen_orders=orders,pixel_check=observed,matches=match,
                limitation='Same inherited pixel method, not independent semantic reliability. Visual reread required.'))
            x=(slot%5)*300;y=(slot//5)*330
            thumb=image.copy();thumb.thumbnail((292,280));canvas.paste(thumb,(x+(300-thumb.width)//2,y+30))
            draw.text((x+5,y+2),f'{start+slot:03d} {fid.split(":")[1][:12]}',fill='black')
            draw.text((x+5,y+312),'L/M/R blue: '+' / '.join(orders),fill='black' if match else 'red')
        path=output/f'sheet_{start:03d}.png';assert not path.exists();canvas.save(path)
        manifest.append(dict(path=str(path),sha256=sha(path),start=start,count=min(20,300-start),
            family_ids=[r['source']['family_id'] for r in items[start:start+20]]))
    save(ROOT/'source_qc/pixel_reread_v1.json',dict(at=now(),checks=checks,
        mismatches=[r['family_id'] for r in checks if not r['matches']],model_outcomes_used=False))
    save(output/'manifest.json',dict(at=now(),sheets=manifest,model_outcomes_used=False))
    print('sheets',len(manifest),'pixel mismatches',sum(not r['matches'] for r in checks))


if __name__=='__main__':main()
