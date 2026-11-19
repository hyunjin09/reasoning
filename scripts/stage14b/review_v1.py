"""Read-only arm-separated review packets; no automatic manual-review claims."""
import argparse
from scripts.stage14b.common import *
from scripts.stage14b.scoring import guard, metadata, final_extraction, final_score, audit_selection, extraction_review


def response_scope(raw, model):
    if model == 'T' and '</think>' not in raw:
        return ''
    return raw.rsplit('</think>', 1)[-1].replace('<|im_end|>', '').strip()


def response_packet(task, generation, row, extraction, chars):
    scope = response_scope(generation['raw_decoded_response'], task['model_key'])
    return dict(task_id=task['task_id'], model=task['model_key'], condition=task['condition'],
                prompt=task['prompt'], options=row['options'], extraction=extraction,
                finish=generation['finish_reason'], tokens=generation['tokens'],
                scope_characters=len(scope), scope_tail=scope[-chars:])


def inventory(mode, model, kind):
    guard(mode, model)
    tasks = [t for t in all_tasks(mode) if t['model_key'] == model]
    if kind == 'extract':
        return [t for t in tasks if final_extraction(t['task_id'])['status'].startswith('NEEDS_')]
    if kind == 'equivalence':
        return [t for t in tasks if final_score(t['task_id'])['status'] == 'NEEDS_EQUIVALENCE_REVIEW']
    selected = set(audit_selection(mode, model))
    return [t for t in tasks if t['task_id'] in selected and not (ROOT/'scoring/qc'/f"{t['task_id']}.json").exists()]


def packet(t, kind, chars):
    path = checked_result(t)
    g = load(path.parent/'generation.json')
    r = metadata(t)
    p = response_packet(t, g, r, final_extraction(t['task_id']), chars)
    p.update(generation_sha256=sha(path.parent/'generation.json'), review_kind=kind)
    if kind != 'extract':
        p.update(gold_answer=r['gold_answer'], score=final_score(t['task_id']))
    return p


def commit_review(packet_path, decisions, mode='main', model='I'):
    """Persist explicit per-row agent decisions after displayed-context review."""
    guard(mode, model)
    pp = rows(packet_path)
    assert len(pp) == len(decisions)
    for p, d in zip(pp, decisions):
        tid = p['task_id']
        assert p['model'] == model and tid == d['task_id']
        assert d['reason'].strip()
        if p['review_kind'] == 'extract':
            assert 'gold_answer' not in p and 'score' not in p
            assert fingerprint(final_extraction(tid)) == fingerprint(p['extraction'])
            extraction_review(tid, d['answer'], d['status'], d['reason'])
        else:
            before = final_score(tid)
            assert fingerprint(before) == fingerprint(p['score'])
            label = d['status']
            assert label in ('CORRECT','WRONG','UNSCORABLE','TECHNICAL_MISSING')
            correct = {'CORRECT':True,'WRONG':False,'UNSCORABLE':None,'TECHNICAL_MISSING':None}[label]
            if label != before['status']:
                save(ROOT/'scoring/score_reviews'/f'{tid}.json', dict(before, at=now(),
                    correct=correct, status=label, grader='same_agent_semantic_review',
                    reason=d['reason'], original_score_sha256=fingerprint(before),
                    review_packet_sha256=fingerprint(p)))
            save(ROOT/'scoring/qc'/f'{tid}.json', dict(at=now(), task_id=tid,
                resolved=True, final_score_sha256=fingerprint(final_score(tid)),
                review_packet_sha256=fingerprint(p), review_packet_file=str(packet_path),
                reason=d['reason'], scope='Same-agent arm-separated response-context review; not independent human QC'))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('kind', choices=['extract','equivalence','qc'])
    p.add_argument('--mode', default='main')
    p.add_argument('--model', default='I')
    p.add_argument('--offset', type=int, default=0)
    p.add_argument('--limit', type=int, default=10)
    p.add_argument('--chars', type=int, default=1800)
    p.add_argument('--save')
    a = p.parse_args()
    tasks = inventory(a.mode, a.model, a.kind)
    print('remaining', len(tasks))
    packets = [packet(t, a.kind, a.chars) for t in tasks[a.offset:a.offset+a.limit]]
    if a.save:
        path = ROOT/'scoring/review_packets'/a.save
        write_rows(path, packets)
        print('saved', path, 'sha256', sha(path))
    for i, row in enumerate(packets, a.offset):
        # Hash identifies precisely which source context was displayed for review.
        print(json.dumps(dict(index=i, packet_sha256=fingerprint(row), **row), ensure_ascii=False))


if __name__ == '__main__':
    main()
