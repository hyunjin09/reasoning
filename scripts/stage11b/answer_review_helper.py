"""Manual literal final-answer review with exact supporting quote validation."""
import sys
from scripts.stage11b.common import ROOT,load,save,sha,now

PACKET=ROOT/'packets/discovery_answer_review.json'
def assigned(who):
    rows=load(PACKET)['rows']
    return rows[['main','a','b'].index(who)::3]

def show(who,start,count=4,tail=1600):
    rows=assigned(who)
    for i,p in enumerate(rows[start:start+count],start):
        body=p['text'].rsplit('</think>',1)[-1]
        print('\nINDEX',i,'PACKET',p['packet_id'],'EOS',p['normal_eos'],'CAP',p['at_length_cap'])
        print('OPTIONS',p['options'],'ADAPTER',p['adapter_proposal'])
        print('BODY_CHARS',len(body),'DISPLAY_START',max(0,len(body)-tail));print(body[-tail:])

def write(who,index,answer,quote,reason):
    p=assigned(who)[index]
    if answer is not None:
        assert isinstance(answer,str) and answer.strip()
        assert quote and quote in p['text']
    assert reason
    row=dict(packet_id=p['packet_id'],reviewer=who,answer=answer,quote=quote,reason=reason,at=now())
    save(ROOT/'audit'/f'reviewer_{who}'/'answer_drafts'/f"{p['packet_id']}.json",row)

def seal(who):
    rows=[load(ROOT/'audit'/f'reviewer_{who}'/'answer_drafts'/f"{p['packet_id']}.json") for p in assigned(who)]
    save(ROOT/'annotations'/f'discovery_answers_{who}.json',dict(at=now(),sealed=True,reviewer=who,
        packet_sha256=sha(PACKET),gold_or_correctness_opened=False,rows=rows))

if __name__=='__main__':show(sys.argv[1],*map(int,sys.argv[2:]))
