import argparse,math,re
from scripts.stage13d.review import *
def selected(arm):
    gate=load(ROOT/'audit/semantic_initial8_gate.json')
    return [t for t in tasks() if t['condition']==arm and (gate['passed'] or t['initial8'])]
def guard(arm):
    i=CONDITIONS.index(arm)
    if i:assert (ROOT/'audit'/f'{CONDITIONS[i-1]}_scoring_closed.json').exists()
def record(tid,correct,reason,second=False):
    t=next(t for t in tasks() if t['task_id']==tid);guard(t['condition'])
    a=load(ROOT/'audit/technical_decisions'/f'{tid}.json')
    assert (correct is None)==(not a['validity']['TECHNICALLY_VALID'])
    assert correct is None or type(correct)==bool
    save(ROOT/'audit'/('second_scores' if second else 'first_scores')/f'{tid}.json',dict(at=now(),task_id=tid,
        item_id=t['item_id'],condition=t['condition'],correct=correct,reason=reason,
        technical_sha256=sha(ROOT/'audit/technical_decisions'/f'{tid}.json'),paired_labels_opened=False,
        scope='Same-agent second pass, not independent-rater reliability' if second else 'Arm-separated first score'))
def first(arm):
    guard(arm);rr=rows();pending=[]
    for t in selected(arm):
        tid=t['task_id'];a=load(ROOT/'audit/technical_decisions'/f'{tid}.json');row=rr[t['item_id']]
        if (ROOT/'audit/first_scores'/f'{tid}.json').exists():continue
        value=a['outcome']
        if not a['validity']['TECHNICALLY_VALID']:record(tid,None,'Frozen technical missingness; never a scientific error.');continue
        if value=='__NO_ANSWER__':record(tid,False,'Normal-stop no-answer/refusal is scientific failure.');continue
        if row['options']:
            assert value in [chr(65+i) for i in range(len(row['options']))],(tid,value)
            correct=value==row['answer']
        else:correct=equivalent(value.strip().strip('*').strip(),row['answer'])
        if correct is None:pending.append(dict(task_id=tid,outcome=value,gold=row['answer']));continue
        record(tid,correct,'Inherited option / exact / bounded numeric1e-6 MathVision equivalence; surrounding Markdown bold markers ignored.')
    print('MANUAL_EQUIVALENCE',pending)
def seal(arm):
    guard(arm);tt=selected(arm);paths=[ROOT/'audit/first_scores'/f"{t['task_id']}.json" for t in tt]
    random=sorted([t['task_id'] for t in tt],key=lambda x:digest('stage13d-v1|score-audit|'+x))[:math.ceil(.2*len(tt))]
    ambiguous=[]
    for t in tt:
        a=load(ROOT/'audit/technical_decisions'/f"{t['task_id']}.json")
        if a['ambiguous'] or a['cap_hit'] or (not rows()[t['item_id']]['options'] and a['outcome'] and not re.fullmatch(r'-?\d+(?:\.\d+)?',a['outcome'])):ambiguous.append(t['task_id'])
    save(ROOT/'audit'/f'{arm}_first_seal.json',dict(at=now(),files={str(p):sha(p) for p in paths},random=random,ambiguous=ambiguous,second=sorted(set(random+ambiguous)),paired_outcomes_opened=False))
def show_second(arm,limit=20,tail=650):
    guard(arm);r=rows();ids=load(ROOT/'audit'/f'{arm}_first_seal.json')['second'];todo=[]
    for tid in ids:
        if (ROOT/'audit/second_scores'/f'{tid}.json').exists():continue
        todo.append(tid)
    for tid in todo[:limit]:
        a=load(ROOT/'audit/technical_decisions'/f'{tid}.json');g=load(ROOT/'generations'/tid/'generation.json')
        print('\nTASK',tid,'GOLD',r[a['item_id']]['answer'],'EXTRACTED',a['outcome'],'CAP',a['cap_hit'],'VALID',a['validity']['TECHNICALLY_VALID'])
        print(g['raw_decoded_response'][-tail:])
    print('QC_PENDING',len(todo))
def close(arm):
    seal=load(ROOT/'audit'/f'{arm}_first_seal.json');reviews=[]
    for p,h in seal['files'].items():assert sha(p)==h
    for tid in seal['second']:
        a=load(ROOT/'audit/first_scores'/f'{tid}.json');b=load(ROOT/'audit/second_scores'/f'{tid}.json');same=a['correct']==b['correct']
        if not same:assert load(ROOT/'audit/score_adjudications'/f'{tid}.json')['resolved']
        reviews.append(dict(task_id=tid,same=same,second_sha256=sha(ROOT/'audit/second_scores'/f'{tid}.json')))
    save(ROOT/'audit'/f'{arm}_scoring_closed.json',dict(at=now(),n=len(seal['files']),reviews=reviews,paired_labels_opened=False))
def final_score(tid):
    p=ROOT/'audit/score_adjudications'/f'{tid}.json'
    return load(p if p.exists() else ROOT/'audit/first_scores'/f'{tid}.json')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['first','seal','qc','close']);p.add_argument('arm',choices=CONDITIONS);p.add_argument('--limit',type=int,default=20);p.add_argument('--tail',type=int,default=650);a=p.parse_args()
    if a.action=='first':first(a.arm)
    elif a.action=='seal':seal(a.arm)
    elif a.action=='close':close(a.arm)
    else:show_second(a.arm,a.limit,a.tail)
