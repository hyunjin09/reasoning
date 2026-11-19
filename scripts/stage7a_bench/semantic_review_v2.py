"""Present full frozen responses and save explicit, evidence-linked judgments.

This utility does not infer semantic or causal labels from keywords/accuracy.
"""
import argparse
import json

from scripts.stage7a.common import ROOT, read_json, read_jsonl, sha, write_jsonl

OUT = ROOT / 'outputs/stage7a_bench_v2'


def packet(run, manifest, start, end):
    rows = read_jsonl(ROOT / manifest)
    for index in range(start, min(end, len(rows))):
        row = rows[index]
        path = OUT / 'native_screen/generations' / run / 'examples' / row['event_id']
        if not (path / 'result.json').exists():
            raise RuntimeError('Example is not complete: ' + row['event_id'])
        result = read_json(path / 'result.json')
        if result.get('unavailable'):
            print(json.dumps(dict(index=index, event_id=row['event_id'], unavailable=result['unavailable_reason'])))
            continue
        generation = read_json(path / 'generation.json')
        assert result['generation_sha256'] == sha(path / 'generation.json')
        print(json.dumps(dict(index=index, event_id=row['event_id'], question=row['prompt'],
            response=generation['raw_decoded_response'], truncated=result['truncated']), ensure_ascii=False))


def record_phantom(run, manifest, judgments):
    rows = read_jsonl(ROOT / manifest)
    dest = OUT / 'native_screen/manual_reviews' / (run + '__' + rows[0]['condition'] + '.jsonl')
    records = read_jsonl(dest) if dest.exists() else []
    seen = {r['event_id']: r for r in records}
    for judgment in judgments:
        index, label, caveat, guessed_answer, quote, note = judgment[:6]
        details = judgment[6] if len(judgment) == 7 else {}
        assert not set(details) - {'binding_claim_present', 'claims', 'output_confidence', 'caveat_scope'}
        row = rows[index]
        assert row['benchmark'] == 'phantom_0' and row['no_image']
        assert label in {'F3', 'F5', 'F6'}
        path = OUT / 'native_screen/generations' / run / 'examples' / row['event_id']
        result = read_json(path / 'result.json')
        generation = read_json(path / 'generation.json')
        assert result['generation_sha256'] == sha(path / 'generation.json')
        assert quote in generation['raw_decoded_response'] and quote
        record = dict(event_id=row['event_id'], base_id=row['base_id'], example_id=row['base_id'],
            family_id=row['family_id'], benchmark=row['benchmark'], condition=row['condition'],
            native_index=index, screen_label=label, final_correctness=None,
            final_correctness_reason='No image/factual answer exists for Phantom-0',
            local_visual_claim_present=label == 'F3', local_visual_claim_correctness=None,
            binding_claim_present=False, unsupported_evidence_claim=label == 'F3',
            correct_local_read_followed_by_later_error=False, abstention_or_caveat=bool(caveat),
            guessed_answer=bool(guessed_answer), truncation=result['truncated'],
            evidence_quote=quote, review_note=note, review_scope='Full raw generated response including reasoning and final answer',
            output_confidence='caveated/uncertain' if caveat else 'unexpressed',
            causal_state=None, causal_state_reason='No actual visual source; behavioral screening only',
            manifest_sha256=sha(ROOT / manifest), generation_sha256=result['generation_sha256'],
            structural_selection_precedes_model_outputs=True)
        record.update(details)
        if row['event_id'] in seen:
            assert seen[row['event_id']] == record, 'Existing semantic judgment differs; explicit amendment required'
        else:
            records.append(record)
    write_jsonl(dest, sorted(records, key=lambda r:r['native_index']))
    print('MANUAL_REVIEWED', rows[0]['condition'], len(records))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', required=True)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--start', type=int, required=True)
    parser.add_argument('--end', type=int, required=True)
    args = parser.parse_args()
    packet(args.run, args.manifest, args.start, args.end)
