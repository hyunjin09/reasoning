"""Gold-blind response packets and input-integrity checks for36 frozen calls."""
import argparse
import hashlib
import re
from pathlib import Path
from scripts.stage12bs.common import ROOT, load, save, sha, now
from scripts.stage12bs.worker import fingerprint


def checked_generation(task):
    origin = origin_for(task['task_id'])
    folder = origin/'generations'/task['task_id']
    receipt = load(folder/'result.json')
    g, inp = load(folder/'generation.json'), load(folder/'input.json')
    assert receipt['generation_sha256'] == sha(folder/'generation.json')
    assert receipt['input_sha256'] == sha(folder/'input.json')
    assert receipt['task_sha256'] == g['task_sha256'] == inp['task_sha256'] == fingerprint(task)
    assert len(g['generated_token_ids']) == g['tokens']
    cfg = load(origin/'config.json')
    original = load('outputs/stage12b/v1/stage12b_frozen_manifest.json')
    frozen_task = next(t for t in original['tasks'] if t['task_id'] == task['task_id'])
    messages = inp['messages']
    text = [c['text'] for m in messages for c in m['content'] if c['type']=='text']
    images = [c for m in messages for c in m['content'] if c['type']=='image']
    checks = dict(exact_original_task=task==frozen_task==inp['task'],
        exact_text=text==[task['prompt']],single_user=len(messages)==1 and messages[0]['role']=='user',
        intended_image=inp['image_present']==(task['arm']!='O') and inp['image_sha256']==task['image_sha256'],
        payload_count=len(images)==len(inp['prepared_image_pixel_sha256'])==(0 if task['arm']=='O' else 1),
        visual_tokens=(g['visual_tokens']==0)==(task['arm']=='O'),
        template=inp['chat_prompt'].endswith('<|im_start|>assistant\n') and task['prompt'] in inp['chat_prompt'],
        config=g['config_sha256']==sha(origin/'config.json'),seed=g['seed']==task['seed'],
        sampling=g['sampling']==dict(cfg['recipe'],max_tokens=task['cap']),
        cap_consistent=(g['cap_hit']==(g['finish_reason']=='length')) and (not g['cap_hit'] or g['tokens']==task['cap']))
    if task['image']:
        checks['image_bytes'] = sha(task['image']) == task['image_sha256']
        checks['image_path'] = images[0]['image'] == task['image']
    else:
        checks['no_image_token'] = '<|image_pad|>' not in inp['chat_prompt']
    # Exact task equality inherits the source-only61-family oracle/fact/no-leakage audit.
    checks['frozen_oracle_integrity'] = load('outputs/stage12b/v1/stage12b_oracle_integrity_review.json')['pass']
    return g, checks



def origin_for(task_id):
    full=load(ROOT/'stage12bs_full_manifest.json')
    reused={r['task_id']:r['origin'] for r in full['reuse']}
    return Path(reused.get(task_id,str(ROOT)))


def materialize():
    full=load(ROOT/'stage12bs_full_manifest.json')
    for t in full['tasks']:
        folder=origin_for(t['task_id'])/'generations'/t['task_id']
        if not (folder/'result.json').exists():continue
        dest=ROOT/'audit/technical_packets'/f"{t['task_id']}.json"
        if dest.exists():continue
        g,checks=checked_generation(t)
        n=next(x for x in full['tasks'] if x['item_id']==t['item_id'] and x['arm']=='N')
        raw=g['raw_decoded_response'];paras=re.split(r'(?:\n[ \t]*){2,}',raw);seen={};coverage=[];unique=[];offset=0
        for p in paras:
            pos=raw.find(p,offset);assert pos>=0;offset=pos+len(p)
            first=p not in seen
            if first:seen[p]=pos;unique.append(f'OFFSET {pos}\n{p}')
            coverage.append(dict(offset=pos,first_occurrence=seen[p],text=p))
        save(dest,dict(task=t['task_id'],item_id=t['item_id'],family_id=t['family_id'],arm=t['arm'],
            question=n['prompt'],request=t['prompt'] if t['arm']=='E' else None,
            raw=raw,tokens=g['tokens'],cap_hit=g['cap_hit'],normal_stop=g['normal_stop'],
            generation_path=str(folder/'generation.json'),generation_sha256=sha(folder/'generation.json'),checks=checks,
            unique_paragraphs=coverage))
        text=f"{t['task_id']} TOKENS {g['tokens']} STOP {g['finish_reason']}\nQUESTION: {n['prompt']}\n"
        if t['arm']=='E':text+=f"REQUEST: {t['prompt']}\n"
        text+='\nUNIQUE EXACT PARAGRAPHS IN FIRST-OCCURRENCE ORDER\n'+'\n\n'.join(unique)
        if len(raw)>12000:text+='\n\nORIGINAL-ORDER LAST5000CHARS\n'+raw[-5000:]
        (dest.with_suffix('.txt')).write_text(text)
    print('TECHNICAL_PACKETS',len(list((ROOT/'audit/technical_packets').glob('*.json'))))


if __name__=='__main__':materialize()
