"""Deterministic response excerpts for semantic review; never assigns labels."""
import re
from scripts.stage12ts.common import ROOT,load,save,sha


def inspect(tid):
    p=ROOT/'audit/technical_packets'/f'{tid}.json';d=load(p);s=d['raw']
    unique=[q for q in d['unique_paragraphs'] if q['offset']==q['first_occurrence']]
    if len(s)<=22000:
        spans=[(0,len(s))]
    else:
        spans=[(0,1200),(max(0,len(s)-4000),len(s))]
        for f in [j/12 for j in range(1,12)]:
            a=int(len(s)*f);spans.append((a,min(a+700,len(s))))
        candidates=[q for q in unique if re.search(r'answer (?:is|should|would|must)|answer:|therefore.{0,60}(?:answer|option)|boxed',q['text'],re.I)]
        for q in candidates:
            a=q['offset'];spans.append((max(0,a-100),min(len(s),a+min(len(q['text']),500)+350)))
        spans=sorted(spans);merged=[]
        for a,b in spans:
            if merged and a<=merged[-1][1]:merged[-1]=(merged[-1][0],max(b,merged[-1][1]))
            else:merged.append((a,b))
        spans=merged
    dest=ROOT/'audit/inspection_packets'/f'{tid}.json'
    record=dict(task_id=tid,packet_sha256=sha(p),total_chars=len(s),
                spans=spans,reviewed_chars=sum(b-a for a,b in spans),
                method='Full when <=22000chars; otherwise opening, ending, 11 evenly spaced 700char passages, all task-answer/boxed matches with local context. Excerpts are not full-trace coverage.')
    if not dest.exists():save(dest,record)
    else:assert load(dest)==record
    print(tid,'TOKENS',d['tokens'],'CAP',d['cap_hit'],'CHARS',len(s),'SHOWN',record['reviewed_chars'],'QUESTION',d['question'])
    for a,b in spans:print(f'\nCHARS {a}:{b}\n'+s[a:b])

if __name__=='__main__':
    import sys
    inspect(sys.argv[1])
