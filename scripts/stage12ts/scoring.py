"""Separate C/T correctness passes; paired outcomes never enter these packets."""
import json
import re
from scripts.stage12ts.common import ROOT,load,save,sha,now
from scripts.stage12bs.protocol import audit_selection
from visual_reasoning.stage8b.v2_scoring import equivalent


def packets(arm):
    assert arm=='T'
    return [json.loads(s) for s in (ROOT/f'audit/correctness_packets/{arm}.jsonl').read_text().splitlines()]


def annotation(tid):return load(ROOT/f'audit/technical_annotations/{tid}.json')


def record(tid,label,reason,ambiguity=(),second=False):
    packet=next(p for p in packets(tid[0]) if p['task_id']==tid)
    assert label in ['CORRECT','INCORRECT','UNSCOREABLE_TECHNICAL']
    assert (label=='UNSCOREABLE_TECHNICAL') == (not annotation(tid)['scoreable'])
    save(ROOT/'audit'/('second_scores' if second else 'first_scores')/f'{tid}.json',dict(
        at=now(),task_id=tid,family_id=packet['family_id'],item_id=packet['item_id'],label=label,
        correct=None if label=='UNSCOREABLE_TECHNICAL' else label=='CORRECT',reason=reason,
        ambiguity=list(ambiguity),packet_sha256=sha(ROOT/f'audit/correctness_packets/{tid[0]}.jsonl'),
        review='Own-arm second pass without paired outcomes/first labels' if second else 'Own-arm first pass'))


def first(arm):
    pending=[]
    for p in packets(arm):
        tid=p['task_id'];a=annotation(tid);tech=load(ROOT/f'audit/technical_packets/{tid}.json');amb=[]
        if a['labels']['R2']:amb.append('provisional_answer_reopened')
        if tech['cap_hit']:amb.append('capped_response')
        if a['labels']['R5']:amb.append('competing_terminal_expressions')
        if not a['scoreable']:
            record(tid,'UNSCOREABLE_TECHNICAL','Pre-correctness sealed missingness; never wrong.',amb);continue
        value=a['extracted_outcome']
        if p['answer_type']=='multiple_choice':
            if value.strip().upper() not in [chr(65+i) for i in range(len(p['options']))]:pending.append(tid);continue
            eq=value.strip().upper()==str(p['gold']).upper()
            reason='Committed option letter under frozen benchmark option equivalence.'
        else:
            eq=equivalent(value,p['gold']);reason='Frozen MathVision exact/bounded numeric equivalence of committed answer.'
            if not re.fullmatch(r'-?\d+(?:\.\d+)?',str(value)) or not re.fullmatch(r'-?\d+(?:\.\d+)?',str(p['gold'])):amb.append('mathematical_equivalence')
            if eq is None:pending.append(tid);continue
        record(tid,'CORRECT' if eq else 'INCORRECT',reason,amb)
    print('Manual equivalence required:',pending)


def freeze():
    full=load(ROOT/'stage12ts_thinking_manifest.json')
    paths=[ROOT/f"audit/first_scores/{t['task_id']}.json" for t in full['tasks']]
    rows=[load(p) for p in paths];assert len(rows)==61
    ambiguous={r['family_id'] for r in rows if r['ambiguity']}
    rules=load(ROOT/'audit/analysis_rules.json')['random_audit']
    random=audit_selection(rules['family_hash_order'],ambiguous)
    selected=[r['task_id'] for r in rows if r['ambiguity'] or r['family_id'] in random]
    save(ROOT/'audit/first_scoring_seal.json',dict(at=now(),first_hashes={str(p):sha(p) for p in paths},
        mandatory_tasks=[r['task_id'] for r in rows if r['ambiguity']],random_families=random,
        unambiguous_family_count=61-len(ambiguous),second_tasks=selected,seed=rules['seed'],paired_outcomes_opened=False))
    print('Second-pass calls:',len(selected),'random families:',len(random))


def show(arm,selected=None,tail=0):
    for p in packets(arm):
        if selected is not None and p['task_id'] not in selected:continue
        print(p['task_id'],'QUESTION',p['question'],'GOLD',p['gold'])
        print('RESPONSE_END',p['response'][-tail:]) if tail else print('COMMITTED',annotation(p['task_id'])['extracted_outcome'])


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('action',choices=['T','freeze']);a=p.parse_args()
    freeze() if a.action=='freeze' else first(a.action)
