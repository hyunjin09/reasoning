"""Review fixed C1 source strata for additional independent numeric facts."""
import argparse
import json
from PIL import Image,ImageDraw
from scripts.stage6a.inventory import OUT
from scripts.stage6a.prepare_candidates import write


def main():
    p=argparse.ArgumentParser();p.add_argument('--start',type=int,default=0);p.add_argument('--count',type=int,default=4)
    p.add_argument('--remaining-strata',action='store_true');a=p.parse_args()
    path=OUT/('cohort/c1_secondary_remaining_review_order.jsonl' if a.remaining_strata else 'cohort/c1_secondary_source_review_order.jsonl')
    if path.exists():rows=[json.loads(s) for s in path.read_text().splitlines()]
    else:
        assert not a.remaining_strata, 'Freeze the remaining eligible C1 source-only review order first'
        rows=[r for r in map(json.loads,(OUT/'cohort/c1_primary_v2_manifest.jsonl').read_text().splitlines()) if r['dataset']=='MathVerse' and r['condition']=='intact']
        assert len(rows)==34
        write(path,rows)
        (OUT/'config/c1_secondary_source_annotation_scope.json').write_text(json.dumps(dict(
            scope='All34already frozen MathVerse C1 candidates, in construction order; no native outcome used to select this annotation stratum.',
            goal='Localize clear additional numeric visual facts for source-identity demand annotations.',
            rules=['Direct full-source review, numeric value and semantic role recorded.',
                'Rectangles must be nonempty and spatially disjoint fromT and one another.',
                'Single-source/ambiguous extra facts explicitly recorded without invented ROI.',
                'No stimulus/prompt/native generation modification; annotation sidecar only.',
                'No attention, confidence, causal effect or trajectory feature used.']),indent=2)+'\n')
    subset=rows[a.start:a.start+a.count]
    for start in range(0,len(subset),4):
        chunk=subset[start:start+4];sheet=Image.new('RGB',(1440,700*((len(chunk)+1)//2)),'white');draw=ImageDraw.Draw(sheet)
        for i,row in enumerate(chunk):
            ox=i%2*720;oy=i//2*700;im=Image.open(row['image_path']).convert('RGB');w,h=im.size
            annotated=im.copy();ImageDraw.Draw(annotated).rectangle(row['target']['roi'],outline='red',width=2)
            annotated.thumbnail((690,610));sheet.paste(annotated,(ox+10,oy+65))
            draw.text((ox+10,oy+5),f"{a.start+start+i}: {row['base_id']} native {w}x{h}",fill='black')
            draw.text((ox+10,oy+23),'T: '+row['target']['entity']+'='+row['target']['value'],fill='black')
            print(json.dumps(dict(index=a.start+start+i,base_id=row['base_id'],size=[w,h],T=row['target'],question=row['question'])))
        stem='c1_secondary_remaining' if a.remaining_strata else 'c1_secondary'
        dest=OUT/f'review/{stem}_{a.start+start:03d}.png';sheet.save(dest);print(dest)


if __name__=='__main__':main()
