"""Build score-blind image/contact sheets and indexed native text for annotation."""
import argparse
from bisect import bisect_right
from PIL import Image,ImageDraw,ImageFont
from scripts.stage5a.prepare import ROOT,OUT,read_json,read_jsonl,write_json,write_jsonl
from visual_reasoning.stage4a.cohort import equivalent_numeric_matches


def main():
    p=argparse.ArgumentParser();p.add_argument('--start',type=int,default=0);p.add_argument('--count',type=int,default=20);args=p.parse_args()
    screen=read_jsonl(OUT/'cohort/prospective_screen_manifest.jsonl')[args.start:args.start+args.count]
    new={r['example_id']:r for r in [read_json(p) for p in (OUT/'prospective_generation/raw').glob('shard_*/examples/*/result.json')]}
    folder=OUT/'cohort/review';folder.mkdir(parents=True,exist_ok=True)
    font=ImageFont.load_default(size=15);sheet=Image.new('RGB',(1280,320*((len(screen)+3)//4)),'white');draw=ImageDraw.Draw(sheet)
    proposals=[];lines=[]
    for idx,item in enumerate(screen):
        base=item['base_problem_id'];artifact=(item['native_reuse'] or new.get(item['example_id'],{})).get('artifact_dir')
        with Image.open(item['source_image']) as src:image=src.convert('RGB')
        x=(idx%4)*320;y=(idx//4)*320
        draw.text((x+4,y+3),f'{item["screen_order"]}: base {base}  {image.width}x{image.height}',font=font,fill='black')
        image.thumbnail((310,280));sheet.paste(image,(x+5,y+28))
        if not artifact:lines.append(f'## {base}: native pending\n');continue
        result=read_json(ROOT/artifact/'result.json');tokens=read_jsonl(ROOT/artifact/'tokens.jsonl')
        text=''.join(str(t['decoded_token']) for t in tokens);starts=[];n=0
        for token in tokens:starts.append(n);n+=len(str(token['decoded_token']))
        (folder/f'{base}_native.txt').write_text(text)
        facts=[]
        for fi,f in enumerate(item['candidate_facts']):
            matches=equivalent_numeric_matches(text,f['original_value']);mentions=[]
            for m in matches:
                mentions.append({'token':bisect_right(starts,m.start())-1,'char_start':m.start(),'char_end':m.end(),
                    'surface':m.group(),'context':text[max(0,m.start()-100):m.end()+125].replace('\n',' ')})
            facts.append({**f,'fact_id':fi,'mentions':mentions})
        proposals.append({**item,'artifact_dir':artifact,'native_status':result['status'],'complete':result['complete'],
            'token_count':len(tokens),'facts':facts,'semantic_reviewed':False,'attention_available':False})
        lines.extend([f'## {item["screen_order"]}: base {base}',f'TD aid: {item["text_dominant_question"]}',
            f'Native {result["status"]}; tokens={len(tokens)}. Initial text (proposal context only):',text[:2200].replace('\n',' '),''])
        for fact in facts:
            lines.append(f'Fact{fact["fact_id"]} value={fact["original_value"]}: {fact["context"]}')
            show=fact['mentions'][:3]+(fact['mentions'][-1:] if len(fact['mentions'])>3 else [])
            for m in show:lines.append(f'  t={m["token"]} chars={m["char_start"]}:{m["char_end"]} {m["context"]}')
        lines.append('')
    sheet.save(folder/f'native_{args.start:04d}.png')
    (folder/f'review_{args.start:04d}.md').write_text('\n'.join(lines))
    write_jsonl(folder/f'proposals_{args.start:04d}.jsonl',proposals)
    print({'reviewed_screen_range':[args.start,args.start+len(screen)],'native_available':len(proposals),'sheet':str(folder/f'native_{args.start:04d}.png')})


if __name__=='__main__':main()
