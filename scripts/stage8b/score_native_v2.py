"""Benchmark correctness and completion are separate; review must be sealed first."""
import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from visual_reasoning.stage8b.v2_protocol import completion_status
from visual_reasoning.stage8b.v2_scoring import score_answer


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='outputs/stage8b/v2/config/transfer32_t1_v1.json')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path('outputs/stage8b/v2')
    cfg = json.loads(Path(args.config).read_text())
    for name in ('code/visual_reasoning/stage8b/v2_scoring.py', 'code/visual_reasoning/stage8b/scoring.py'):
        assert sha(name) == cfg['source_sha256'][name]
    audit = [json.loads(x) for x in Path(cfg['manifest']).read_text().splitlines()]
    for row in audit:
        review = root/'annotations/transfer32_t1_v1/sealed'/f'{row["item_id"]}.json'
        assert review.exists(), f'Seal score-blind semantic review before outcomes: {row["item_id"]}'
    rows = []
    for row in audit:
        folder = Path(cfg['output_dir'])/'examples'/row['item_id']
        receipt = json.loads((folder/'result.json').read_text())
        for name in ('generation.json', 'manifest_row.json'):
            assert sha(folder/name) == receipt['provenance_sha256'][str(folder/name)]
        assert json.loads((folder/'manifest_row.json').read_text()) == row
        generated = json.loads((folder/'generation.json').read_text())
        assert generated['generation_parameters']['temperature'] == 1.0
        text = generated['raw_decoded_response']
        state = completion_status(text, normal_eos=receipt['normal_eos'],
            at_length_cap=receipt['at_length_cap'], tokens=receipt['tokens'])
        rows.append(dict(item_id=row['item_id'], family_id=row['family_id'],
            answer=score_answer(text, row), **state, source_receipt=str(folder/'result.json'),
            source_receipt_sha256=sha(folder/'result.json')))
    counts = Counter(r['answer']['benchmark_label'] for r in rows)
    cross = Counter((r['answer']['benchmark_label'], r['completion']) for r in rows)
    scored = counts['correct'] + counts['wrong']
    report = dict(at=datetime.now(timezone.utc).isoformat(), examples=len(rows), counts=dict(counts),
        accuracy_on_scorable=counts['correct']/scored if scored else None,
        extraction_yield=sum(r['answer']['extracted'] is not None for r in rows)/len(rows),
        outcome_yield=scored/len(rows), gate2=counts['correct'] >= 250 and counts['wrong'] >= 250,
        completion_counts=dict(Counter(r['completion'] for r in rows)),
        outcome_completion=[dict(outcome=o, completion=c, count=n) for (o,c),n in sorted(cross.items())],
        manual_extraction_pending=[r['item_id'] for r in rows if r['answer']['extracted'] is None],
        unsupported_equivalence_pending=[r['item_id'] for r in rows if r['answer']['extracted'] is not None and r['answer']['correct'] is None],
        scorer_limitation=cfg['scorer'], rows=rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as stream: json.dump(report, stream, indent=2, ensure_ascii=False)
    print(json.dumps({k:v for k,v in report.items() if k != 'rows'}, indent=2))


if __name__ == '__main__':
    main()
