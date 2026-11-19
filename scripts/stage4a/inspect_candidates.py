"""Prepare a compact visual/text review packet; never accepts a candidate."""
import argparse
from bisect import bisect_right
from PIL import Image, ImageDraw
from scripts.stage4a.prepare_config import ROOT, OUT, read_json, read_jsonl, write_json
from visual_reasoning.stage4a.cohort import equivalent_numeric_matches, choose_event_triplet


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('packet', help='JSON mapping base ID to two physically reviewed values')
    parser.add_argument('--mentions', type=int, default=6)
    args = parser.parse_args()
    pairs = read_json(args.packet)
    screen = read_jsonl(OUT / 'cohort/prospective_screen_manifest.jsonl')
    outcomes = read_jsonl(OUT / 'cohort/reused_native_outcomes.jsonl')
    outcomes += [read_json(p) for p in (OUT / 'prospective_generation/raw').glob('shard_*/examples/*/result.json')]
    outcomes = {r['example_id']: r for r in outcomes}
    sheet = Image.new('RGB', (1500, 430 * ((len(pairs) + 2) // 3)), 'white')
    draw = ImageDraw.Draw(sheet)
    records = []
    for i, (base, values) in enumerate(pairs.items()):
        item = next(r for r in screen if r['base_problem_id'] == base)
        native = Image.open(item['source_image']).convert('RGB')
        print('\nBASE', base, 'size', native.size, 'question', item['question'])
        annotated = native.copy()
        grid = ImageDraw.Draw(annotated)
        for x in range(0, native.width, 50):
            grid.line((x, 0, x, native.height), fill=(220, 220, 220))
            grid.text((x, 0), str(x), fill='red')
        for y in range(50, native.height, 50):
            grid.line((0, y, native.width, y), fill=(220, 220, 220))
            grid.text((0, y), str(y), fill='red')
        annotated.thumbnail((480, 390))
        x, y = i % 3 * 500, i // 3 * 430
        sheet.paste(annotated, (x, y + 30))
        draw.text((x, y + 5), f'{base} original {native.size}', fill='black')
        outcome = outcomes.get(item['example_id'])
        if not outcome or not outcome['complete'] or outcome['truncated']:
            print('NO NATURAL COMPLETE', outcome and outcome['status'])
            continue
        tokens = read_jsonl(ROOT / outcome['artifact_dir'] / 'tokens.jsonl')
        starts, cursor = [], 0
        for token in tokens:
            starts.append(cursor)
            cursor += len(token['decoded_token'])
        text = ''.join(t['decoded_token'] for t in tokens).split('</think>')[0]
        mentions = {}
        for value in values:
            mentions[value] = []
            for match in equivalent_numeric_matches(text, value):
                pos = bisect_right(starts, match.start()) - 1
                mentions[value].append({'position': pos, 'context': text[max(0, match.start()-100):match.end()+150].replace('\n', ' ')})
        triplet = choose_event_triplet([m['position'] for m in mentions[values[0]]], [m['position'] for m in mentions[values[1]]])
        print('numeric proposal only', triplet)
        for value, found in mentions.items():
            for mention in found[:args.mentions]:
                print(value, mention['position'], mention['context'])
        records.append({'base_problem_id': base, 'example_id': item['example_id'], 'mentions': mentions, 'numeric_proposal_only': triplet})
    name = __import__('pathlib').Path(args.packet).stem
    sheet.save(OUT / 'cohort/review' / (name + '.png'))
    write_json(OUT / 'cohort/review' / (name + '.json'), records)


if __name__ == '__main__':
    main()
