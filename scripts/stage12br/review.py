"""Gold-blind response packets and input-integrity checks for36 frozen calls."""
import argparse
import hashlib
import re
from pathlib import Path
from scripts.stage12br.common import ROOT, load, save, sha, now
from scripts.stage12br.worker import fingerprint


def checked_generation(task):
    folder = ROOT/'generations'/task['task_id']
    receipt = load(folder/'result.json')
    g, inp = load(folder/'generation.json'), load(folder/'input.json')
    assert receipt['generation_sha256'] == sha(folder/'generation.json')
    assert receipt['input_sha256'] == sha(folder/'input.json')
    assert receipt['task_sha256'] == g['task_sha256'] == inp['task_sha256'] == fingerprint(task)
    assert len(g['generated_token_ids']) == g['tokens']
    cfg = load(ROOT/'config.json')
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
        config=g['config_sha256']==sha(ROOT/'config.json'),seed=g['seed']==task['seed'],
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


def packet():
    m = load(ROOT/'stage12br_validation_manifest.json')
    out = Path('reports/stage12br/v1');out.mkdir(parents=True,exist_ok=True)
    reviewed = []
    for item in m['validation_ids']:
        tasks = [t for t in m['tasks'] if t['item_id']==item]
        question = next(t['prompt'] for t in tasks if t['arm']=='N')
        text = f'# Family {item} — Stage12B-R technical review\n\nOriginal task (no source answer):\n\n{question}\n'
        for t in tasks:
            folder=ROOT/'generations'/t['task_id']
            if not (folder/'result.json').exists():continue
            g,checks=checked_generation(t)
            text += f'\n## {t["arm"]} — {g["tokens"]} tokens; {g["finish_reason"]}\n\n'
            if t['arm']=='E':text += f'Request (no gold values):\n\n{t["prompt"]}\n\n'
            text += g['raw_decoded_response']+'\n'
            reviewed.append(dict(task_id=t['task_id'],item_id=item,arm=t['arm'],tokens=g['tokens'],
                finish=g['finish_reason'],input_valid=all(checks.values()),checks=checks,
                generation_sha256=sha(folder/'generation.json')))
        (out/f'{item}.md').write_text(text)
    (out/'index.md').write_text('# Stage12B-R complete raw E/N/O responses\n\nTechnical behavior only; no task/evidence correctness assessed.\n\n'+
        '\n'.join(f'- [Family {i}]({i}.md)' for i in m['validation_ids'])+'\n')
    path=ROOT/'audit/review_packets'/f'{now().replace(":", "")}.json'
    save(path,dict(at=now(),correctness_opened=False,rows=reviewed))
    for r in reviewed:print(r['task_id'],r['tokens'],r['finish'],'input_valid',r['input_valid'])
    print('REVIEW_PACKET',path)


if __name__=='__main__':
    packet()
