"""Response-only technical packets: no gold, old outcomes, or bottleneck labels."""
import json
import re
from scripts.stage12ts.common import ROOT, load, save, sha, now
from scripts.stage12ts.worker import fingerprint
from scripts.stage12bs.review import origin_for


def folder_for(task):
    from scripts.stage12ts.common import OLD
    return (OLD if task['task_id'] in load(ROOT/'stage12ts_thinking_manifest.json')['reuse_ids'] else ROOT)/'generations'/task['task_id']

def all_tasks():
    return load(ROOT/'stage12ts_thinking_manifest.json')['tasks']

def checked_generation(task):
    from scripts.stage12ts.common import OLD
    folder=folder_for(task)
    if folder==OLD/'generations'/task['task_id']:
        from scripts.stage12cr.review import checked_generation as original
        return original(task)
    g=load(folder/'generation.json');inp=load(folder/'input.json');receipt=load(folder/'result.json')
    assert receipt['generation_sha256']==sha(folder/'generation.json')
    assert receipt['input_sha256']==sha(folder/'input.json')
    assert receipt['task_sha256']==g['task_sha256']==inp['task_sha256']==fingerprint(task)
    assert len(g['generated_token_ids'])==g['tokens']
    cfg=load(ROOT/'config.json');arm=task['arm'];c=cfg['arms'][arm]
    prior=load('outputs/stage12bs/v1/stage12bs_full_manifest.json')
    native=next(t for t in prior['tasks'] if t['item_id']==task['item_id'] and t['arm']=='N')
    baseline=load(origin_for(native['task_id'])/'generations'/native['task_id']/'input.json')
    texts=[v['text'] for m in inp['messages'] for v in m['content'] if v['type']=='text']
    images=[v for m in inp['messages'] for v in m['content'] if v['type']=='image']
    suffix='<|im_start|>assistant\n'+('<think>\n' if arm=='T' else '')
    checks=dict(exact_task=inp['task']==task,
        exact_prompt=task['prompt']==native['prompt'],
        actual_text=texts==[task['prompt']],single_user=len(inp['messages'])==1 and inp['messages'][0]['role']=='user',
        image_payload=len(images)==len(inp['prepared_image_pixel_sha256'])==1,
        original_pixels=inp['prepared_image_pixel_sha256']==baseline['prepared_image_pixel_sha256'],
        image_bytes=sha(task['image'])==task['image_sha256']==native['image_sha256'],
        image_present=inp['image_present'] and images[0]['image']==task['image'] and g['visual_tokens']>0,
        native_template=inp['chat_prompt'].endswith(suffix),config=g['config_sha256']==sha(ROOT/'config.json'),
        native_seed=g['seed']==task['seed']==native['seed'],
        recipe=g['sampling']==dict(c['recipe'],max_tokens=c['cap']),
        cap_consistent=g['cap_hit']==(g['finish_reason']=='length') and (not g['cap_hit'] or g['tokens']==c['cap']))
    return g,checks


def materialize():
    for task in all_tasks():
        tid=task['task_id'];folder=folder_for(task);dest=ROOT/'audit/technical_packets'/f'{tid}.json'
        if not (folder/'result.json').exists() or dest.exists():continue
        g,checks=checked_generation(task);raw=g['raw_decoded_response']
        seen={};paragraphs=[];offset=0
        for part in re.split(r'(?:\n[ \t]*){2,}',raw):
            pos=raw.find(part,offset);assert pos>=0;offset=pos+len(part)
            if part not in seen:seen[part]=pos
            paragraphs.append(dict(offset=pos,first_occurrence=seen[part],text=part))
        p=dict(at=now(),task_id=tid,item_id=task['item_id'],family_id=task['family_id'],arm=task['arm'],
            question=task['prompt'],raw=raw,tokens=g['tokens'],cap_hit=g['cap_hit'],normal_stop=g['normal_stop'],
            generation_sha256=sha(folder/'generation.json'),checks=checks,unique_paragraphs=paragraphs)
        save(dest,p)
        text=f"{tid} TOKENS {g['tokens']} STOP {g['finish_reason']}\nQUESTION: {task['prompt']}\n\n"
        text+='\n\n'.join(f"OFFSET {p['offset']}\n{p['text']}" for p in paragraphs if p['offset']==p['first_occurrence'])
        if len(raw)>12000:text+='\n\nORIGINAL END\n'+raw[-5000:]
        dest.with_suffix('.txt').write_text(text)
    print('Technical packets:',len(list((ROOT/'audit/technical_packets').glob('*.json'))))


def show(tid,start=0,end=None,tail=0):
    p=load(ROOT/'audit/technical_packets'/f'{tid}.json')
    text='\n\n'.join(x['text'] for x in p['unique_paragraphs'] if x['offset']==x['first_occurrence'])
    print(tid,'TOKENS',p['tokens'],'CAP',p['cap_hit'],'UNIQUE_CHARS',len(text),'QUESTION',p['question'])
    print(text[start:end])
    if tail:print('ORIGINAL TAIL',p['raw'][-tail:])


if __name__=='__main__':materialize()
