"""Score sealed dev extractions using the unchanged inherited equivalence rule."""
import copy
import json
from datetime import datetime, timezone
from pathlib import Path

from scripts.stage8c.prepare import save, sha
from visual_reasoning.stage8b.v2_scoring import equivalent
from visual_reasoning.stage8c.analysis_fp32 import summarize, transitions
from visual_reasoning.stage8c.analysis_fp32_reviewed import development_decision

ROOT = Path('outputs/stage8c_v3/v1')


def grade_extracted(answer, row):
    # Exact comparison policy from scripts/stage8b/score_block0.py.
    if answer is None:
        return None
    if row['options']:
        letters = [chr(65+i) for i in range(len(row['options']))]
        letter = answer.strip().strip('().').upper()
        if letter in letters:
            return letter == row['answer']
        matches = [letters[i] for i, value in enumerate(row['options']) if equivalent(answer, value) is True]
        return matches[0] == row['answer'] if len(matches) == 1 else None
    return equivalent(answer, row['answer'])


def main():
    review_root = ROOT/'annotations/dev_extraction_v1'
    seal_path = review_root/'manual_extraction_seal.json'
    seal = json.loads(seal_path.read_text())
    assert seal['labels_sealed'] and seal['extraction_review_closed']
    assert seal['packet_sha256'] == sha(review_root/'packets.json')
    # Gold and task/dose mapping are opened only after the extraction seal.
    metadata = {r['item_id']: r for r in json.loads((ROOT/'stage8c_v3_dev128_manifest.json').read_text())['rows']}
    mapping = {r['blind_id']: r for r in json.loads((review_root/'mapping.json').read_text())['rows']}
    packets = {r['blind_id']: r for r in json.loads((review_root/'packets.json').read_text())['packets']}
    auto_path = ROOT/'stage8c_v3_dev_dose_results.json'
    auto = json.loads(auto_path.read_text())
    arms = {float(g): copy.deepcopy(a) for g, a in auto['rows'].items()}
    tasks = {r['task_id']: r for a in arms.values() for r in a.values()}
    pending = {r['task_id'] for r in auto['blind_extraction_pending']}
    assert len(seal['rows']) == len(mapping) == len(pending) == 78
    assert {mapping[r['blind_id']]['task_id'] for r in seal['rows']} == pending
    for r in tasks.values():
        assert grade_extracted(r['extracted'], metadata[r['item_id']]) == r['correct']
    provenance = []
    for manual in seal['rows']:
        m = mapping[manual['blind_id']]; p = packets[manual['blind_id']]
        assert sha(m['generation']) == m['generation_sha256']
        text = json.loads(Path(m['generation']).read_text())['raw_decoded_response']
        import hashlib
        assert hashlib.sha256(text.encode()).hexdigest() == manual['raw_text_sha256']
        body = p['body']; assert hashlib.sha256(body.encode()).hexdigest() == manual['body_sha256']
        offset = text.rfind(body); assert offset >= 0
        span = None
        if manual['body_span'] is not None:
            a, b = manual['body_span']; span = [offset+a, offset+b]
            assert text[slice(*span)] == manual['literal']
        r = tasks[m['task_id']]; before = {k: r[k] for k in ('correct','extracted','span','method','status')}
        correct = grade_extracted(manual['extracted'], metadata[r['item_id']])
        r.update(correct=correct, extracted=manual['extracted'], span=span,
                 method='blind_manual_extraction' if manual['extracted'] is not None else 'blind_review_unresolved',
                 status='extracted' if manual['extracted'] is not None else 'unresolved',
                 benchmark_label='unresolved' if correct is None else 'correct' if correct else 'wrong',
                 extraction_review_closed=True, extraction_provenance=str(seal_path),
                 unresolved_reason=(manual['rationale'] if manual['extracted'] is None else
                    'Unsupported or non-unique equivalence under the unchanged local adapter') if correct is None else None)
        provenance.append(dict(task_id=r['task_id'], blind_id=manual['blind_id'], automatic=before,
                               manual=manual, correct=correct, raw_span=span))
    summaries = {}
    for g, a in arms.items():
        summaries[str(g)] = dict(auto['summaries'][str(g)], **summarize(a))
        summaries[str(g)]['transitions'] = None if g == 1. else transitions(arms[1.], a)
    decision = development_decision(arms, metadata, extraction_review_closed=True)
    at = datetime.now(timezone.utc).isoformat()
    result = dict(at=at, stage='development', status='development_review_complete',
        complete_trajectories=512, extraction_review_closed=True, blind_extraction_pending=[],
        summaries=summaries, rows={str(g): a for g, a in arms.items()}, decision=decision,
        automatic_results_path=str(auto_path), automatic_results_sha256=sha(auto_path),
        manual_seal=str(seal_path), manual_seal_sha256=sha(seal_path),
        scorer_sha256=sha('code/visual_reasoning/stage8b/v2_scoring.py'),
        analysis_sha256=sha('code/visual_reasoning/stage8c/analysis_fp32_reviewed.py'),
        implementation_sha256=sha(__file__), unresolved_correct_credit=False,
        review_limitation=seal['limitation'], receipt_sha256=auto['receipt_sha256'])
    out = ROOT/'stage8c_v3_dev_dose_results_reviewed_v1.json'
    save(out, result)
    save(review_root/'scoring_provenance.json', dict(at=at, extraction_seal_sha256=sha(seal_path),
         unchanged_automatic_comparisons=512, unchanged_nonqueue_rows=434,
         source_comparison_helper_sha256=sha('scripts/stage8b/score_block0.py'), rows=provenance))
    save(ROOT/'stage8c_v3_dose_freeze.json', dict(decision, at=at,
         development_results=str(out), development_results_sha256=sha(out),
         manual_extraction_seal_sha256=sha(seal_path), heldout_launched=False))
    print(json.dumps(dict(decision=decision['status'], dose=decision['dose'], summaries=summaries), indent=2))


if __name__ == '__main__':
    main()
