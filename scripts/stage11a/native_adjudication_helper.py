"""Record explicit human/agent adjudication choices; never choose a label."""
import copy,json,sys
from scripts.stage11a.common import ROOT,load,save,sha,now
from scripts.stage11a.review_validation import validate_native

PACKETS=ROOT/'packets/native_adjudication.json'

def request(index):
    r=load(PACKETS)['rows'][index]
    return r,load(r['packet'])

def show(index,start=None,count=40):
    r,p=request(index)
    print('INDEX',index,'ID',p['packet_id'],'QUESTION',p['question'])
    print('FACTS',json.dumps(p['facts'],ensure_ascii=False))
    print('REASON',r['reason'],'TOKENS',p['reasoning_tokens'],'PARAGRAPHS',len(p['unique_paragraphs']))
    if start is None:print('REVIEWS',json.dumps(r['reviews'],ensure_ascii=False,indent=2))
    else:
        for j,v in enumerate(p['unique_paragraphs'][start:start+count],start):print(j,v['text'])
        print('DISPLAYED',start,min(start+count,len(p['unique_paragraphs'])))

def write(index,row,reason):
    req,p=request(index);r=copy.deepcopy(row)
    assert reason.strip()
    r.update(packet_sha256=sha(req['packet']),adjudicator='main',adjudication_reason=reason)
    validate_native(r,p)
    save(ROOT/'audit/native_adjudication_drafts'/f"{p['packet_id']}.json",r)
    print('ADJUDICATED',index,p['packet_id'],r['state'])

def adopt(index,who,reason):
    req,_=request(index);write(index,req['reviews'][who],reason)

def seal():
    rows=[]
    for req in load(PACKETS)['rows']:
        r=load(ROOT/'audit/native_adjudication_drafts'/f"{req['packet_id']}.json")
        validate_native(r,load(req['packet']));rows.append(r)
    save(ROOT/'annotations/native_adjudication.json',dict(at=now(),sealed=True,packet_sha256=sha(PACKETS),
        probe_outputs_opened=False,mode_correctness_opened=False,rows=rows))

if __name__=='__main__':show(*map(int,sys.argv[1:]))
