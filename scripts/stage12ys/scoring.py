"""Arm-separated frozen MathVision grading and explicit evidence-atom review."""
import hashlib,math,re
from scripts.stage12ys.execution import ROOT,load,save,sha,now
from scripts.stage12ys.review import tasks,technical,technical_path
from visual_reasoning.stage8b.v2_scoring import equivalent

LABELS=['CORRECT','INCORRECT','UNSCOREABLE_TECHNICAL']

def packet(tid):
    p=load(ROOT/'audit/review_packets'/f'{tid}.json')
    row=next(r for r in load(ROOT/'stage12ys_frozen96_manifest.json')['rows'] if r['item_id']==p['item_id'])
    return p,row

def record(tid,label,reason,atoms=None,ambiguity=(),second=False):
    p,row=packet(tid);a=technical(tid)
    assert label in LABELS
    assert (label=='UNSCOREABLE_TECHNICAL')==(not a['validity']['TECHNICALLY_VALID'])
    if p['arm'].startswith('E_'):
        assert len(atoms)==len(row['facts']) and set(atoms)<=set('CIU')
        assert label=='UNSCOREABLE_TECHNICAL' or (label=='CORRECT')==all(x=='C' for x in atoms)
    save(ROOT/'audit'/('second_scores' if second else 'first_scores')/f'{tid}.json',dict(at=now(),task_id=tid,
        item_id=p['item_id'],family_id=p['family_id'],arm=p['arm'],label=label,
        correct=None if label=='UNSCOREABLE_TECHNICAL' else label=='CORRECT',reason=reason,atoms=atoms,
        ambiguity=list(ambiguity),technical_sha256=sha(technical_path(tid)),
        scope='Own-arm second pass without first labels/paired outcomes displayed; same-agent QC' if second else 'Own-arm first pass; no paired labels'))

def show_e(selected=None,start=0,n=12,phase='A',arm='E_T'):
    rows=[t for t in tasks(phase) if t['arm']==arm]
    if selected is not None:rows=[t for t in rows if t['task_id'] in selected]
    else:rows=[t for t in rows if (ROOT/'audit/review_packets'/f"{t['task_id']}.json").exists() and not (ROOT/'audit/first_scores'/f"{t['task_id']}.json").exists()]
    for t in rows[start:start+n]:
        p,row=packet(t['task_id']);print('\nTASK',t['task_id'])
        for f in row['facts']:print(f['fact_id'],f['probe_request'],'EXPECTED',f['gold_value'])
        print('RESPONSE',p['raw'].split('</think>')[-1] if '</think>' in p['raw'] else p['raw'][-6000:])

def evidence(tid,codes,reason,ambiguity=(),second=False):
    a=technical(tid)
    label='UNSCOREABLE_TECHNICAL' if not a['validity']['TECHNICALLY_VALID'] else 'CORRECT' if set(codes)=={'C'} else 'INCORRECT'
    record(tid,label,reason,list(codes),ambiguity,second)

def first_task(phase,arm):
    assert (ROOT/'audit'/f'phase{phase}_{arm}_technical_seal.json').exists()
    pending=[]
    for t in tasks(phase):
        tid=t['task_id']
        if t['arm']!=arm or (ROOT/'audit/first_scores'/f'{tid}.json').exists():continue
        p,row=packet(tid);a=technical(tid);amb=[]
        if a['ambiguous']:amb.append('semantic_extraction')
        if p['cap_hit']:amb.append('cap_hit')
        if not a['validity']['TECHNICALLY_VALID']:
            record(tid,'UNSCOREABLE_TECHNICAL','Response-only validity is sealed; missing, never incorrect.',ambiguity=amb);continue
        value=a['outcome']
        if row['options']:
            assert value in [chr(65+i) for i in range(len(row['options']))],(tid,value)
            correct=value==row['answer'];reason='Committed option letter, original MathVision option equivalence.'
        else:
            correct=equivalent(value,row['answer']);reason='Inherited exact or bounded numeric1e-6 MathVision equivalence.'
            if not re.fullmatch(r'-?\d+(?:\.\d+)?',value) or not re.fullmatch(r'-?\d+(?:\.\d+)?',str(row['answer'])):amb.append('math_expression')
        if correct is None:pending.append(dict(task_id=tid,answer=value,gold=row['answer']));continue
        record(tid,'CORRECT' if correct else 'INCORRECT',reason,ambiguity=amb)
    print('Manual equivalence',pending)

def freeze_first(phase):
    paths=[ROOT/'audit/first_scores'/f"{t['task_id']}.json" for t in tasks(phase)];rows=[load(p) for p in paths]
    ambiguous={r['family_id'] for r in rows if r['ambiguity']}
    families={r['family_id'] for r in rows}
    ordered=sorted(families-ambiguous,key=lambda f:hashlib.sha256(('stage12ys-score-audit-v1|'+f).encode()).hexdigest())
    random=ordered[:math.ceil(.2*len(ordered))]
    selected=[r['task_id'] for r in rows if r['ambiguity'] or r['family_id'] in random]
    save(ROOT/'audit'/f'phase{phase}_first_scoring_seal.json',dict(at=now(),files={str(p):sha(p) for p in paths},
        ambiguous_tasks=[r['task_id'] for r in rows if r['ambiguity']],random_families=random,second_tasks=selected,paired_outcomes_opened=False))
    print('QC required',len(selected),'calls;',len(random),'random families')

def close(phase):
    seal=load(ROOT/'audit'/f'phase{phase}_first_scoring_seal.json');reviews=[]
    for p,h in seal['files'].items():assert sha(p)==h
    for tid in seal['second_tasks']:
        a=load(ROOT/'audit/first_scores'/f'{tid}.json');b=load(ROOT/'audit/second_scores'/f'{tid}.json')
        same=a['label']==b['label'] and a['atoms']==b['atoms']
        if not same:
            c=load(ROOT/'audit/score_adjudications'/f'{tid}.json');assert c['resolved']
        reviews.append(dict(task_id=tid,agreement=same,second_sha256=sha(ROOT/'audit/second_scores'/f'{tid}.json')))
    save(ROOT/'audit'/f'phase{phase}_scoring_review.json',dict(at=now(),n_first=len(seal['files']),n_second=len(reviews),reviews=reviews,
        scope='Arm-separated same-agent second-pass review, not independent human reliability.',paired_outcomes_opened=False))

def final_score(tid):
    p=ROOT/'audit/score_adjudications'/f'{tid}.json'
    if p.exists():return load(p)
    return load(ROOT/'audit/first_scores'/f'{tid}.json')

def show_second(phase,arm,start=0,n=15):
    """Display one arm for QC without exposing its first score or paired labels."""
    seal=load(ROOT/'audit'/f'phase{phase}_first_scoring_seal.json')
    ids=[i for i in seal['second_tasks'] if packet(i)[0]['arm']==arm and not (ROOT/'audit/second_scores'/f'{i}.json').exists()]
    if arm.startswith('E_'):show_e(ids[start:start+n],n=n,phase=phase,arm=arm)
    else:
        for tid in ids[start:start+n]:
            p,r=packet(tid);a=technical(tid)
            print('\nTASK',tid,'GOLD',r['answer'],'COMMITMENT',a['outcome'],'VALID',a['validity']['TECHNICALLY_VALID'])
            print('EXTRACTION_REASON',a['reason']);print('RESPONSE_END',p['raw'][-650:])
    print('SECOND_PENDING',arm,len(ids))
