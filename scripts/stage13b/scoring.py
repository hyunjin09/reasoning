"""Arm-separated correctness and same-agent QC; no paired comparisons here."""
import re
from scripts.stage13b.execution import ROOT,load,save,sha,now
from scripts.stage13b.review import tasks,source,technical,technical_path
from visual_reasoning.stage8b.v2_scoring import equivalent

ORDER=['2B_I_EQ','2B_T_EQ','4B_I_EQ','4B_T_EQ','8B_I_EQ','8B_T_EQ',
       '2B_I_img','2B_T_img','4B_I_img','4B_T_img','8B_I_img','8B_T_img']


def guard(cell):
    assert cell in ORDER
    for prior in ORDER[:ORDER.index(cell)]:
        assert (ROOT/'audit/scoring_closed'/f'{prior}.json').exists(),f'Close {prior} before scoring {cell}'


def record(tid,label,reason,ambiguity=(),second=False):
    t=next(t for t in tasks() if t['task_id']==tid);assert t['phase']!='technical'
    cell=t['scale']+'_'+t['arm'];guard(cell);a=technical(tid)
    assert label in ['CORRECT','INCORRECT','UNSCOREABLE_TECHNICAL']
    assert (label=='UNSCOREABLE_TECHNICAL')==(not a['validity']['TECHNICALLY_VALID'])
    save(ROOT/'audit'/('second_scores' if second else 'first_scores')/f'{tid}.json',
        dict(at=now(),task_id=tid,cell=cell,item_id=t['item_id'],family_id=t['family_id'],label=label,
             correct=None if label=='UNSCOREABLE_TECHNICAL' else label=='CORRECT',reason=reason,
             ambiguity=list(ambiguity),technical_sha256=sha(technical_path(tid)),
             scope='Own-arm same-agent QC, not independent reliability' if second else 'Own-arm first pass; paired outcomes closed'))


def first(cell):
    guard(cell);pending=[];selected=tasks(cell=cell);assert len(selected)==144
    assert all(technical_path(t['task_id']).exists() for t in selected)
    for t in selected:
        tid=t['task_id']
        if (ROOT/'audit/first_scores'/f'{tid}.json').exists():continue
        a=technical(tid);p=load(ROOT/'audit/review_packets'/f'{tid}.json');r=source(t);amb=[]
        if a['ambiguous']:amb.append('semantic_extraction')
        if p['cap_hit']:amb.append('cap_hit')
        if not a['validity']['TECHNICALLY_VALID']:
            record(tid,'UNSCOREABLE_TECHNICAL','Pre-outcome truncation/input validity missing; never incorrect.',amb);continue
        value=a['outcome']
        if value=='__NO_ANSWER__':
            record(tid,'INCORRECT','Normal-stop no-answer/refusal is scientific failure.',amb);continue
        if r['options']:
            assert value in [chr(65+i) for i in range(len(r['options']))],(tid,value)
            correct=value==r['answer'];reason='Frozen MathVision committed-option equivalence.'
        else:
            correct=equivalent(value,r['answer']);reason='Frozen exact or bounded numeric1e-6 MathVision equivalence.'
            if not re.fullmatch(r'-?\d+(?:\.\d+)?',value) or not re.fullmatch(r'-?\d+(?:\.\d+)?',str(r['answer'])):amb.append('math_expression')
        if correct is None:pending.append(dict(task_id=tid,answer=value,gold=r['answer']));continue
        record(tid,'CORRECT' if correct else 'INCORRECT',reason,amb)
    print('MANUAL_EQUIVALENCE',pending)


def freeze(cell):
    guard(cell);selected=tasks(cell=cell);assert len(selected)==144
    paths=[ROOT/'audit/first_scores'/f"{t['task_id']}.json" for t in selected]
    rows=[load(p) for p in paths];random=load(ROOT/'audit/random_review_manifest.json')['tasks'][cell]
    chosen=[r['task_id'] for r in rows if r['ambiguity'] or r['task_id'] in random]
    save(ROOT/'audit/first_scoring_seals'/f'{cell}.json',dict(at=now(),cell=cell,files={str(p):sha(p) for p in paths},
        random_tasks=random,ambiguous_tasks=[r['task_id'] for r in rows if r['ambiguity']],second_tasks=chosen,paired_opened=False))
    print('SECOND_REQUIRED',cell,len(chosen))


def show_second(cell,n=16,start=0):
    guard(cell);ids=load(ROOT/'audit/first_scoring_seals'/f'{cell}.json')['second_tasks']
    pending=[tid for tid in ids if not (ROOT/'audit/second_scores'/f'{tid}.json').exists()]
    indexed={t['task_id']:t for t in tasks(cell=cell)}
    for tid in pending[start:start+n]:
        t=indexed[tid];r=source(t);p=load(ROOT/'audit/review_packets'/f'{tid}.json');a=technical(tid)
        print('\nTASK',tid,'GOLD',r['answer'],'COMMITMENT',a['outcome'],'VALID',a['validity']['TECHNICALLY_VALID'])
        print('RESPONSE_END',p['raw'][-750:])
    print('SECOND_PENDING',cell,len(pending))


def close(cell):
    guard(cell);seal=load(ROOT/'audit/first_scoring_seals'/f'{cell}.json');reviews=[]
    for p,h in seal['files'].items():assert sha(p)==h
    for tid in seal['second_tasks']:
        a=load(ROOT/'audit/first_scores'/f'{tid}.json');b=load(ROOT/'audit/second_scores'/f'{tid}.json')
        same=a['label']==b['label']
        if not same:assert load(ROOT/'audit/score_adjudications'/f'{tid}.json')['resolved']
        reviews.append(dict(task_id=tid,agreement=same,second_sha256=sha(ROOT/'audit/second_scores'/f'{tid}.json')))
    save(ROOT/'audit/scoring_closed'/f'{cell}.json',dict(at=now(),cell=cell,n=144,reviews=reviews,
        files=seal['files'],paired_outcomes_opened=False,scope='Same-agent QC, not independent-rater reliability'))
