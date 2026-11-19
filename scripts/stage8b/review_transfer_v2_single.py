"""Build score-blind packets, seal manual reviews, then evaluate the frozen gate."""
import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from visual_reasoning.stage8a.annotations import align_reviewed_event
from visual_reasoning.stage8b.transfer import evaluate_transfer, reasoning_length


ROOT = Path('outputs/stage8b/v2')
NATIVE = ROOT / 'native/transfer32_t1_node02_single_v1'
ANNOTATIONS = ROOT / 'annotations/transfer32_t1_v1'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')


def source(item):
    rows = [json.loads(x) for x in (ROOT/'cohort/transfer32_manifest_v1.jsonl').read_text().splitlines()]
    row = next(x for x in rows if x['item_id'] == item)
    folder = NATIVE/'examples'/item
    receipt = json.loads((folder/'result.json').read_text())
    hashes = receipt['provenance_sha256']
    for name in ('manifest_row.json', 'tokens.jsonl'):
        assert digest(folder/name) == hashes[str(folder/name)]
    assert json.loads((folder/'manifest_row.json').read_text()) == row
    assert digest(Path(row['image'])) == row['image_sha256']
    tokens = [json.loads(x) for x in (folder/'tokens.jsonl').read_text().splitlines()]
    assert [x['token_index'] for x in tokens] == list(range(len(tokens)))
    reasoning = reasoning_length([x['decoded_token'] for x in tokens])
    reviewed = tokens[:min(1536, reasoning)]
    return row, receipt, reviewed, reasoning


def packet(item):
    row, receipt, tokens, reasoning = source(item)
    value = dict(item_id=item, family_id=row['family_id'], image=row['image'],
                 question=row['question'], reviewed_prefix_tokens=len(tokens),
                 native_reasoning_tokens=reasoning, token_rows=tokens,
                 token_sha256=receipt['provenance_sha256'][str(NATIVE/'examples'/item/'tokens.jsonl')],
                 no_detector_scores_or_final_accuracy=True)
    dest = ANNOTATIONS/'packets'/item
    save(dest.with_suffix('.json'), value)
    with dest.with_suffix('.md').open('x') as stream:
        stream.write(f'# MathVision {item} — blind reasoning-prefix packet\n\n{row["question"]}\n\n')
        stream.write(f'Source: {row["image"]}\n\nCoverage: {len(tokens)}/{reasoning} reasoning tokens.\n\n')
        for start in range(0, len(tokens), 64):
            part = tokens[start:start+64]
            stream.write(f'[{start}:{start+len(part)}] '+''.join(x['decoded_token'] for x in part)+'\n\n')
    print(json.dumps(dict(packet=str(dest.with_suffix('.md')), reviewed_prefix_tokens=len(tokens))))


def seal(path):
    manual = json.loads(path.read_text())
    item = manual['item_id']
    row, receipt, tokens, reasoning = source(item)
    assert manual['source_image_reviewed'] is True
    assert manual['complete_prefix_reviewed'] is True
    assert manual['detector_and_outcome_blind'] is True
    assert manual['reviewed_prefix_tokens'] == len(tokens)
    events = []
    for entry in manual['events']:
        category = entry['category']
        assert category in ('T', 'M', 'nonvisual') and entry['rationale'].strip()
        if category == 'T':
            assert entry['source_identity'].strip()
            assert entry['local_truth'] in ('L+', 'L-', 'unresolved')
        aligned = align_reviewed_event(tokens, quote=entry['quote'], value=entry['readout'],
                                       occurrence=entry.get('occurrence'))
        events.append(dict(entry, item_id=item, query_index=aligned['prefix_length'], alignment=aligned))
    assert len({x['query_index'] for x in events}) == len(events)
    assert [x['query_index'] for x in events] == sorted(x['query_index'] for x in events)
    counts = Counter(x['category'] for x in events)
    assert counts['T'] <= 2 and counts['M'] <= 1 and counts['nonvisual'] <= 1
    dest = ANNOTATIONS/'sealed'/f'{item}.json'
    save(dest, dict(item_id=item, family_id=row['family_id'], at=datetime.now(timezone.utc).isoformat(),
                    reviewer='main agent; manual source and complete prefix review',
                    reviewed_prefix_tokens=len(tokens), native_reasoning_tokens=reasoning,
                    source_sha256=row['image_sha256'], native_provenance=receipt['provenance_sha256'],
                    manual_packet=str(path), manual_packet_sha256=digest(path), events=events,
                    annotation_protocol_sha256=digest(Path('plan/stage8b_v2_transfer_annotation_protocol.md')),
                    review_notes=manual['review_notes'], detector_and_outcome_blind=True))
    print(json.dumps(dict(sealed=str(dest), events=dict(counts))))


def evaluate():
    # No score file is opened until all manifest reviews have been sealed and validated.
    demands = json.loads((ROOT/'annotations/input_demands_v1.json').read_text())
    expected = [x['item_id'] for x in demands['rows']]
    assert len(expected) == 32 and len(set(expected)) == 32
    sealed = []
    seal_hashes = {}
    for item in expected:
        path = ANNOTATIONS/'sealed'/f'{item}.json'
        review = json.loads(path.read_text())
        row, receipt, tokens, reasoning = source(item)
        assert review['item_id'] == item and review['detector_and_outcome_blind']
        assert review['native_provenance'] == receipt['provenance_sha256']
        assert review['reviewed_prefix_tokens'] == len(tokens) and review['native_reasoning_tokens'] == reasoning
        assert review['source_sha256'] == row['image_sha256']
        assert review['annotation_protocol_sha256'] == digest(Path('plan/stage8b_v2_transfer_annotation_protocol.md'))
        sealed.append(review)
        seal_hashes[str(path)] = digest(path)
    import numpy as np
    scores = {}
    for review in sealed:
        path = NATIVE/'examples'/review['item_id']/'passive.npz'
        assert digest(path) == review['native_provenance'][str(path)]
        with np.load(path, allow_pickle=False) as arrays:
            scores[review['item_id']] = arrays['retrieval_score'][:review['native_reasoning_tokens']]
    freeze = json.loads((ROOT/'config/transfer32_t1_node02_single_v1.json').read_text())
    rule_path = Path(freeze['detector_freeze'])
    assert digest(rule_path) == freeze['detector_freeze_sha256']
    rule = json.loads(rule_path.read_text())
    events = [event for review in sealed for event in review['events']]
    result = evaluate_transfer(scores, {x['item_id']: x['image_required'] for x in demands['rows']},
                               events, threshold=rule['retrieval']['tau_R'])
    result.update(at=datetime.now(timezone.utc).isoformat(), sealed_review_sha256=seal_hashes,
                  total_reviewed_prefix_tokens=sum(x['reviewed_prefix_tokens'] for x in sealed),
                  total_native_reasoning_tokens=sum(x['native_reasoning_tokens'] for x in sealed),
                  scope='Random32 early-prefix semantic alignment plus whole-reasoning item coverage; no causal certificate',
                  input_demands_sha256=digest(ROOT/'annotations/input_demands_v1.json'))
    dest = ROOT/'analysis/transfer_gate_v1.json'
    save(dest, result)
    print(json.dumps(result, indent=2))


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='action', required=True)
    sub.add_parser('packet').add_argument('item')
    sub.add_parser('seal').add_argument('manual_packet', type=Path)
    sub.add_parser('evaluate')
    args = parser.parse_args()
    if args.action == 'packet':
        packet(args.item)
    elif args.action == 'seal':
        seal(args.manual_packet)
    else:
        evaluate()


if __name__ == '__main__':
    main()
