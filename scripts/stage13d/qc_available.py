"""Stream the unchanged arm-separated QC set without showing first labels."""
import argparse,math,re
from scripts.stage13d.scoring import selected,guard
from scripts.stage13d.review import rows
from scripts.stage13d.common import *
def show(arm,limit,tail):
    guard(arm);tt=selected(arm);rr=rows()
    random=set(sorted([t['task_id'] for t in tt],key=lambda x:digest('stage13d-v1|score-audit|'+x))[:math.ceil(.2*len(tt))]);todo=[]
    for t in tt:
        tid=t['task_id'];p=ROOT/'audit/technical_decisions'/f'{tid}.json'
        if not p.exists() or not (ROOT/'audit/first_scores'/f'{tid}.json').exists() or (ROOT/'audit/second_scores'/f'{tid}.json').exists():continue
        a=load(p);math_amb=not rr[t['item_id']]['options'] and a['outcome'] and not re.fullmatch(r'-?\d+(?:\.\d+)?',a['outcome'])
        if tid in random or a['ambiguous'] or a['cap_hit'] or math_amb:todo.append((t,a))
    for t,a in todo[:limit]:
        g=load(ROOT/'generations'/t['task_id']/'generation.json')
        print('\nTASK',t['task_id'],'GOLD',rr[t['item_id']]['answer'],'COMMITMENT',a['outcome'],'VALID',a['validity']['TECHNICALLY_VALID'],'CAP',a['cap_hit'])
        print(g['raw_decoded_response'][-tail:])
    print('AVAILABLE_QC_PENDING',len(todo))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('arm',choices=CONDITIONS);p.add_argument('--limit',type=int,default=20);p.add_argument('--tail',type=int,default=500);a=p.parse_args();show(a.arm,a.limit,a.tail)
