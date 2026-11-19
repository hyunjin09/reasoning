"""Versioned, gold-blind repair for complete letter:matching-option replies."""
import argparse
import re
from scripts.stage14b.common import *
from scripts.stage14b.review_v1 import response_scope
from scripts.stage14b.scoring import guard, metadata, final_extraction


def labeled_choice(raw, options, model, finish):
    if finish != 'stop':
        return None
    body = response_scope(raw, model)
    m = re.fullmatch(r'([A-Z])\s*:\s*(.+)', body)
    if not m or not 0 <= ord(m[1])-65 < len(options):
        return None
    if m[2].strip() != str(options[ord(m[1])-65]).strip():
        return None
    return m[1]


def apply(mode, model):
    guard(mode, model)
    seal = load(ROOT/'audit/presentation_repair_v2_seal.json')
    for path, expected in seal['files'].items():
        assert sha(path) == expected
    repaired = []
    for t in all_tasks(mode):
        if t['model_key'] != model:
            continue
        tid = t['task_id']; old = final_extraction(tid)
        if not old['status'].startswith('NEEDS_'):
            continue
        receipt = checked_result(t)
        g = load(receipt.parent/'generation.json')
        answer = labeled_choice(g['raw_decoded_response'], metadata(t)['options'], model, g['finish_reason'])
        if answer is None:
            continue
        save(ROOT/'scoring/extraction_reviews'/f'{tid}.json', dict(old, at=now(),
            answer=answer, status='EXTRACTED', method='automatic_labeled_choice_presentation_v2',
            reason='Whole normal-stop answer is exactly letter:matching-source-option text; no gold consulted.',
            original_extraction_sha256=sha(ROOT/'scoring/extraction'/f'{tid}.json'),
            repair_seal_sha256=sha(ROOT/'audit/presentation_repair_v2_seal.json')))
        repaired.append(tid)
    save(ROOT/'audit'/f'{mode}_{model}_presentation_repair_v2.json',
         dict(at=now(),repaired_task_ids=repaired,correctness_used=False,manual_review_claimed=False))
    print('Formatting repair', model, len(repaired))


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('mode');p.add_argument('model');a=p.parse_args();apply(a.mode,a.model)
