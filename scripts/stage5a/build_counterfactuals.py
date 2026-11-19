"""Build score-blind numeric-only proposals for manual semantic/sham validation."""
import numpy as np
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from scripts.stage5a.prepare import ROOT,OUT,read_json,read_jsonl,write_json,write_jsonl,sha
from visual_reasoning.stage5a.edits import numeric_edit


def main():
    if (OUT/'cohort/cohort_freeze_complete.json').exists():raise RuntimeError('Frozen cohort')
    proposals=[];failed=[]
    for item in read_jsonl(OUT/'cohort/provisional_atlas.jsonl'):
        m=read_json(ROOT/item['metadata_path']);base=m['base']
        if not any(e['cf_semantics_eligible'] for e in m['events']):continue
        with Image.open(m['source_image']) as im:native=im.convert('RGB')
        for key,fact in m['facts'].items():
            if not fact.get('cf_allowed'):continue
            target=OUT/'counterfactual_assets'/base/key;record=target/'proposal.json';failure=target/'construction_failure.json'
            if record.exists():proposals.append(read_json(record));continue
            if failure.exists():failed.append(read_json(failure));continue
            try:images,audit=numeric_edit(native,fact)
            except ValueError as error:
                value={'base':base,'source':key,'reason':str(error),'attention_used':False,'causal_scores_available':False,'facts':fact}
                write_json(failure,value);failed.append(value);continue
            target.mkdir(parents=True,exist_ok=True);paths={}
            for name,im in images.items():
                path=target/(name+'.png');im.save(path);paths[name]=str(path.relative_to(ROOT))
            result={'base':base,'source':key,'facts':fact,'audit':audit,'paths':paths,
                    'sha256':{k:sha(ROOT/p) for k,p in paths.items()},'manual_review':'pending',
                    'before_causal_scoring':True,'metadata_path':item['metadata_path']}
            write_json(record,result);proposals.append(result)
    write_jsonl(OUT/'counterfactual_assets/proposals.jsonl',proposals)
    write_jsonl(OUT/'counterfactual_assets/construction_failures.jsonl',failed)
    for offset in range(0,len(proposals),24):
        part=proposals[offset:offset+24];sheet=Image.new('RGB',(1080,130*((len(part)+2)//3)),'#eeeeee');d=ImageDraw.Draw(sheet);font=ImageFont.load_default(size=13)
        for i,r in enumerate(part):
            x=i%3*360;y=i//3*130;m=read_json(ROOT/r['metadata_path']);box=r['facts']['roi']
            d.text((x+3,y+2),f'{offset+i} b{r["base"]} {r["source"]}: {r["facts"]["value"]} -> {r["facts"]["counterfactual"]}',fill='black',font=font)
            for j,(name,p) in enumerate([('O',m['source_image']),('sham',ROOT/r['paths']['sham']),('CF',ROOT/r['paths']['semantic'])]):
                with Image.open(p) as im:crop=im.convert('RGB').crop(box)
                factor=min(4,112/crop.width,80/crop.height);crop=crop.resize((max(1,round(crop.width*factor)),max(1,round(crop.height*factor))))
                d.text((x+3+j*120,y+21),name,fill='black',font=font);sheet.paste(crop,(x+3+j*120,y+40))
        sheet.save(OUT/f'counterfactual_assets/review_{offset:04d}.png')
    print({'proposed_sources':len(proposals),'construction_failures':len(failed),'proposed_bases':len({r['base'] for r in proposals})})


if __name__=='__main__':main()
