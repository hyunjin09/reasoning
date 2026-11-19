"""Produce a conservative census snapshot after the blind transfer review is sealed."""
import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from visual_reasoning.stage8b.scoring import score_answer


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--native-root', type=Path, action='append', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path('outputs/stage8b')
    freeze = json.loads((root/'audit/answer_scoring_freeze_v1.json').read_text())
    # Use the exact scorer frozen before native outcomes, not a yield-tuned repair.
    scorer = Path('code/visual_reasoning/stage8b/scoring.py')
    assert digest(scorer) == freeze['source_sha256'][str(scorer)]
    audit_rows = [json.loads(x) for x in (root/'cohort/transfer32_manifest_v1.jsonl').read_text().splitlines()]
    for row in audit_rows:
        review = root/'annotations/transfer32_v1/sealed'/f'{row["item_id"]}.json'
        assert review.exists(), f'Finish blind semantic review first: {row["item_id"]}'
    results, seen = [], set()
    for native in args.native_root:
        for receipt_path in sorted((native/'examples').glob('*/result.json')):
            receipt = json.loads(receipt_path.read_text())
            key = (receipt['item_id'], receipt['seed'])
            assert receipt['seed'] == 1234 and key not in seen, 'Duplicate/non-census rollout'
            seen.add(key)
            folder = receipt_path.parent
            for name in ('generation.json', 'manifest_row.json'):
                assert digest(folder/name) == receipt['provenance_sha256'][str(folder/name)]
            generated = json.loads((folder/'generation.json').read_text())
            row = json.loads((folder/'manifest_row.json').read_text())
            answer = score_answer(generated['raw_decoded_response'], row, normal_eos=receipt['normal_eos'])
            results.append(dict(item_id=receipt['item_id'], family_id=receipt['family_id'],
                                answer=answer, normal_eos=receipt['normal_eos'], tokens=receipt['tokens'],
                                source_receipt=str(receipt_path), source_receipt_sha256=digest(receipt_path),
                                runtime=receipt['runtime'], subject=row['subject'], level=row['level']))
    counts = Counter('correct' if x['answer']['correct'] is True else
                     'wrong' if x['answer']['correct'] is False else 'unresolved' for x in results)
    usable = Counter('correct' if x['answer']['correct'] is True else 'wrong'
                     for x in results if x['normal_eos'] and x['answer']['correct'] is not None)
    total, resolved = len(results), counts['correct'] + counts['wrong']
    result = dict(at=datetime.now(timezone.utc).isoformat(), native_examples=total, counts=dict(counts),
                  accuracy_on_resolved=counts['correct']/resolved if resolved else None,
                  unresolved_accuracy_interval=[counts['correct']/total, (counts['correct']+counts['unresolved'])/total] if total else None,
                  usable_normal_eos_outcomes=dict(usable), gate0=usable['correct'] >= 250 and usable['wrong'] >= 250,
                  manual_answer_adjudication_pending=counts['unresolved'], scorer_sha256=digest(scorer), rows=results,
                  interpretation='Unresolved extractions are not labeled wrong; capped traces retain explicit censoring. Gate0 here conservatively counts only normal-EOS resolved outcomes.')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}, indent=2))


if __name__ == '__main__':
    main()
