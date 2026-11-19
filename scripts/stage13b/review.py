"""Own-response technical review with exact input/receipt checks, before labels."""
import argparse,re
from scripts.stage13b.execution import ROOT,load,save,sha,now,fingerprint
from scripts.stage12br.protocol import validity
from visual_reasoning.stage8b.v2_scoring import extract_answer,equivalent


def tasks(phase=None,cell=None):
    m=load(ROOT/'stage13b_seed_manifest.json');rows=m['technical']+m['new_scientific']
    return [t for t in rows if (phase is None or t['phase']==phase) and (cell is None or t['scale']+'_'+t['arm']==cell)]


def source(t):
    name='stage13b_technical4_manifest.json' if t['phase']=='technical' else 'stage13b_frozen48_manifest.json'
    return next(r for r in load(ROOT/name)['rows'] if r['family_id']==t['family_id'])


def technical_path(tid):
    p=ROOT/'audit/technical_adjudications'/f'{tid}.json'
    return p if p.exists() else ROOT/'audit/technical_decisions'/f'{tid}.json'


def technical(tid):return load(technical_path(tid))


def checked(t):
    folder=ROOT/'generations'/t['task_id'];g=load(folder/'generation.json');inp=load(folder/'input.json');r=load(folder/'result.json');cfg=load(ROOT/'config.json')
    assert r['generation_sha256']==sha(folder/'generation.json') and r['input_sha256']==sha(folder/'input.json')
    assert r['task_sha256']==g['task_sha256']==inp['task_sha256']==fingerprint(t)
    images=[c for m in inp['messages'] for c in m['content'] if c['type']=='image']
    text=[c['text'] for m in inp['messages'] for c in m['content'] if c['type']=='text']
    checks=dict(task_exact=inp['task']==t,prompt_exact=text==[t['prompt']],
        single_user=len(inp['messages'])==1 and inp['messages'][0]['role']=='user',
        image_payload=len(images)==len(inp['prepared_image_pixel_sha256'])==int(bool(t['image'])),
        image_receipt=inp['image_present']==bool(t['image']) and inp['image_sha256']==t['image_sha256'],
        visual_tokens=(g['visual_tokens']>0)==bool(t['image']),
        template=inp['chat_prompt'].endswith('<|im_start|>assistant\n'+('<think>\n' if t['mode']=='T' else '')),
        output_token_receipt=g['tokens']==len(g['generated_token_ids']),prompt_token_receipt=g['prompt_tokens']==len(g['prompt_token_ids']),
        config=g['config_sha256']==sha(ROOT/'config.json'),seed=g['seed']==t['seed'],
        sampling=g['sampling']==dict(cfg['models'][t['model_key']]['recipe'],max_tokens=t['cap']),
        cap_consistent=g['cap_hit']==(g['finish_reason']=='length') and (not g['cap_hit'] or g['tokens']==t['cap']))
    if t['image']:checks['image_exact']=sha(t['image'])==t['image_sha256'] and images[0]['image']==t['image']
    else:checks['no_image_token']=not set([151652,151653,151655,151656]).intersection(g['prompt_token_ids'])
    assert all(checks.values()),(t['task_id'],checks)
    return g,checks


def packets(phase,cell):
    for t in tasks(phase,cell):
        path=ROOT/'audit/review_packets'/f"{t['task_id']}.json"
        if path.exists() or not (ROOT/'generations'/t['task_id']/'result.json').exists():continue
        g,checks=checked(t);row=source(t);raw=g['raw_decoded_response']
        save(path,dict(at=now(),task_id=t['task_id'],item_id=t['item_id'],family_id=t['family_id'],scale=t['scale'],arm=t['arm'],
            question=row['question'],options=row['options'],raw=raw,tokens=g['tokens'],cap_hit=g['cap_hit'],finish_reason=g['finish_reason'],
            checks=checks,extraction=extract_answer(raw,row['options']),generation_sha256=sha(ROOT/'generations'/t['task_id']/'generation.json'),
            scope='Own response only, no correctness or paired outcomes.'))


def record(tid,outcome,reason,ambiguous=False,adjudication=False):
    p=ROOT/'audit/review_packets'/f'{tid}.json';r=load(p)
    assert not (ROOT/'audit/first_scores'/f'{tid}.json').exists(),'Resolve extraction before correctness'
    if outcome is None and not r['cap_hit']:
        outcome='__NO_ANSWER__';ambiguous=True
        reason+=' Normal-stop no-answer/refusal is scientific failure, not technical missingness.'
    assert outcome is None or isinstance(outcome,str) and outcome
    flags=validity(all(r['checks'].values()),outcome is not None,r['cap_hit'],outcome is None)
    save(ROOT/'audit'/('technical_adjudications' if adjudication else 'technical_decisions')/f'{tid}.json',
         dict(at=now(),task_id=tid,outcome=outcome,scoreable=outcome is not None,reason=reason,ambiguous=ambiguous,
              validity=flags,packet_sha256=sha(p),correctness_used=False))


def automatic(phase,cell):
    """Only normal-stop terminal boxes; all caps/unclear commitments need review."""
    packets(phase,cell);n=0
    for t in tasks(phase,cell):
        path=ROOT/'audit/review_packets'/f"{t['task_id']}.json"
        if not path.exists() or technical_path(t['task_id']).exists():continue
        p=load(path);e=p['extraction']
        if p['cap_hit'] or e['method']!='local_balanced_box':continue
        if t['mode']=='T' and '</think>' not in p['raw']:continue
        # The final balanced box must end the response apart from LaTeX/punctuation.
        trailing=p['raw'][e['span'][1]+1:]
        if re.sub(r'[\s$\\\[\]().!*#{}]','',trailing):continue
        value=e['extracted'];options=p['options']
        if options:
            letters=[chr(65+i) for i in range(len(options))]
            if value.strip().strip('().') in letters:value=value.strip().strip('().')
            else:
                matches=[letters[i] for i,x in enumerate(options) if equivalent(value,x) is True]
                if len(matches)!=1:continue
                value=matches[0]
        record(t['task_id'],value,'Normal-stop unretracted terminal balanced box; exact extraction span preserved.',False);n+=1
    return n


def show(phase,cell,n=12,tail=1600,start=0,full=False):
    packets(phase,cell)
    selected=[t for t in tasks(phase,cell) if (ROOT/'audit/review_packets'/f"{t['task_id']}.json").exists() and not technical_path(t['task_id']).exists()]
    for t in selected[start:start+n]:
        p=load(ROOT/'audit/review_packets'/f"{t['task_id']}.json")
        print('\nTASK',t['task_id'],'TOKENS',p['tokens'],'STOP',p['finish_reason'],'OPTIONS',p['options'])
        print('QUESTION',p['question']);print('RESPONSE',p['raw'] if full else p['raw'][-tail:])
    print('PENDING',len(selected))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase');parser.add_argument('cell');parser.add_argument('--n',type=int,default=12);parser.add_argument('--tail',type=int,default=1600);parser.add_argument('--start',type=int,default=0);parser.add_argument('--full',action='store_true')
    show(**vars(parser.parse_args()))
