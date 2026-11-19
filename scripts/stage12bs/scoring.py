"""Arm-separated correctness decisions; immutable first and blind second passes."""
import json
import re
from scripts.stage12bs.common import ROOT, load, save, sha, now
from scripts.stage12bs.protocol import audit_selection
from visual_reasoning.stage8b.v2_scoring import equivalent


def packets(arm):
    return [json.loads(x) for x in (ROOT/'audit/correctness_packets'/f'{arm}.jsonl').read_text().splitlines()]


def annotation(tid):
    return load(ROOT/'audit/technical_annotations'/f'{tid}.json')


def record(tid,label,reason,ambiguity=(),atoms=None,second=False):
    dest=ROOT/'audit'/('second_scores' if second else 'first_scores')/f'{tid}.json'
    assert not dest.exists()
    packet=next(p for p in packets(tid[0]) if p['task_id']==tid)
    assert label in ['CORRECT','INCORRECT','UNRESOLVED_TECHNICAL']
    if tid[0]=='E':
        assert len(atoms)==len(packet['facts'])
        assert all(v in ['CORRECT','INCORRECT','UNRESOLVED'] for v in atoms)
    save(dest,dict(at=now(),task_id=tid,family_id=packet['family_id'],item_id=packet['item_id'],
        label=label,correct=None if label=='UNRESOLVED_TECHNICAL' else label=='CORRECT',
        reason=reason,ambiguity=list(ambiguity),atoms=atoms,
        packet_sha256=sha(ROOT/'audit/correctness_packets'/f'{tid[0]}.jsonl'),
        review='Separate own-arm pass; no paired-arm outcomes or first-pass labels displayed' if second else 'Own-arm first pass'))


def evidence(item_id,codes,reason,ambiguity=(),second=False):
    tid=f'E_{item_id}_v1'; atoms=[{'C':'CORRECT','I':'INCORRECT','U':'UNRESOLVED'}[s] for s in codes]
    a=annotation(tid)
    label='UNRESOLVED_TECHNICAL' if not a['scoreable'] else 'CORRECT' if all(v=='CORRECT' for v in atoms) else 'INCORRECT'
    record(tid,label,reason,ambiguity,atoms,second)


def show_e(start=0,end=61,selected=None):
    for p in packets('E')[start:end]:
        if selected is not None and p['task_id'] not in selected:continue
        print('\n',p['task_id'])
        for f in p['facts']:
            print(f['fact_id'],f['probe_request'],'GOLD:',f['gold_value'],'ACCEPT:',f['accepted_paraphrases'],'EXACT:',f['exact_lexical_required'])
        print('RESPONSE:',p['response'])


def task_first(arm):
    assert arm in 'NO'
    pending=[]
    for p in packets(arm):
        a=annotation(p['task_id']);technical=load(ROOT/'audit/technical_packets'/f"{p['task_id']}.json")
        ambiguity=[]
        if a['labels']['R2']:ambiguity.append('provisional_answer_reopened')
        if technical['cap_hit']:ambiguity.append('capped_response')
        if a['labels']['R5']:ambiguity.append('competing_terminal_expressions')
        answer=a['extracted_outcome']
        if not a['scoreable']:
            record(p['task_id'],'UNRESOLVED_TECHNICAL','Pre-correctness sealed unscoreability; not wrong.',ambiguity)
            continue
        if p['answer_type']=='multiple_choice':
            value=answer.strip().upper()
            if value not in [chr(65+i) for i in range(len(p['options']))]:
                ambiguity.append('malformed_or_value_option'); pending.append(p['task_id']);continue
            eq=value==str(p['gold']).upper()
            method='Explicit committed option letter from response-only semantic extraction.'
        else:
            eq=equivalent(answer,p['gold'])
            method='Frozen case-insensitive exact / bounded numeric1e-6 equivalence of committed expression.'
            if not re.fullmatch(r'-?\d+(?:\.\d+)?',str(answer)) or not re.fullmatch(r'-?\d+(?:\.\d+)?',str(p['gold'])):
                ambiguity.append('mathematical_equivalence')
            if eq is None:pending.append(p['task_id']);continue
        if p['task_id']=='N_2198_v1':ambiguity.append('terminal_option_letter_value_conflict')
        record(p['task_id'],'CORRECT' if eq else 'INCORRECT',method,ambiguity)
    print('MANUAL_EQUIVALENCE_REQUIRED',pending)


def freeze_first():
    full=load(ROOT/'stage12bs_full_manifest.json'); paths=[ROOT/'audit/first_scores'/f"{t['task_id']}.json" for t in full['tasks']]
    rows=[load(p) for p in paths];assert len(rows)==183
    ambiguous={r['family_id'] for r in rows if r['ambiguity']}
    rules=load(ROOT/'audit/analysis_rules.json')
    random=audit_selection(rules['random_audit']['family_hash_order'],ambiguous)
    selected=[r['task_id'] for r in rows if r['ambiguity'] or r['family_id'] in random]
    path=ROOT/'audit/first_scoring_seal.json';assert not path.exists()
    save(path,dict(at=now(),first_hashes={str(p):sha(p) for p in paths},
        mandatory_tasks=[r['task_id'] for r in rows if r['ambiguity']],
        random_families=random,unambiguous_family_count=61-len(ambiguous),second_tasks=selected,
        seed=rules['random_audit']['seed'],paired_outcomes_opened=False))
    print('Second review',len(selected),'random families',len(random))


def show_task(arm,selected=None,tail=0):
    for p in packets(arm):
        if selected is not None and p['task_id'] not in selected:continue
        print('\n',p['task_id'],'QUESTION',p['question'],'GOLD',p['gold'])
        # No first correctness label is loaded or displayed.
        if tail:print('RESPONSE_END',p['response'][-tail:])
        else:print('COMMITTED',annotation(p['task_id'])['extracted_outcome'])


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('action',choices=['N','O','freeze']);a=p.parse_args()
    freeze_first() if a.action=='freeze' else task_first(a.action)
