"""Ordered Block2 comparisons; low-yield results remain descriptive throughout."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from visual_reasoning.stage8b.block1_data import digest, save
from visual_reasoning.stage8b.block2_data import ROOT, PREFIX, P1, P2, P3, SECONDARY, TRANSPORT, B0
from visual_reasoning.stage8b.block2_statistics import compare, adjustment_diagnostics, paired_comparisons


def output(name, value):
    value.update(written_at=datetime.now(timezone.utc).isoformat(), descriptive_only=True,
                 annotation_seal_sha256=digest(ROOT/'annotations/semantic_seal.json'))
    save(ROOT/(PREFIX+name+'.json'), value)


def activation(frame):
    output('activation_comparison', dict(primary=compare(frame, P1), secondary=compare(frame, SECONDARY),
           adjustment=adjustment_diagnostics(frame),
           claim_timing=dict(claim_before_onset=int((frame.claim_start_token < frame.start_token).sum()),
                             claim_minus_onset_median=float((frame.claim_start_token-frame.start_token).median()),
                             scope='Onset and episode summaries are concurrent selected-event descriptions; not validated pre-read predictors.'),
           final_outcome_secondary={label: compare(sub, P1) for label, sub in frame.groupby('benchmark_label')},
           interpretation_limit='17 L- events in16 families, below24; neither a robust activation deficit nor activation equivalence can be established.'))


def load_replay(manifest):
    rows, files = [], {}
    for rank in range(2):
        worker = ROOT/'replay'/f'worker{rank}'
        finished = json.loads((worker/'completed.json').read_text()); assert finished['completed']
        expected = {r['event_id'] for r in manifest['requests'] if r['rank'] == rank}
        assert expected == set(finished['events'])
        for eid in sorted(expected):
            path = worker/'events'/f'{eid}.json'; result = json.loads(path.read_text())
            assert result['capture_logits_exact'] and result['native_features_match']
            assert result['manifest_sha256'] == digest(ROOT/(PREFIX+'replay_manifest.json'))
            files[str(path)] = digest(path); rows.append(result)
    assert len(rows) == len(manifest['requests'])
    return rows, files


def comparisons(frame, manifest):
    assert (ROOT/(PREFIX+'activation_comparison.json')).exists()
    replay, hashes = load_replay(manifest)
    covariates = frame.drop(columns=['local', 'family_id', 'item_id'])
    route = pd.DataFrame([dict(event_id=r['event_id'], local=r['local'], family_id=r['family_id'], item_id=r['item_id'], **r['routing']) for r in replay])
    route = route.merge(covariates, on='event_id', validate='one_to_one')
    pairs = manifest['pairs']; matched_ids = {p[k] for p in pairs for k in ['failure', 'control']}
    matched = route.loc[route.event_id.isin(matched_ids)]
    balance_fields = ['normalized_start', 'R_onset', 'log_question_length', 'reasoning_tokens', 'duration']
    balance = {key: matched.groupby('local')[key].agg(['mean', 'median', 'min', 'max']).to_dict(orient='index') for key in balance_fields}
    route_extra = ['qk_T_I', 'share_T_I', 'qk_T_rest', 'share_T_rest', 'density_T_X', 'target_attention_density']
    output('source_routing_comparison', dict(primary_matched=compare(matched, P2),
           paired=paired_comparisons(route, pairs, P2), all_replayed_descriptive=compare(route, P2),
           secondary=compare(route, route_extra), adjustment=adjustment_diagnostics(route, routing=True),
           matching_balance=balance, matching_pairs=pairs, unmatched=manifest['unmatched'],
           completion_exact_pairs=sum(p['completion_exact'] for p in pairs),
           source_counts=route.groupby(['local', 'candidate_count']).size().to_dict(),
           scope='Target ranks/entropy refer to the small semantically identified candidate set, not exhaustive image segmentation.',
           replay_parity=dict(events=len(replay), logits_exact=all(r['capture_logits_exact'] for r in replay),
                              native_global_max_abs_delta=max(r['feature_max_abs_delta'] for r in replay)),
           replay_artifacts_sha256=hashes))
    output('source_ambiguity_comparison', dict(primary_matched=compare(matched, P3),
           paired=paired_comparisons(route, pairs, P3), all_replayed_descriptive=compare(route, P3),
           missing_confuser_events=route.loc[route.qk_T_X.isna(), 'event_id'].tolist(),
           candidate_count_caveat='Candidate multiplicity and ROI area vary; small sample cannot fully control these differences. No robust ambiguity claim.'))
    heads = ['target_over_X_head_fraction', 'head_qk_margin_variance', 'head_attention_margin_variance',
             'layer_top_source_agreement', 'cross_head_source_entropy']
    output('head_layer_agreement', dict(comparison=compare(route, heads),
           layers=manifest['layers'], heads=manifest['heads'], selection='All frozen64 late heads; no post-result head selection',
           per_event={r['event_id']: r['per_layer'] for r in replay}))
    # Only now open and compare the previously saved transport observations.
    assert (ROOT/(PREFIX+'source_ambiguity_comparison.json')).exists()
    transport = pd.DataFrame([dict(event_id=r['event_id'], **r['transport']) for r in replay]).merge(route.drop(columns=[c for c in TRANSPORT if c in route]), on='event_id')
    output('transport_descriptive', dict(matched=compare(transport.loc[transport.event_id.isin(matched_ids)], TRANSPORT),
           all_replayed=compare(transport, TRANSPORT),
           scope='Observed source alphaV contributions, FP32 diagnostic reductions of BF16 native tensors; neither causal effects nor grounding scores.',
           ordered_after=['activation', 'source_routing', 'source_ambiguity']))
    # A flat, auditable table supports figures without rerunning inference.
    flat = route.drop(columns=['candidate_visual_shares']).copy()
    flat.to_parquet(ROOT/'audit/replayed_routing.parquet', index=False)
    return replay


def demand(frame):
    all_events = pd.read_parquet(ROOT/(PREFIX+'TMU_table.parquet'))
    tokens = pd.read_parquet(B0/'stage8b_block0_token_retrieval_features.parquet', columns=['item_id', 'token_index', 'active_retrieval'])
    coverage = []
    for item, group in frame.groupby('item_id'):
        active = tokens.loc[(tokens.item_id == item) & tokens.active_retrieval, 'token_index'].to_numpy()
        for row in group.itertuples():
            covered = bool((np.abs(active-int(row.claim_start_token)) <= 32).any())
            coverage.append(dict(event_id=row.event_id, family_id=row.family_id, benchmark_label=row.benchmark_label,
                                 local=row.local, claim_window_covered=covered))
    cover = pd.DataFrame(coverage)
    output('demand_coverage', dict(population_coverage=None,
           unavailable_reason='All456 events were selected from retrieval episodes; there is no independent census of non-retrieved required moments.',
           selected_episode_onset_coverage=1.,
           claim_window=dict(radius_tokens=32, centered_on='first local readout token',
                             overall=float(cover.claim_window_covered.mean()),
                             by_final=cover.groupby('benchmark_label').claim_window_covered.agg(['sum', 'count', 'mean']).to_dict(orient='index'),
                             scope='Conditional coverage within retrieval-selected T events, not missed-demand population recall'),
           selected_M_fraction=float((all_events.semantic == 'M').mean()), selected_M_events=int((all_events.semantic == 'M').sum()),
           denominator_selected_events=len(all_events),
           selection_scope='M frequency does not estimate all-token unnecessary retrieval probability.', events=coverage))


def edit_distance(a, b):
    last = list(range(len(b)+1))
    for i, first in enumerate(a, 1):
        now = [i]
        for j, second in enumerate(b, 1):
            now.append(min(last[j]+1, now[j-1]+1, last[j-1]+(first != second)))
        last = now
    return last[-1]


def sequences(replay, manifest):
    requests = {r['event_id']: r for r in manifest['requests']}; groups = {}
    for event in replay:
        groups.setdefault(event['item_id'], []).append(event)
    records = []
    for item, events in groups.items():
        if len(events) < 2:
            continue
        events.sort(key=lambda e: e['query']); demanded, retrieved, inventories = [], [], []
        for event in events:
            request = requests[event['event_id']]
            sources = {s['role']: item+':'+','.join(map(str, s['roi'])) for s in request['sources'] if request['source_positions'].get(s['role'])}
            demanded.append(sources['T']); retrieved.append(sources.get(event['routing']['top_source']))
            inventories.append(set(sources.values()))
        comparable = all(s == inventories[0] for s in inventories)
        changes = [i for i in range(1, len(events)) if demanded[i] != demanded[i-1]]
        transition = float(np.mean([retrieved[i-1:i+1] == demanded[i-1:i+1] for i in changes])) if comparable and changes else None
        records.append(dict(item_id=item, events=[e['event_id'] for e in events], queries=[e['query'] for e in events],
                            demanded_sources=demanded, retrieved_sources=retrieved, shared_source_inventory=comparable,
                            sparse_exact_ROI_edit_distance=edit_distance(demanded, retrieved)/len(demanded),
                            observed_target_agreement=float(np.mean([a == b for a, b in zip(demanded, retrieved)])),
                            source_transition_accuracy=transition,
                            oscillation_count=sum(retrieved[i] == retrieved[i-2] != retrieved[i-1] for i in range(2, len(events))) if comparable else None,
                            stale_source_count=sum(retrieved[i] == demanded[i-1] != demanded[i] for i in changes) if comparable else None,
                            lag=None, limitation='Sparse selected events; changing ROI granularities prevent continuous or canonical source dynamics claims.'))
    output('source_sequence_alignment', dict(trajectories_with_multiple_replayed_events=len(records), trajectories=records,
           continuous_lag=None, continuous_lag_unavailable_reason='No measurements between sparse selected anchors.',
           interpretation='Exact ROI keys are operational labels, not a semantic equivalence judgment across differently sized regions. No causal misrouting claim.'))


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--phase', choices=['activation', 'remaining'], required=True)
    args = parser.parse_args(); frame = pd.read_parquet(ROOT/'audit/event_features.parquet')
    if args.phase == 'activation':
        activation(frame)
    else:
        manifest = json.loads((ROOT/(PREFIX+'replay_manifest.json')).read_text())
        replay = comparisons(frame, manifest); demand(frame); sequences(replay, manifest)
    print(json.dumps(dict(phase=args.phase, complete=True)))


if __name__ == '__main__':
    main()
