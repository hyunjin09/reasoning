"""Prepare source-only MathVerse review panels; store actual human/agent receipts."""
import argparse
from PIL import Image, ImageDraw
from scripts.stage14a.common import ROOT, load, save, now, sha

VERSIONS=['Text Dominant','Text Lite','Text Only','Vision Intensive','Vision Dominant','Vision Only']
CHECKS=['same_task','gold_consistency','text_only_sufficient','visual_versions_sufficient','answer_safe','unique_ids']
FEATURES=['image_present','textual_information_level','visual_information_level','requires_visual_binding',
          'requires_symbolic_reasoning','contains_explicit_entity_labels','contains_explicit_quantities','requires_low_level_visual_detail']

def packet(start,count):
    source=load(ROOT/'audit/mathverse_mapping_source_snapshot.json')
    selected=source['families'][start-1:start-1+count]
    by={}
    for v in source['versions']:by.setdefault(v['family_id'],[]).append(v)
    rows=[dict(f,variants=by[f['family_id']]) for f in selected]
    out=ROOT/'audit/packets'/f'verse_{start:04d}_{start+len(rows)-1:04d}'
    out.mkdir(parents=True,exist_ok=True)
    canvas=Image.new('RGB',(1500,600*len(rows)),'white');d=ImageDraw.Draw(canvas)
    for j,row in enumerate(rows):
        images=[]
        for v in row['variants']:
            if v['image'] and v['image'] not in [p for _,p in images]:images.append((v['version'],v['image']))
        for i,(version,path) in enumerate(images):
            x,y=i*500,j*600
            d.text((x+8,y+8),f"{row['problem_index']} | {version}",fill='black')
            with Image.open(path) as im:
                im=im.convert('RGB');im.thumbnail((485,555));canvas.paste(im,(x+(500-im.width)//2,y+30))
    if not (out/'board.jpg').exists():canvas.save(out/'board.jpg',quality=95)
    if not (out/'source.json').exists():save(out/'source.json',rows)
    for r in rows:
        print('FAMILY',r['problem_index'],'GOLD',r['gold_answer'],'TYPE',r['answer_type'])
        for v in r['variants']:print(v['version']+': '+v['question'])
    print(out/'board.jpg')

def commit(path):
    source=load(ROOT/'audit/mathverse_mapping_source_snapshot.json')
    by={r['family_id']:r for r in source['families']}
    for r in load(path):
        assert r['family_id'] in by
        assert set(r['consistency_checks'])==set(CHECKS)
        assert all(v in ['PASS','FAIL','UNRESOLVED'] for v in r['consistency_checks'].values())
        assert r['review_note'].strip()
        assert set(r['source_metadata'])==set(VERSIONS)
        for v,features in r['source_metadata'].items():
            assert set(features)==set(FEATURES)
            assert features['image_present']==(v!='Text Only')
        save(ROOT/'audit/reviews/mathverse'/(by[r['family_id']]['problem_index']+'.json'),
             dict(r,at=now(),reviewer='main agent',source_receipt_sha256=sha(path),model_outcomes_used=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['packet','commit']);p.add_argument('--start',type=int);p.add_argument('--count',type=int,default=4);p.add_argument('--path')
    a=p.parse_args();packet(a.start,a.count) if a.action=='packet' else commit(a.path)
