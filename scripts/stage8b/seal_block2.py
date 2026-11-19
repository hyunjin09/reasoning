"""Seal the exact semantic census before exposing any group feature comparisons."""
import copy
import itertools
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from visual_reasoning.stage8b.block1_data import digest, save

ROOT = Path('outputs/stage8b_block2/v1')


def main():
    prep = json.loads((ROOT/'audit/preparation_freeze.json').read_text())
    amendments_path = ROOT/'annotations/geometry_amendments_v1.json'
    amendments = json.loads(amendments_path.read_text())['amendments']
    hashes, records = {}, []
    for path in sorted((ROOT/'annotations/reviews').glob('*.json')):
        review = json.loads(path.read_text())
        packet_path = ROOT/'annotations/packets'/f'{review["item_id"]}.json'
        packet = json.loads(packet_path.read_text())
        assert digest(packet_path) == review['packet_sha256'] == prep['packet_sha256'][str(packet_path)]
        assert digest(packet['image']) == review['image_sha256'] == packet['image_sha256']
        assert review['protocol_sha256'] == prep['protocol_sha256'] == digest('plan/stage8b_block2_execution_protocol_v1.md')
        tokens = [json.loads(s) for s in Path(packet['token_file']).read_text().splitlines()]
        assert digest(packet['token_file']) == packet['token_sha256']
        pieces = [t['decoded_token'] for t in tokens]
        text = ''.join(pieces)
        ends = np.cumsum([len(s) for s in pieces]); starts = np.r_[0, ends[:-1]]
        hashes[str(path)] = digest(path)
        for event, frozen_event in zip(review['events'], packet['events'], strict=True):
            for key, value in frozen_event.items():
                assert event[key] == value, (event['event_id'], key)
            event = copy.deepcopy(event)
            for amendment in amendments:
                if amendment['event_id'] != event['event_id']:
                    continue
                assert amendment['review_sha256'] == digest(path)
                source = next(s for s in event['sources'] if s['id'] == amendment['source_id'])
                assert source['roi'] == amendment['original_roi']
                source['roi'] = amendment['replacement_roi']
            if event['semantic'] == 'T':
                assert event['source_image_reviewed'] and event['local'] in ['L+', 'L-', 'L?']
                left, right = event['claim_char_start'], event['claim_char_end']
                assert text[left:right] == event['quoted_native_text'] == event.get('readout', event['quote'])
                chosen = np.flatnonzero((starts < right) & (ends > left))
                assert list([int(chosen[0]), int(chosen[-1]+1)]) == [event['claim_start_token'], event['claim_end_token']]
                assert event['predicting_generated_query'] == int(chosen[0])-1 >= 0
                assert len({s['role'] for s in event['sources']}) == len(event['sources'])
                for source in event['sources']:
                    x0, y0, x1, y1 = source['roi']; w, h = packet['image_size']
                    assert source['role'] in ['T', 'X', 'I'] and 0 <= x0 < x1 <= w and 0 <= y0 < y1 <= h
                for a, b in itertools.combinations(event['sources'], 2):
                    x, y = a['roi'], b['roi']
                    assert min(x[2], y[2]) <= max(x[0], y[0]) or min(x[3], y[3]) <= max(x[1], y[1]), event['event_id']
            else:
                assert event['semantic'] in ['M', 'U'] and event['local'] is None and not event['sources']
            records.append(event)
    records.sort(key=lambda e: e['review_order'])
    assert len(records) == 456 and len({e['event_id'] for e in records}) == 456
    assert [e['event_id'] for e in records] == [e['event_id'] for e in prep['events']]
    seal = dict(at=datetime.now(timezone.utc).isoformat(), annotation_complete=True,
                protocol_sha256=prep['protocol_sha256'], preparation_sha256=digest(ROOT/'audit/preparation_freeze.json'),
                review_sha256=hashes, geometry_amendments_sha256=digest(amendments_path),
                feature_comparisons_opened=False, records=records)
    seal_path = ROOT/'annotations/semantic_seal.json'
    if seal_path.exists():
        previous = json.loads(seal_path.read_text())
        for key in seal.keys() - {'at'}:
            assert previous[key] == seal[key], key
    else:
        save(seal_path, seal)
    # Final outcomes are joined only after semantic sealing, never used as local labels.
    frame = pd.DataFrame(records)
    frame['item_id'] = frame.item_id.astype(str)
    covariates = pd.read_csv('outputs/stage8b_block1/v1/stage8b_block1_trajectory_metrics.csv', dtype={'item_id': str})
    fields = ['item_id', 'reasoning_tokens', 'subject', 'subject_group', 'question_words', 'log_question_length', 'benchmark_label', 'completion']
    frame = frame.merge(covariates[fields], on='item_id', how='left', validate='many_to_one')
    assert frame.benchmark_label.notna().all()
    frame['sources_json'] = frame.sources.map(json.dumps)
    frame.drop(columns=['sources']).to_parquet(ROOT/'stage8b_block2_TMU_table.parquet', index=False)
    frame.loc[frame.semantic == 'T'].drop(columns=['sources']).to_parquet(ROOT/'stage8b_block2_local_read_table.parquet', index=False)
    local = frame.loc[frame.semantic == 'T']
    counts = dict(Counter(local.local))
    summary = dict(at=datetime.now(timezone.utc).isoformat(), cohort_examples=256, reviewed_events=456,
                   reviewed_families=frame.family_id.nunique(), families_without_selected_events=42,
                   TMU=dict(Counter(frame.semantic)), local=counts,
                   local_families=local.groupby('local').family_id.nunique().to_dict(),
                   source_localizable=local.loc[local.source_localizable].groupby('local').size().to_dict(),
                   source_localizable_families=local.loc[local.source_localizable].groupby('local').family_id.nunique().to_dict(),
                   local_by_final=pd.crosstab(local.local, local.benchmark_label).to_dict(orient='index'),
                   local_by_completion=pd.crosstab(local.local, local.completion).to_dict(orient='index'),
                   preferred_gate_pass=counts.get('L+', 0) >= 64 and counts.get('L-', 0) >= 24,
                   descriptive_only=counts.get('L-', 0) < 24,
                   annotation_seal_sha256=digest(ROOT/'annotations/semantic_seal.json'),
                   annotation_limitations=['Single main-agent annotator; masked packets do not constitute independent blinding.',
                       'Earliest certifiable immediate claim can be coarser than later quantitative errors; this is not an exhaustive visual-error census.',
                       'Retrieval-selected membership cannot identify population missed-demand coverage.',
                       'Adjacent events can share evidence; all inference clusters by image family.'])
    save(ROOT/'stage8b_block2_event_annotation_summary.json', summary)
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
