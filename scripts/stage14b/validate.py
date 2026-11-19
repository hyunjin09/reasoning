"""Response-only receipt audit; no gold/accuracy endpoint in technical validation."""
from collections import Counter,defaultdict
from scripts.stage14b.common import *
from scripts.stage14b.protocol import extract


def checked(t):
    p=checked_result(t)
    if p is None:return None
    g=load(p.parent/'generation.json');inp=load(p.parent/'input.json');cfg=load(ROOT/'spec/frozen_run_config.json')
    texts=[c['text'] for message in inp['messages'] for c in message['content'] if c['type']=='text']
    images=[c for message in inp['messages'] for c in message['content'] if c['type']=='image']
    checks=dict(task=inp['task']==t,prompt=texts==[t['prompt']],user=len(inp['messages'])==1 and inp['messages'][0]['role']=='user',
        image_count=len(images)==len(inp['prepared_image_pixel_sha256'])==int(bool(t['image'])),
        image_hash=inp['image_sha256']==t['image_sha256'],image_presence=(g['visual_tokens']>0)==bool(t['image']),
        template=inp['chat_prompt'].endswith('<|im_start|>assistant\n'+('<think>\n' if t['model_key']=='T' else '')),
        config=g['config_sha256']==sha(ROOT/'spec/frozen_run_config.json'),
        output_ids=g['tokens']==len(g['generated_token_ids']),prompt_ids=g['prompt_tokens']==len(g['prompt_token_ids']),
        seed=g['seed']==t['seed'],sampling=g['sampling']==dict(cfg['models'][t['model_key']]['recipe'],max_tokens=t['cap']),
        cap=g['cap_hit']==(g['finish_reason']=='length') and (not g['cap_hit'] or g['tokens']==t['cap']),
        finish=g['finish_reason'] in ('length','stop'))
    if t['image']:
        checks['pixels']=sha(t['image'])==t['image_sha256'] and images[0]['image']==t['image']
        checks['resize']=images[0]['min_pixels']==602112 and images[0]['max_pixels']==4014080
    else:checks['no_image_special_tokens']=not set([151652,151653,151655,151656]).intersection(g['prompt_token_ids'])
    assert all(checks.values()),(t['task_id'],checks)
    return dict(checks=checks,generation=g,receipt=str(p))


def preflight():
    tasks=all_tasks('preflight');rr=[];synthetic=defaultdict(list)
    for t in tasks:
        r=checked(t);assert r is not None,('preflight incomplete',t['task_id'])
        g=r['generation']
        rr.append(dict(task_id=t['task_id'],model=t['model_key'],condition=t['condition'],tokens=g['tokens'],
            finish_reason=g['finish_reason'],visual_tokens=g['visual_tokens'],checks=r['checks'],receipt=r['receipt'],
            response_sha256=hashlib.sha256(g['raw_decoded_response'].encode()).hexdigest(),latency_seconds=g['request_latency_seconds']))
        if t['condition']=='seedcheck':synthetic[t['model_key']].append(g['generated_token_ids'])
    replay={m:len(ids)==2 and ids[0]==ids[1] for m,ids in synthetic.items()}
    review=load(ROOT/'audit/preflight_response_review.json')
    assert review['correctness_used'] is False and review['extraction_and_format_review_pass']
    assert set(review['reviewed_task_ids'])<=set(t['task_id'] for t in tasks)
    passed=len(rr)==24 and all(replay.values())
    result=dict(at=now(),pass_=passed,rows=rr,same_seed_replay=replay,correctness_used=False,
        response_review_sha256=sha(ROOT/'audit/preflight_response_review.json'),technical_tests=15,
        scope='Implementation/input/missingness/replay gate only, no accuracy/completion-rate tuning')
    result['pass']=result.pop('pass_')
    save(ROOT/'audit/preflight_validation.json',result)
    print({'pass':passed,'n':len(rr),'same_seed_replay':replay})

if __name__=='__main__':preflight()
