"""Freeze all localizable failures and deterministic controls after annotation sealing."""
import json
from datetime import datetime, timezone
from pathlib import Path

from visual_reasoning.stage8b.block1_data import digest, save
from visual_reasoning.stage8b.block2_data import ROOT, PREFIX, event_features, match_events, source_positions


def main():
    seal_path = ROOT/'annotations/semantic_seal.json'
    seal = json.loads(seal_path.read_text())
    assert seal['annotation_complete']
    for path, expected in seal['review_sha256'].items():
        assert digest(path) == expected
    frame, aligned = event_features()
    assert not (ROOT/'audit/event_features.parquet').exists()
    frame.to_parquet(ROOT/'audit/event_features.parquet', index=False)
    aligned.to_parquet(ROOT/'audit/onset_aligned.parquet', index=False)
    pairs, unmatched = match_events(frame)
    ids = set(frame.loc[frame.source_localizable & (frame.local == 'L-'), 'event_id'])
    ids.update(p['control'] for p in pairs)
    prep = json.loads((ROOT/'audit/preparation_freeze.json').read_text())
    manifest = {r['item_id']: r for r in map(json.loads, Path('outputs/stage8b1a/cohort/census256_manifest_v1.jsonl').read_text().splitlines())}
    records = {e['event_id']: e for e in seal['records']}
    requests, skipped = [], []
    for _, event in frame.loc[frame.event_id.isin(ids)].sort_values('review_order').iterrows():
        native = Path(prep['native_paths'][event.item_id])
        annotation = records[event.event_id]
        metadata = json.loads((native/'input.json').read_text())
        positions, geometry = source_positions(annotation['sources'], metadata)
        if not positions['T']:
            skipped.append(dict(event_id=event.event_id, reason='Target has no unique grid cells after shared-cell exclusion', geometry=geometry))
            continue
        receipt = json.loads((native/'result.json').read_text())
        for path, expected in receipt['provenance_sha256'].items():
            assert digest(path) == expected
        requests.append(dict(event_id=event.event_id, item_id=event.item_id, family_id=event.family_id,
                             local=event.local, native_dir=str(native), row=manifest[event.item_id],
                             native_sha256=receipt['provenance_sha256'], source_positions=positions, geometry=geometry,
                             source_identity=annotation['source_identity'], sources=annotation['sources'],
                             query=int(event.predicting_generated_query), claim_start=int(event.claim_start_token),
                             pair_ids=[p['pair_id'] for p in pairs if event.event_id in [p['failure'], p['control']]]))
    # Whole items stay on one GPU, greedily balancing maximum required prefix length.
    costs = {}
    for request in requests:
        costs[request['item_id']] = max(costs.get(request['item_id'], 0), request['query']+1)
    ranks, loads = {}, [0, 0]
    for item in sorted(costs, key=lambda key: (-costs[key], key)):
        rank = min(range(2), key=lambda r: (loads[r], r)); ranks[item] = rank; loads[rank] += costs[item]
    for request in requests:
        request['rank'] = ranks[request['item_id']]
    source_paths = ['scripts/stage8b/run_block2_replay.py', 'scripts/stage8b/run_block2_replay.sh',
                    'scripts/stage8b/prepare_block2_replay.py', 'code/visual_reasoning/stage8b/block2_capture.py',
                    'code/visual_reasoning/stage8b/block2_data.py', 'code/visual_reasoning/stage8b/v2_protocol.py',
                    'code/visual_reasoning/stage8b/passive.py', 'code/visual_reasoning/stage0/modeling.py',
                    'code/visual_reasoning/stage3c9/streaming.py', 'code/visual_reasoning/stage3b0/cache.py',
                    'code/visual_reasoning/stage3b0/runtime.py']
    config = json.loads(Path('outputs/stage8b1a/config/resume125_node06_v1.json').read_text())
    output = dict(at=datetime.now(timezone.utc).isoformat(), stage='Block2 observational source replay',
                  annotation_seal_sha256=digest(seal_path), protocol_sha256=seal['protocol_sha256'],
                  model_checkpoint=config['model_checkpoint'], model_revision=config['model_revision'],
                  seed=1234, layers=[19, 20, 21, 22], heads=list(range(16)), dtype='bfloat16',
                  node='node06', gpus=2, prefix_chunk_size=1, interventions=False, generation=False,
                  pairs=pairs, unmatched=unmatched, geometry_unavailable=skipped,
                  mapping_policy='Existing pixel-to-grid mapping; remove shared cells from every source. Empty confusers stay missing; empty target is unreplayable.',
                  requests=requests, estimated_generated_queries_by_rank=loads,
                  source_sha256={p: digest(p) for p in source_paths},
                  global_feature_parity=dict(atol=1e-5, rtol=1e-5, mismatch_action='stop, preserve diagnostic; no downstream scientific analysis'))
    save(ROOT/(PREFIX+'replay_manifest.json'), output)
    print(json.dumps(dict(events=len(requests), pairs=len(pairs), unmatched=unmatched, geometry_unavailable=skipped,
                         prefixes=costs, estimated_generated_queries_by_rank=loads), indent=2))


if __name__ == '__main__':
    main()
