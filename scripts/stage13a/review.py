"""Receipt checks and response-only review; arm-separated immutable decisions."""
import argparse,hashlib,re
from scripts.stage13a.execution import ROOT,load,save,sha,now,fingerprint
from scripts.stage12br.protocol import validity
from visual_reasoning.stage8b.v2_scoring import extract_answer

def tasks(phase):return load(ROOT/'audit'/f'phase{phase}_execution.json')['tasks']

def blind_guard(arm):
    if arm!='I_EQ':assert (ROOT/'audit/I_EQ_scoring_closed.json').exists(),'Close all Instruct scoring/QC before opening Thinking responses'


def technical_path(tid):
    resolved=ROOT/'audit/technical_adjudications'/f'{tid}.json'
    return resolved if resolved.exists() else ROOT/'audit/technical_decisions'/f'{tid}.json'

def technical(tid):return load(technical_path(tid))

def adjudicate(tid,outcome,reason):
    old=load(ROOT/'audit/technical_decisions'/f'{tid}.json');p=load(ROOT/'audit/review_packets'/f'{tid}.json')
    assert not (ROOT/'audit/first_scores'/f'{tid}.json').exists(), 'Resolve technical ambiguity before correctness'
    blind_guard(p['arm'])
    if outcome is None and not p['cap_hit']:outcome='__NO_ANSWER__'
    save(ROOT/'audit/technical_adjudications'/f'{tid}.json',dict(old,at=now(),outcome=outcome,scoreable=outcome is not None,
        validity=validity(all(p['checks'].values()),outcome is not None,p['cap_hit'],outcome is None),
        reason=reason,original_sha256=sha(ROOT/'audit/technical_decisions'/f'{tid}.json'),
        review_scope='Expanded own-response semantic adjudication before correctness; original decision preserved.',correctness_used=False))

def checked(t):
    folder=ROOT/'generations'/t['task_id'];g=load(folder/'generation.json');inp=load(folder/'input.json');r=load(folder/'result.json');cfg=load(ROOT/'config.json')
    assert r['generation_sha256']==sha(folder/'generation.json') and r['input_sha256']==sha(folder/'input.json')
    assert r['task_sha256']==g['task_sha256']==inp['task_sha256']==fingerprint(t)
    images=[c for m in inp['messages'] for c in m['content'] if c['type']=='image']
    text=[c['text'] for m in inp['messages'] for c in m['content'] if c['type']=='text']
    prefix=t.get('prefix','');suffix='<|im_start|>assistant\n'+('<think>\n' if t['model_key']=='T' else '')
    checks=dict(task_exact=inp['task']==t,prompt_exact=text==[t['prompt']],
        single_user=len(inp['messages'])==1 and inp['messages'][0]['role']=='user',
        image_payload=len(images)==len(inp['prepared_image_pixel_sha256'])==int(bool(t['image'])),
        image_receipt=inp['image_present']==bool(t['image']) and inp['image_sha256']==t['image_sha256'],
        visual_tokens=(g['visual_tokens']>0)==bool(t['image']),
        template=inp['chat_prompt'].endswith(suffix+prefix),
        output_token_receipt=g['tokens']==len(g['generated_token_ids']),
        prompt_token_receipt=g['prompt_tokens']==len(g['prompt_token_ids']),
        config=g['config_sha256']==sha(ROOT/'config.json'),seed=g['seed']==t['seed'],
        sampling=g['sampling']==dict(cfg['models'][t['model_key']]['recipe'],max_tokens=t['cap']),
        cap_consistent=g['cap_hit']==(g['finish_reason']=='length') and (not g['cap_hit'] or g['tokens']==t['cap']))
    if t['image']:checks['image_exact']=sha(t['image'])==t['image_sha256'] and images[0]['image']==t['image']
    else:checks['no_image_token']=not set([151652,151653,151655,151656]).intersection(g['prompt_token_ids'])
    if t.get('prefix_path'):checks['prefix_exact']=sha(t['prefix_path'])==t['prefix_sha256']
    assert all(checks.values()),(t['task_id'],checks)
    return g,checks

def packets(phase,arm):
    blind_guard(arm)
    cohort={r['item_id']:r for r in load(ROOT/'stage13a_frozen96_manifest.json')['rows']}
    for t in tasks(phase):
        if t['arm']!=arm:continue
        path=ROOT/'audit/review_packets'/f"{t['task_id']}.json"
        if path.exists() or not (ROOT/'generations'/t['task_id']/'result.json').exists():continue
        g,checks=checked(t);raw=g['raw_decoded_response'];row=cohort[t['item_id']]
        seen=set();parts=[];offset=0
        for p in re.split(r'(?:\n[ \t]*){2,}',raw):
            pos=raw.find(p,offset);offset=pos+len(p)
            if p not in seen:parts.append(dict(offset=pos,text=p));seen.add(p)
        save(path,dict(at=now(),task_id=t['task_id'],item_id=t['item_id'],family_id=t['family_id'],arm=arm,
            question=t['prompt'] if arm.startswith('E_') else row['question'],options=[] if arm.startswith('E_') else row['options'],
            raw=raw,tokens=g['tokens'],cap_hit=g['cap_hit'],finish_reason=g['finish_reason'],checks=checks,
            extraction=None if arm.startswith('E_') else extract_answer(raw,row['options']),unique_paragraphs=parts,
            generation_sha256=sha(ROOT/'generations'/t['task_id']/'generation.json'),
            scope='Own response only, no gold/paired outcomes; replay scores new continuation only.'))

def show(phase,arm,start=0,n=12,tail=1600,full=False):
    packets(phase,arm)
    pending=[]
    for t in tasks(phase):
        p=ROOT/'audit/review_packets'/f"{t['task_id']}.json"
        if t['arm']==arm and p.exists() and not (ROOT/'audit/technical_decisions'/p.name).exists():pending.append(load(p))
    for p in pending[start:start+n]:
        print('\nTASK',p['task_id'],'TOKENS',p['tokens'],'STOP',p['finish_reason'],'QUESTION',p['question'])
        print('RESPONSE',('\n\n'.join(x['text'] for x in p['unique_paragraphs'])) if full else p['raw'][-tail:])
    print('PENDING_AVAILABLE',len(pending))

def record(tid,outcome,reason,ambiguous=False,scope='Terminal commitment with own-response context; longer context examined if ambiguous'):
    p=ROOT/'audit/review_packets'/f'{tid}.json';r=load(p)
    blind_guard(r['arm'])
    if outcome is None and not r['cap_hit']:
        outcome='__NO_ANSWER__';ambiguous=True
        reason+=' Normal-stop refusal/no-answer is a resolved scientific failure under Stage13A.'
    assert outcome is None or isinstance(outcome,str) and outcome
    flags=validity(all(r['checks'].values()),outcome is not None,r['cap_hit'],outcome is None)
    save(ROOT/'audit/technical_decisions'/f'{tid}.json',dict(at=now(),task_id=tid,scoreable=outcome is not None,
        outcome=outcome,reason=reason,ambiguous=ambiguous,packet_sha256=sha(p),validity=flags,correctness_used=False,review_scope=scope))

def seal_arm(phase,arm):
    paths=[technical_path(t['task_id']) for t in tasks(phase) if t['arm']==arm]
    assert paths
    save(ROOT/'audit'/f'phase{phase}_{arm}_technical_seal.json',dict(at=now(),n=len(paths),files={str(p):sha(p) for p in paths},correctness_opened=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase');p.add_argument('arm');p.add_argument('--start',type=int,default=0);p.add_argument('--n',type=int,default=12);p.add_argument('--tail',type=int,default=1600);p.add_argument('--full',action='store_true');a=p.parse_args();show(**vars(a))
