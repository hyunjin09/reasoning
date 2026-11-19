"""Read-only QC packets and explicit manual-review receipts; no inferred labels."""
import argparse
import datetime as dt
import json
from pathlib import Path

from scripts.stage14d.prepare_technical_v1 import ROOT, save, sha


def records():
    indexes = sorted((ROOT / 'audit').glob('native_review_adjudication_index_v*.json'),
                     key=lambda p: int(p.stem.rsplit('_v', 1)[1]))
    overrides = json.loads(indexes[-1].read_text())['active_overrides']
    result = []
    for p in (ROOT / 'annotation/native_review_v1').glob('*.json'):
        entry = overrides.get(p.stem)
        if entry:
            p = Path(entry['path'])
            assert sha(p) == entry['sha256']
        r = json.loads(p.read_text())
        result.append((p, r))
    return sorted(result, key=lambda x: (len(x[1]['prefix_text']), x[1]['task_id']))


def packet(path, r):
    source = json.loads(Path(r['source_review']).read_text())
    assert sha(r['source_review']) == r['source_review_sha256']
    raw = json.loads(Path(r['original_receipts']['generation']).read_text())['raw_decoded_response']
    print('\nCASE', r['task_id'], 'RECORD', str(path))
    print('QUESTION', source['original_source']['native_question'])
    print('TARGET', source['request'], 'REFERENCE', source['evaluator_only_reference'])
    print('SOURCE', source['source_observation'], 'ROI', source['ROI_pixels'])
    print('IMAGE', source['original_source']['source_image'])
    print('STATE', r['evidence_state'], 'FALLBACK', r['fallback'], r['fallback_reason'])
    print('FULL PREFIX', repr(r['prefix_text']))
    for k, e in r['events'].items():
        if e is None:
            print(k, None)
            continue
        a, b = e['char_start'], e['char_end']
        assert raw[a:b] == e['quote']
        print(k, a, b, repr(e['quote']))
        print('CONTEXT', repr(raw[max(0, a-200):min(len(raw), b+300)]))
    print('LATER SPANS', json.dumps(r['observed_repeats_or_contradictions'], ensure_ascii=False))
    print('FIRST PASS NOTE', r['note'])


def receipt(task_id, note):
    path, r = next((p, r) for p, r in records() if r['task_id'] == task_id)
    save(ROOT / 'annotation/native_qc_v1' / f'{task_id}.json', {
        'at': dt.datetime.now(dt.timezone.utc).isoformat(),
        'task_id': task_id, 'reviewed_record': str(path), 'reviewed_record_sha256': sha(path),
        'source_review': r['source_review'], 'source_review_sha256': r['source_review_sha256'],
        'reviewer': 'main agent, second pass; not independent inter-rater reliability',
        'method': 'manual source-reference / exact-span / whole-prefix QC, with original trace context as needed',
        'evidence_state': r['evidence_state'],
        'target_label_qc': 'PASS', 'event_timing_qc': 'PASS', 'source_neutral_prefix_qc': 'PASS',
        'scientific_intervention_outcomes_seen': False, 'manual_adjudication_note': note,
    })


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--start', type=int, default=0)
    parser.add_argument('--end', type=int, default=1)
    parser.add_argument('--task-id')
    parser.add_argument('--pending-limit', type=int)
    args = parser.parse_args()
    shown = 0
    for index, (path, row) in enumerate(records()):
        if args.pending_limit is not None:
            done = ROOT / 'annotation/native_qc_v1' / f'{row["task_id"]}.json'
            if done.exists():
                assert json.loads(done.read_text())['reviewed_record_sha256'] == sha(path)
                continue
            if shown >= args.pending_limit:
                break
            shown += 1
            print('QC ORDER INDEX', index)
            packet(path, row)
            continue
        if (args.task_id and row['task_id'] == args.task_id) or (not args.task_id and args.start <= index < args.end):
            print('QC ORDER INDEX', index)
            packet(path, row)
