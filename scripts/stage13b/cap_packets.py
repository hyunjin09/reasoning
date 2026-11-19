"""Preserve full raw text; losslessly describe an exactly periodic capped tail."""
import re
from scripts.stage13b.execution import ROOT,load,save,sha,now
from scripts.stage13b.review import tasks,technical_path


def make(tid):
    dest=ROOT/'audit/cap_review_packets'/f'{tid}.json'
    if dest.exists():return load(dest)
    p=ROOT/'audit/review_packets'/f'{tid}.json';r=load(p);raw=r['raw'];tail=raw[-8192:];period=None
    for n in range(16,min(2049,len(tail)//4)):
        if tail[:-n]==tail[n:]:period=n;break
    if period:
        k=len(raw)-period-1
        while k>=0 and raw[k]==raw[k+period]:k-=1
        start=k+1;unit=raw[start:start+period];num,rem=divmod(len(raw)-start,period)
        assert raw==raw[:start]+unit*num+unit[:rem]
        compact=raw[:start]+unit*2+f'\n[Exact periodic tail: {num}repeats of{period}characters; remainder{rem}.]\n'+unit[:rem]
    else:compact=raw
    unique=list(dict.fromkeys(re.split(r'(?:\n[ \t]*){2,}',compact)))
    packet=dict(at=now(),task_id=tid,unique_paragraphs=unique,periodic_tail=period,compact=compact,
        original_sha256=sha(p),original_characters=len(raw),dedup_characters=sum(map(len,unique)))
    save(dest,packet);return packet


def show(tid):
    r=make(tid);print('\nTASK',tid,'UNIQUE_CHAR',r['dedup_characters']);print('\n\n'.join(r['unique_paragraphs']))


def inventory(cell):
    for t in tasks('equal',cell):
        p=ROOT/'audit/review_packets'/f"{t['task_id']}.json"
        if not p.exists() or technical_path(t['task_id']).exists():continue
        r=load(p);packet=make(t['task_id']) if r['cap_hit'] else None
        print(t['task_id'],'TOKENS',r['tokens'],'CAP',r['cap_hit'],'UNIQUE_CHARS',packet['dedup_characters'] if packet else None,'EXTRACTION',r['extraction'])
