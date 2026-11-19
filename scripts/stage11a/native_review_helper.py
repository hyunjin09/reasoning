"""Blind packet display and literal-quote recording; contains no automatic scorer."""
import json,bisect,sys
from scripts.stage11a.common import ROOT,load,save,sha,now

ASSIGN=ROOT/'packets/native_assignment_main_v2.json'

def packet(index):
    a=load(ASSIGN)['rows'][index];return a,load(a['packet'])

def show(index,start=0,count=80):
    a,p=packet(index)
    print('INDEX',index,'ID',p['packet_id'],'QUESTION',p['question'])
    print('FACTS',json.dumps([{k:f.get(k) for k in ['fact_id','gold_value','probe_request']} for f in p['facts']],ensure_ascii=False))
    print('TOKENS',p['reasoning_tokens'],'UNIQUE_PARAGRAPHS',len(p['unique_paragraphs']),'UNIQUE_CHARS',sum(len(r['text']) for r in p['unique_paragraphs']))
    for j,r in enumerate(p['unique_paragraphs'][start:start+count],start):
        print('PARAGRAPH',j,'FIRST_TOKEN',r['occurrences'][0]['token_start']-p['token_offset_origin'],'OCCURRENCES',len(r['occurrences']))
        print(r['text'])
    print('DISPLAYED',start,'TO',min(start+count,len(p['unique_paragraphs'])),'OF',len(p['unique_paragraphs']))

def write(index,state,reason,facts):
    a,p=packet(index);assert len(facts)==len(p['facts']);quotes=[];times=[];complete=[]
    for supplied,gold in zip(facts,p['facts']):
        supplied['fact_id']=gold['fact_id']
        for q in supplied.get('quotes',[]):assert q in p['reasoning_text'],q;quotes.append(q)
        local=[]
        for q in supplied.get('correct_quotes',[]):
            assert q in p['reasoning_text'];local.append(bisect.bisect_right(p['token_character_offsets'],p['reasoning_text'].index(q))-1)
        if local:times.append(min(local));complete.append(min(local))
    r=dict(packet_id=p['packet_id'],packet_sha256=sha(a['packet']),reviewer='main',state=state,reason=reason,
        coverage_complete=True,facts=facts,evidence_quotes=list(dict.fromkeys(quotes)),
        first_evidence_token=min(times) if times else None,
        first_sufficient_token=max(complete) if len(complete)==len(facts) else None)
    save(ROOT/'audit/reviewer_main/native_drafts'/f"{p['packet_id']}.json",r)
    print('REVIEWED',index,p['packet_id'],state)

def f(status,reason,*quotes,correct=None):
    return dict(status=status,reason=reason,quotes=list(quotes),correct_quotes=list(quotes) if status=='CORRECT' else list(correct or []))

def seal():
    rr=[]
    for a in load(ASSIGN)['rows']:
        r=load(ROOT/'audit/reviewer_main/native_drafts'/f"{a['packet_id']}.json");assert r['packet_sha256']==sha(a['packet']);rr.append(r)
    save(ROOT/'annotations/native_main.json',dict(at=now(),sealed=True,reviewer='main',assignment_sha256=sha(ASSIGN),
        probe_outputs_opened=False,mode_correctness_opened=False,rows=rr))

if __name__=='__main__':show(*map(int,sys.argv[1:]))
