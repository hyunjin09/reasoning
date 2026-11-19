"""Own-response validity first; correctness and paired inference are separate."""
import argparse,math,re
from scripts.stage13d.common import *
from visual_reasoning.stage8b.v2_scoring import extract_answer,equivalent
from scripts.stage12br.protocol import validity
def tasks():return load(ROOT/'stage13d_semantic_seed_manifest.json')['tasks']
def rows():return {r['item_id']:r for r in load(ROOT/'stage13d_frozen24_manifest.json')['rows']}
def checked(t):
    folder=ROOT/'generations'/t['task_id'];g=load(folder/'generation.json');i=load(folder/'input.json');r=load(folder/'result.json');cfg=load(ROOT/'config.json')
    assert r['generation_sha256']==sha(folder/'generation.json') and r['input_sha256']==sha(folder/'input.json')
    assert g['task_sha256']==i['task_sha256']==r['task_sha256']==fingerprint(t)
    assert i['task']==t and i['chat_prompt']==t['chat_prompt'] and not i['image_present']
    assert g['prompt_token_ids']==t['prompt_token_ids'] and g['visual_tokens']==0 and g['tokens']==len(g['generated_token_ids'])
    assert not set([151652,151653,151655,151656]).intersection(g['prompt_token_ids'])
    assert g['sampling']==dict(cfg['models']['I']['recipe'],max_tokens=32768) and g['seed']==t['seed']
    assert g['config_sha256']==sha(ROOT/'config.json') and g['cap_hit']==(g['finish_reason']=='length')
    assert not g['cap_hit'] or g['tokens']==32768
    return g
def canonical(value,row):
    if not value:return None
    s=value.strip().strip('*').strip().strip('$').strip().replace('\\text{','').replace('\\mathrm{','').rstrip('}')
    if row['options']:
        m=re.fullmatch(r'\(?([A-E])\)?[.\s]*',s)
        if m:return m[1]
        labeled=re.fullmatch(r'([A-E])[.)]\s*(.+)',s)
        if labeled:
            index=ord(labeled[1])-65
            if index<len(row['options']) and equivalent(labeled[2].strip('*').strip(),row['options'][index]) is True:return labeled[1]
        matches=[chr(65+k) for k,x in enumerate(row['options']) if equivalent(value,x) is True]
        if len(matches)==1:return matches[0]
        return None
    return value
def record(tid,outcome,reason,ambiguous=True):
    t=next(t for t in tasks() if t['task_id']==tid);g=checked(t)
    if outcome is None and not g['cap_hit']:outcome='__NO_ANSWER__'
    assert outcome is None or isinstance(outcome,str)
    save(ROOT/'audit/technical_decisions'/f'{tid}.json',dict(at=now(),task_id=tid,item_id=t['item_id'],condition=t['condition'],
        outcome=outcome,reason=reason,ambiguous=ambiguous,cap_hit=g['cap_hit'],validity=validity(True,outcome is not None,g['cap_hit'],outcome is None),
        generation_sha256=sha(ROOT/'generations'/tid/'generation.json'),correctness_used=False))
def prepare(arm=None):
    rr=rows();pending=[]
    for t in tasks():
        tid=t['task_id'];p=ROOT/'audit/technical_decisions'/f'{tid}.json'
        if arm and t['condition']!=arm or p.exists() or not (ROOT/'generations'/tid/'result.json').exists():continue
        g=checked(t);raw=g['raw_decoded_response'];e=extract_answer(raw,[]);value=canonical(e['extracted'],rr[t['item_id']])
        safe=not g['cap_hit'] and value is not None and e['method'] in ['local_balanced_box','local_plain_answer','local_explicit_answer']
        tail=raw[e['span'][1]:] if e['span'] else raw
        safe=safe and len(tail)<450 and not re.search(r'\b(wait|instead|reconsider|incorrect|mistake|however)\b',tail,re.I)
        if safe:record(tid,value,'Explicit terminal answer extracted from own response; no post-answer reconsideration marker. '+e['method'],False)
        else:pending.append(tid)
    print('PENDING_REVIEW',pending)
def show(arm=None,limit=20,tail=1400):
    rr=rows();pending=[]
    for t in tasks():
        tid=t['task_id']
        if arm and t['condition']!=arm or (ROOT/'audit/technical_decisions'/f'{tid}.json').exists() or not (ROOT/'generations'/tid/'result.json').exists():continue
        pending.append(t)
    for t in pending[:limit]:
        g=checked(t);r=rr[t['item_id']]
        print('\nTASK',t['task_id'],'TOKENS',g['tokens'],'CAP',g['cap_hit'],'OPTIONS',r['options'])
        print(g['raw_decoded_response'][-tail:])
    print('PENDING',len(pending))
def initial_gate():
    selected=[t for t in tasks() if t['initial8']];stats={};files={}
    for arm in CONDITIONS:
        aa=[t for t in selected if t['condition']==arm];dec=[]
        for t in aa:
            p=ROOT/'audit/technical_decisions'/f"{t['task_id']}.json";dec.append(load(p));files[str(p)]=sha(p)
        n=sum(not x['validity']['TECHNICALLY_VALID'] for x in dec)
        stats[arm]=dict(total=len(dec),missing=n,rate=n/len(dec),passed=n/len(dec)<=.2)
    result=dict(at=now(),passed=all(x['passed'] for x in stats.values()),arms=stats,files=files,correctness_opened=False)
    save(ROOT/'audit/semantic_initial8_gate.json',result);print(result['passed'],stats)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','show','gate']);p.add_argument('--arm');p.add_argument('--limit',type=int,default=20);p.add_argument('--tail',type=int,default=1400);a=p.parse_args()
    if a.action=='prepare':prepare(a.arm)
    elif a.action=='show':show(a.arm,a.limit,a.tail)
    else:initial_gate()
