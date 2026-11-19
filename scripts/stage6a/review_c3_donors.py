"""Group unrelated-control donors for pre-stress semantic image review."""
import json
from collections import defaultdict
from PIL import Image, ImageDraw
from scripts.stage6a.inventory import OUT


def main():
    rows=[json.loads(s) for s in (OUT/'cohort/c3_primary_manifest.jsonl').read_text().splitlines()]
    intact={r['base_id']:r for r in rows if r['condition']=='intact'}
    groups=defaultdict(list)
    for row in rows:
        if row['condition']=='unrelated':
            groups[row['unrelated_donor']].append(dict(base_id=row['base_id'],event_id=row['event_id'],category=row['category']))
    packet=[dict(donor_id=k,image_path=intact[k]['image_path'],recipients=v) for k,v in sorted(groups.items())]
    dest=OUT/'review/c3_unrelated_donors.json'
    assert not dest.exists()
    dest.write_text(json.dumps(packet,indent=2)+'\n')
    for start in range(0,len(packet),4):
        sheet=Image.new('RGB',(1320,1160),'white');draw=ImageDraw.Draw(sheet)
        for i,row in enumerate(packet[start:start+4]):
            x=(i%2)*660;y=(i//2)*580
            im=Image.open(row['image_path']).convert('RGB');im.thumbnail((640,485))
            sheet.paste(im,(x+10,y+80));draw.text((x+10,y+4),row['donor_id'],fill='black')
            cats=sorted({r['category'] for r in row['recipients']})
            draw.text((x+10,y+22),'Check ABSENT: '+', '.join(cats[:4]),fill='black')
            if len(cats)>4:draw.text((x+10,y+40),', '.join(cats[4:]),fill='black')
        sheet.save(OUT/f'review/c3_unrelated_{start:03}.png')
    print('Frozen donor review packet:',len(packet),'images')


if __name__=='__main__':main()
