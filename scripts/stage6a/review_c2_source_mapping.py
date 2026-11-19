"""One bounded source-only revalidation of the32already acquired C2 families."""
import json
from PIL import Image, ImageDraw
from scripts.stage6a.inventory import OUT


def main():
    target=OUT/'review/c2_source_mapping_packet.json'
    assert not target.exists(), 'Preserve the fixed revalidation packet'
    rows=[json.loads(s) for s in (OUT/'cohort/c2_primary_manifest.jsonl').read_text().splitlines()]
    bases=[r for r in rows if r['condition']=='AR']
    assert len(bases)==32
    packet=[]
    for start in range(0,len(bases),2):
        sheet=Image.new('RGB',(1400,1500),'white');draw=ImageDraw.Draw(sheet)
        artifact=f'review/c2_source_mapping_{start:03d}.jpg'
        for i,row in enumerate(bases[start:start+2]):
            native=Image.open(row['image_path']).convert('RGB')
            marked=native.copy();md=ImageDraw.Draw(marked)
            sources=[row['target']]+row['other_sources']
            for source,color in zip(sources,['red','blue']):md.rectangle(source['roi'],outline=color,width=3)
            marked.thumbnail((670,700));y=i*750
            sheet.paste(marked,(5,y+35));draw.text((8,y+8),row['base_id']+' T=red X=blue',fill='black')
            for j,source in enumerate(sources):
                x0,y0,x1,y1=source['roi'];box=[max(0,x0-250),max(0,y0-95),min(native.width,x1+250),min(native.height,y1+95)]
                crop=native.crop(box);cd=ImageDraw.Draw(crop)
                cd.rectangle([x0-box[0],y0-box[1],x1-box[0],y1-box[1]],outline=['red','blue'][j],width=2)
                crop.thumbnail((690,290));sheet.paste(crop,(700,y+55+j*350))
                draw.text((705,y+25+j*350),source['source_id']+' '+source['entity']+' = '+row['answers'][j],fill='black')
            packet.append(dict(base_id=row['base_id'],image_path=row['image_path'],review_image=artifact,
                sources=sources,answers=row['answers'],events=[{k:r[k] for k in ['event_id','condition','prompt','answer']} for r in rows if r['base_id']==row['base_id']],
                review_scope='Full source layout, native T/X glyph context and AR/R-only versus A-only/Neither source equivalence; no native outputs or model features included.'))
        sheet.save(OUT/artifact)
    target.write_text(json.dumps(packet,indent=2)+'\n')
    print('Prepared32source mappings in16review sheets; no judgments inferred')


if __name__=='__main__':main()
