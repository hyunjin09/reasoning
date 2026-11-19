"""Arm-separated review packets and explicit, immutable human/agent decisions.

This module never adjudicates an answer itself. Extraction packets omit gold;
QC packets include gold only after the arm's response extraction is resolved.
"""
import argparse
from scripts.stage14c.common import *
from scripts.stage14c import scoring_v3 as scoring


def response_view(raw, model, limit=12000):
    closed = model != 'T' or '</think>' in raw
    body = raw.rsplit('</think>', 1)[-1] if closed else ''
    body = body.replace('<|im_end|>', '').strip()
    if len(body) <= limit:
        return dict(native_think_closed=closed, final_body=body, excerpted=False)
    return dict(native_think_closed=closed, final_body_head=body[:limit//3],
                final_body_tail=body[-2*limit//3:], excerpted=True,
                omitted_characters=len(body)-limit,
                caution='Inspect full generation if excerpts cannot establish final commitment.')


def packet(model, phase, start, count):
    scoring.guard(model)
    tasks={t['task_id']:t for t in all_tasks('main') if t['model_key']==model}
    if phase=='extraction':
        selected=[tid for tid in tasks if scoring.final_extraction(tid)['extraction'].get('needs_review')]
    else:
        selected=[tid for tid in scoring.audit_selection(model)
                  if not (ROOT/'scoring/qc'/f'{tid}.json').exists()]
    selected=sorted(selected); out=[]
    for tid in selected[start:start+count]:
        t=tasks[tid]; c=scoring.checked(t); source=scoring.source()[t['family_id']]
        row=dict(task_id=tid, benchmark=t['benchmark'], condition=t['condition'],
                 answer_kind=t['answer_kind'], question=source['question'],
                 extraction=scoring.final_extraction(tid),
                 raw_generation_path=str(c[0].parent/'generation.json') if c else None)
        if c:
            row.update(response_view(c[2]['raw_decoded_response'],model))
            row.update(cap_hit=c[2]['cap_hit'],tokens=c[2]['tokens'],finish_reason=c[2]['finish_reason'])
        if phase=='qc':
            row.update(gold=source['gold'],score=scoring.final_score(tid),
                       source_flags=scoring.eligibility()[t['family_id']]['source_validity_flags'])
        out.append(row)
    return dict(at=now(),model=model,phase=phase,remaining=len(selected),start=start,
                correctness_visible=phase=='qc',rows=out)


def apply_extractions(path):
    decisions=load(path); model=decisions['model']; scoring.guard(model)
    valid={t['task_id'] for t in all_tasks('main') if t['model_key']==model}
    assert decisions['correctness_used'] is False
    assert len({d['task_id'] for d in decisions['rows']})==len(decisions['rows'])
    for d in decisions['rows']:
        assert d['task_id'] in valid and d['response_only_reviewed'] is True
        assert not (ROOT/'scoring/extraction_reviews'/f"{d['task_id']}.json").exists()
        assert d['extraction_sha256']==fingerprint(load(ROOT/'scoring/extraction'/f"{d['task_id']}.json"))
    for d in decisions['rows']:
        scoring.extraction_review(d['task_id'],d['answer'],d['status'],d['reason'])


def apply_qc(path):
    decisions=load(path); model=decisions['model']; scoring.guard(model)
    valid=set(scoring.audit_selection(model))
    assert len({d['task_id'] for d in decisions['rows']})==len(decisions['rows'])
    for d in decisions['rows']:
        assert d['task_id'] in valid and d['response_and_gold_reviewed'] is True and d['reason'].strip()
        assert d['score_sha256']==fingerprint(scoring.final_score(d['task_id']))
        assert d['status'] in ['CORRECT','WRONG','UNSCORABLE','TECHNICAL_MISSING']
        assert not (ROOT/'scoring/qc'/f"{d['task_id']}.json").exists()
    for d in decisions['rows']:
        tid=d['task_id']; old=scoring.final_score(tid)
        if d['status']!=old['status']:
            save(ROOT/'scoring/score_reviews'/f'{tid}.json',dict(old,at=now(),status=d['status'],
                 reason=d['reason'],original_score_sha256=fingerprint(old),reviewer='main_agent',
                 review_batch_sha256=sha(path)))
        save(ROOT/'scoring/qc'/f'{tid}.json',dict(at=now(),resolved=True,
             score_sha256=fingerprint(scoring.final_score(tid)),reason=d['reason'],
             reviewer='main_agent',independent_interrater_review=False,review_batch_sha256=sha(path)))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['packet','extractions','qc'])
    p.add_argument('--model',choices=['I','T']);p.add_argument('--phase',choices=['extraction','qc'])
    p.add_argument('--start',type=int,default=0);p.add_argument('--count',type=int,default=20);p.add_argument('--path')
    a=p.parse_args()
    if a.action=='packet':
        value=packet(a.model,a.phase,a.start,a.count)
        if a.path:save(a.path,value)
        else:print(json.dumps(value,ensure_ascii=False,indent=2))
    elif a.action=='extractions':apply_extractions(a.path)
    else:apply_qc(a.path)
