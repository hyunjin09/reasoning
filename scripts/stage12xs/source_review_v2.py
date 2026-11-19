"""Additive source reviews after the explicitly approved reserve amendment."""
from pathlib import Path
from scripts.stage12xs.common import ROOT as V1, load, save, sha, now

ROOT = Path('outputs/stage12xs/v2')

def source_rows():
    return load(V1/'stage12xs_source_candidate_manifest.json')['rows'] + load(ROOT/'audit/approved_extension64.json')['rows']

def records():
    result = {p.stem:load(p) for p in (V1/'annotations/primary').glob('*.json')}
    result.update({p.stem:load(p) for p in (ROOT/'annotations/primary').glob('*.json')})
    result.update({p.stem:load(p) for p in (ROOT/'annotations/resolved').glob('*.json')})
    return result

def record(item, facts, rationale, eligible=True, resolved=False):
    row = next(r for r in source_rows() if r['item_id']==item)
    assert sha(row['image']) == row['image_sha256']
    assert (1 <= len(facts) <= 4) if eligible else not facts
    previous = records().get(item)
    path = ROOT/'annotations'/('resolved' if resolved else 'primary')/f'{item}.json'
    save(path,dict(at=now(),item_id=item,family_id=row['family_id'],eligible=eligible,
        image_sha256=row['image_sha256'],facts=[dict(fact_id=f'E{i}',probe_request=q,gold_value=v) for i,(q,v) in enumerate(facts,1)],
        source_only_rationale=rationale,reviewer='main agent; source image and question',model_outcomes_used=False,
        previous_review_preserved=previous['at'] if previous else None))

def board(ids, name):
    from PIL import Image,ImageDraw
    rows=[next(r for r in source_rows() if r['item_id']==i) for i in ids]
    canvas=Image.new('RGB',(1280,500*((len(rows)+1)//2)),'white');draw=ImageDraw.Draw(canvas)
    for j,r in enumerate(rows):
        im=Image.open(r['image']).convert('RGB');im.thumbnail((610,450))
        x=(j%2)*640;y=(j//2)*500
        draw.text((x+10,y+8),'Item '+r['item_id'],fill='black')
        canvas.paste(im,(x+(640-im.width)//2,y+35+(450-im.height)//2))
    path=ROOT/'audit/source_boards'/f'{name}.png';path.parent.mkdir(parents=True,exist_ok=True)
    assert not path.exists();canvas.save(path)
    for r in rows:print(r['item_id'],r['question'])
    print('BOARD',path)
