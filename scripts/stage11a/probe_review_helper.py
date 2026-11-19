"""Manual review support for already frozen, short, mode-blinded probes."""
import json,sys
from scripts.stage11a.common import ROOT,load,save,sha,now
from scripts.stage11a.review_validation import validate_probe

PACKETS=ROOT/'packets/probe_review.json'
REVIEWERS=['main','a','b']

def assigned(who):
    assert who in REVIEWERS
    return load(PACKETS)['rows'][REVIEWERS.index(who)::len(REVIEWERS)]

def show(who,index):
    p=assigned(who)[index]
    print('INDEX',index,'PACKET',p['packet_id'],'ITEM',p['item_id'],'TOKENS',p['tokens'])
    print('FACTS',json.dumps([{k:f.get(k) for k in ['fact_id','gold_value','probe_request']} for f in p['facts']],ensure_ascii=False))
    print(p['text'])

def f(label,reason,*quotes):
    return dict(label=label,reason=reason,quotes=list(quotes))

def write(who,index,facts):
    p=assigned(who)[index]
    assert len(facts)==len(p['facts'])
    for f,g in zip(facts,p['facts']):f['fact_id']=g['fact_id']
    r=dict(packet_id=p['packet_id'],reviewer=who,facts=facts,coverage_complete=True)
    validate_probe(r,p)
    save(ROOT/'audit'/f'reviewer_{who}'/'probe_drafts'/f"{p['packet_id']}.json",r)
    print('REVIEWED',who,index,p['packet_id'])

def seal(who):
    rows=[]
    for p in assigned(who):
        r=load(ROOT/'audit'/f'reviewer_{who}'/'probe_drafts'/f"{p['packet_id']}.json")
        validate_probe(r,p);rows.append(r)
    save(ROOT/'annotations'/f'probe_{who}.json',dict(at=now(),sealed=True,reviewer=who,packet_sha256=sha(PACKETS),
        native_sealed_sha256=sha(ROOT/'annotations/native_final.json'),mode_correctness_opened=False,rows=rows))

def seal_all():
    rows=[];sources={}
    for who in REVIEWERS:
        path=ROOT/'annotations'/f'probe_{who}.json';d=load(path)
        assert d['sealed'] and d['mode_correctness_opened'] is False
        assert d['packet_sha256']==sha(PACKETS) and d['native_sealed_sha256']==sha(ROOT/'annotations/native_final.json')
        rr={r['packet_id']:r for r in d['rows']};pp=assigned(who)
        assert len(rr)==len(d['rows'])==len(pp) and set(rr)=={p['packet_id'] for p in pp}
        for p in pp:validate_probe(rr[p['packet_id']],p)
        rows.extend(d['rows']);sources[str(path)]=sha(path)
    save(ROOT/'annotations/probe_final.json',dict(at=now(),sealed=True,rows=rows,sources_sha256=sources,
        packet_sha256=sha(PACKETS),native_sealed_sha256=sha(ROOT/'annotations/native_final.json'),mode_correctness_opened=False))

if __name__=='__main__':show(sys.argv[1],int(sys.argv[2]))
