"""Verify receipts and expose continuation-only outcomes without paired labels."""
import argparse
import re
from pathlib import Path
from scripts.stage12us.common import ROOT,load,save,sha,now
from scripts.stage12ts.worker import fingerprint
from visual_reasoning.stage8b.v2_scoring import extract_answer


def tasks(phase):return load(ROOT/'audit'/f'{phase}_execution.json')['tasks']


def checked(task):
    folder=ROOT/'generations'/task['task_id'];g=load(folder/'generation.json');inp=load(folder/'input.json');r=load(folder/'result.json')
    assert r['generation_sha256']==sha(folder/'generation.json') and r['input_sha256']==sha(folder/'input.json')
    assert r['task_sha256']==g['task_sha256']==fingerprint(task)
    prefix=Path(task['prefix_path']).read_text() if task['prefix_path'] else ''
    cfg=load(ROOT/'config.json');arm=cfg['arms'][task['target']]
    actual=g['actual_prompt_token_ids']
    checks=dict(task_unchanged=inp['task']==task,
        source_unchanged=not task['prefix_path'] or sha(task['prefix_path'])==task['prefix_sha256'],
        zero_image_tokens=not set([151652,151653,151655,151656]).intersection(actual) and g['visual_tokens']==0,
        question_preserved=inp['messages']==[{'role':'user','content':[{'type':'text','text':task['question']}]}],
        prefix_exact=inp['chat_prompt'][inp['prefix_char_start']:inp['prefix_char_end']]==prefix,
        assistant_prefill=inp['chat_prompt'][:inp['prefix_char_start']].endswith('<|im_start|>assistant\n'+('<think>\n' if task['target']=='T' else '')),
        continuation_boundary=actual==inp['prompt_token_ids'] and g['continuation_begins_at_token']==len(actual),
        no_image_payload=inp['image_present'] is False and 'multi_modal_data' not in inp,
        output_receipt=g['tokens']==len(g['generated_token_ids']),seed=g['seed']==task['seed'],
        recipe=g['sampling']==dict(arm['recipe'],max_tokens=arm['cap']),
        config=g['config_sha256']==sha(ROOT/'config.json'),
        cap_consistent=g['cap_hit']==(g['finish_reason']=='length') and (not g['cap_hit'] or g['tokens']==arm['cap']))
    assert all(checks.values()),(task['task_id'],checks)
    return g,checks


def packets(phase):
    if phase=='science': assert load(ROOT/'stage12us_technical_validation.json')['pass']
    for t in tasks(phase):
        dest=ROOT/'audit/review_packets'/f"{t['task_id']}.json"
        if dest.exists() or not (ROOT/'generations'/t['task_id']/'result.json').exists():continue
        g,checks=checked(t);raw=g['raw_decoded_response']
        options=re.findall(r'^([A-E])\. (.*)$',t['question'],re.M)
        extraction=extract_answer(raw,[v for k,v in options])
        save(dest,dict(at=now(),task=t,raw=raw,tokens=g['tokens'],cap_hit=g['cap_hit'],
            finish_reason=g['finish_reason'],checks=checks,extraction=extraction,
            options=[v for k,v in options],generated_reasoning_closed='</think>' in raw,
            review_scope='New continuation only, no source prefix answer credit; no gold or paired outcomes.'))


def show(phase,tail):
    packets(phase)
    for t in tasks(phase):
        p=ROOT/'audit/review_packets'/f"{t['task_id']}.json"
        if not p.exists() or (ROOT/'audit/technical_decisions'/p.name).exists():continue
        r=load(p);print('\nTASK',t['task_id'],'TOKENS',r['tokens'],'STOP',r['finish_reason'],'EXTRACT',r['extraction']['extracted'])
        print(r['raw'][-tail:])


def record(tid,scoreable,outcome,reason,ambiguous=False):
    p=ROOT/'audit/review_packets'/f'{tid}.json';r=load(p)
    assert bool(outcome)==scoreable
    save(ROOT/'audit/technical_decisions'/f'{tid}.json',dict(at=now(),task_id=tid,scoreable=scoreable,
        outcome=outcome,reason=reason,ambiguous=ambiguous,packet_sha256=sha(p),correctness_used=False))


def technical_gate():
    rows=[]
    for t in tasks('technical'):
        g,checks=checked(t);a=load(ROOT/'audit/technical_decisions'/f"{t['task_id']}.json")
        assert a['packet_sha256']==sha(ROOT/'audit/review_packets'/f"{t['task_id']}.json")
        rows.append(dict(task_id=t['task_id'],target=t['target'],checks=checks,scoreable=a['scoreable'],tokens=g['tokens'],cap_hit=g['cap_hit']))
    audit=load(ROOT/'audit/technical_prefix_audit.json')
    safe=all(not r['EXPLICIT_FINAL_PRESENT'] and not r['ANSWER_CANDIDATE_PRESENT'] for r in audit['rows'])
    passed=all(all(r['checks'].values()) and r['scoreable'] for r in rows) and safe
    save(ROOT/'stage12us_technical_validation.json',dict(at=now(),rows=rows,**{'pass':passed},
        source_answer_safe=safe,correctness_inspected=False,primary_generation_not_started=True,
        criterion='All12 frozen technical calls meet seven plan requirements; no correctness threshold.'))
    print('TECHNICAL_PASS',passed)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['technical','science','gate']);p.add_argument('--tail',type=int,default=1400)
    a=p.parse_args();technical_gate() if a.action=='gate' else show(a.action,a.tail)
