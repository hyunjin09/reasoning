"""Output-only technical packets and sealed manual format decisions."""
import argparse
from scripts.stage12a.common import ROOT,load,save,sha,now
from scripts.stage12a.protocol import parse_task,parse_evidence,technical_gate
from scripts.stage11cr.protocol import repetition_metrics

def packet(label):
    m=load(ROOT/'audit'/f'{label}.json');rows=[]
    for t in m['rows']:
        folder=ROOT/'generations'/t['task_id']
        if not (folder/'result.json').exists():continue
        g=load(folder/'generation.json');receipt=load(folder/'result.json')
        assert receipt['generation_sha256']==sha(folder/'generation.json')
        parsed=parse_evidence(g['raw_decoded_response'],t['n_facts']) if t['arm']=='E' else parse_task(g['raw_decoded_response'],t['arm'],t['answer_type'])
        text=g['raw_decoded_response']
        rows.append(dict(task_id=t['task_id'],item_id=t['item_id'],arm=t['arm'],answer_type=t['answer_type'],
            n_facts=t['n_facts'],tokens=g['tokens'],cap_hit=g['cap_hit'],normal_stop=g['normal_stop'],
            generation_sha256=sha(folder/'generation.json'),parsed=parsed,repetition=repetition_metrics(g['generated_token_ids']),
            full_text=text,head=text[:500],tail=text[-1800:],middle=text[len(text)//2:len(text)//2+800]))
    p=ROOT/'audit/review_packets'/f'{label}_{now().replace(":", "")}.json'
    save(p,dict(at=now(),correctness_opened=False,rows=rows,expected=len(m['rows'])))
    print(p)
    for r in rows:print(r['task_id'],r['tokens'],r['cap_hit'],r['parsed'],r['repetition'])

def seal(label,decision_path,previous=None):
    m=load(ROOT/'audit'/f'{label}.json');d=load(decision_path)
    tasks={t['task_id']:t for t in m['rows']};assert set(tasks)=={r['task_id'] for r in d['rows']}
    assert len(d['rows'])==len(tasks) and d['correctness_opened'] is False
    merged={}
    if previous:
        old=load(ROOT/'audit'/f'{previous}_review.json');assert old['correctness_opened'] is False
        merged={(r['arm'],r['item_id']):r for r in old['rows']}
    for r in d['rows']:
        t=tasks[r['task_id']];p=ROOT/'generations'/r['task_id']/'generation.json';g=load(p)
        assert r['generation_sha256']==sha(p)
        for k in ['format_valid','severe_reasoning','intermediate_reasoning','repetition_pathology','committed_final']:assert isinstance(r[k],bool)
        assert r['reason'] and r['quote'] in g['raw_decoded_response']
        r=dict(r,arm=t['arm'],item_id=t['item_id'],cap_hit=g['cap_hit'],tokens=g['tokens'])
        merged[t['arm'],t['item_id']]=r
    by_arm={a:[r for (arm,_),r in merged.items() if arm==a] for a in 'EDC'}
    expected=set(load(ROOT/'stage12a_frozen_e_star_manifest.json')['technical_selection']['ids'])
    assert all({r['item_id'] for r in rr}==expected for rr in by_arm.values())
    result=dict(at=now(),correctness_opened=False,rows=list(merged.values()),previous=previous,
        decision_path=str(decision_path),decision_sha256=sha(decision_path),**technical_gate(by_arm))
    save(ROOT/'audit'/f'{label}_review.json',result)
    if result['pass'] or previous:
        result['repair_rounds']=int(previous is not None)
        save(ROOT/'stage12a_technical_prompt_validation.json',result)
    print('TECHNICAL_GATE',result['pass_by_arm'],result['summaries'])

if __name__=='__main__':
    p=argparse.ArgumentParser();s=p.add_subparsers(dest='action',required=True)
    a=s.add_parser('packet');a.add_argument('label')
    a=s.add_parser('seal');a.add_argument('label');a.add_argument('decisions');a.add_argument('--previous')
    a=p.parse_args()
    if a.action=='packet':packet(a.label)
    else:seal(a.label,a.decisions,a.previous)
