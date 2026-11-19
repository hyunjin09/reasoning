"""Deterministic reduction, assembly, and final integrity freeze for Block 0."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from prepare_block0 import ROOT, digest, save
from visual_reasoning.stage8b.block0 import TAU, EPSILON, Z_KEYS, PLACEHOLDERS, review_indices

PREFIX = 'stage8b_block0_'


def target(name):
    return ROOT/(PREFIX+name)


def moments():
    rows = []
    for rank in range(4):
        rows.extend(json.loads((ROOT/'workers'/f'rank{rank}'/'moments.json').read_text()))
    by_id = {r['item_id']:r for r in rows}
    cohort = json.loads(target('cohort_manifest.json').read_text())['rows']
    assert len(by_id) == 256
    count = np.zeros(4, dtype=np.int64); mean = np.zeros(4); m2 = np.zeros(4)
    for source in cohort:
        r = by_id[source['item_id']]
        n, mu, sq = np.array(r['count']), np.array(r['mean']), np.array(r['m2'])
        total = count+n; delta = mu-mean
        m2 += sq+delta**2*count*n/total
        mean += delta*n/total; count = total
    scale = np.sqrt(m2/count); scale[scale == 0] = 1
    save(ROOT/'audit'/'standardization_freeze.json', dict(at=datetime.now(timezone.utc).isoformat(),
        features=Z_KEYS, mean=mean.tolist(), scale=scale.tolist(), finite_counts=count.tolist(),
        variance_ddof=0, population='all finite reasoning-token values per dimension; all 256 trajectories',
        outcomes_used=False, missing='preserved, not imputed', moments_order='frozen cohort order'))


def tables():
    cohort = json.loads(target('cohort_manifest.json').read_text())['rows']
    all_events = {0:[], 4:[], 8:[]}
    metrics, phases, geometry, completions, membership, roi, checks = [], [], [], [], [], [], []
    writer = None
    try:
        for row in cohort:
            out = ROOT/'items'/row['item_id']
            meta = json.loads((out/'meta.json').read_text())
            derived = json.loads((out/'derived.json').read_text())
            table = pq.read_table(out/'features.parquet')
            if writer is None:
                writer = pq.ParquetWriter(target('token_retrieval_features.parquet'), table.schema, compression='zstd')
            writer.write_table(table)
            identity = {k:row[k] for k in ['item_id','family_id','order']}
            completions.append(dict(identity, **meta['completion'], delimiter_tokens=meta['delimiter_tokens']))
            metrics.append(dict(identity, **meta['metrics']))
            phases.extend(dict(identity, **r) for r in derived['phases'])
            geometry.append(dict(identity, **{f'{space}_{k}':v for space,g in derived['geometry'].items() for k,v in g.items()}))
            for gap in all_events:
                all_events[gap].extend(meta['episodes'][str(gap)])
            es = meta['episodes']['4']
            expected = [es[i]['event_id'] for i in review_indices(es)]
            assert expected == meta['selected_event_ids']
            membership.append(dict(identity, event_ids=expected))
            checks.append(dict(identity, **meta['source_checks']))
            for event_id in expected:
                roi.append(dict(identity, event_id=event_id, **meta['roi_structure'], roi_localizability=None,
                    target_region_available=None, plausible_alternative_region_available=None,
                    candidate_label_value_available=None, source_specific_replay_feasible=None,
                    counterfactual_edit_feasible=None,
                    feasibility_status='requires semantic source identification in later selected-event review'))
    finally:
        if writer is not None:
            writer.close()
    pd.DataFrame(metrics).to_csv(target('trajectory_metrics.csv'), index=False)
    pd.DataFrame(completions).to_csv(target('completion_table.csv'), index=False)
    pd.DataFrame(geometry).to_csv(target('trajectory_geometry.csv'), index=False)
    pd.DataFrame(phases).to_parquet(target('phase_metrics.parquet'), index=False)
    pd.DataFrame(roi).to_csv(target('roi_feasibility_table.csv'), index=False)
    for gap, rows in all_events.items():
        frame = pd.DataFrame(rows)
        if gap == 4:
            for key in PLACEHOLDERS:
                frame[key] = None
            frame.to_parquet(ROOT/'audit'/'episodes_before_outcome_join.parquet', index=False)
        else:
            frame.to_parquet(target(f'retrieval_episode_gap{gap}_sensitivity.parquet'), index=False)
    save(target('review_membership.json'), dict(at=datetime.now(timezone.utc).isoformat(),
        rule='earliest, nearest midpoint .5 (earlier on tie), latest; deduplicated; all if <=3',
        correctness_used=False, semantic_labels_used=False, causal_effects_used=False, rows=membership))
    save(ROOT/'audit'/'preprocessing_integrity.json', dict(examples=256, primary_gap=4, rows=checks,
        token_rows=pq.ParquetFile(target('token_retrieval_features.parquet')).metadata.num_rows,
        membership_sha256=digest(target('review_membership.json')),
        no_outcome_join_yet=True, annotation_placeholders_empty=True))
    print(json.dumps(dict(event='preprocessing_tables_complete', examples=256,
                         token_rows=sum(r['reasoning_tokens'] for r in metrics),
                         selected_events=sum(len(r['event_ids']) for r in membership))), flush=True)


def finish():
    cohort = json.loads(target('cohort_manifest.json').read_text())['rows']
    outcomes = pd.read_csv(target('outcome_table.csv'), dtype={'item_id':str,'family_id':str})
    completions = pd.read_csv(target('completion_table.csv'), dtype={'item_id':str,'family_id':str})
    metrics = pd.read_csv(target('trajectory_metrics.csv'), dtype={'item_id':str,'family_id':str})
    ids = [r['item_id'] for r in cohort]
    assert list(outcomes.item_id) == list(completions.item_id) == list(metrics.item_id) == ids
    assert len(ids) == len(set(ids)) == 256
    assert set(outcomes.benchmark_label) <= {'correct','wrong','unresolved'}
    assert not outcomes.loc[outcomes.benchmark_label == 'unresolved','unresolved_reason'].isna().any()
    for frame in [outcomes, completions, metrics]:
        assert list(frame.family_id) == [r['family_id'] for r in cohort]
    events = pd.read_parquet(ROOT/'audit'/'episodes_before_outcome_join.parquet')
    membership = json.loads(target('review_membership.json').read_text())
    selected = [e for r in membership['rows'] for e in r['event_ids']]
    integrity = json.loads((ROOT/'audit'/'preprocessing_integrity.json').read_text())
    assert digest(target('review_membership.json')) == integrity['membership_sha256']
    assert set(selected) <= set(events.event_id) and len(selected) == len(set(selected))
    assert events[PLACEHOLDERS].isna().all().all()
    events = events.merge(outcomes[['item_id','benchmark_label']], on='item_id', validate='many_to_one', sort=False)
    events = events.merge(completions[['item_id','completion']], on='item_id', validate='many_to_one', sort=False)
    assert not events[['benchmark_label','completion']].isna().any().any()
    events.to_parquet(target('retrieval_episode_table.parquet'), index=False)
    phase_table = pd.read_parquet(target('phase_metrics.parquet'))
    assert len(phase_table) == 256*4
    assert phase_table.token_count.sum() == metrics.reasoning_tokens.sum()
    assert metrics.reasoning_tokens.sum() == integrity['token_rows']
    assert metrics.retrieval_episode_count.sum() == len(events)
    assert phase_table.retrieval_episode_count.sum() == len(events)
    assert completions.token_cap_reached.sum() == 18
    assert (completions.completion == 'capped').sum() == 18
    summary = (f'# Stage8B Block 0 shared dataset\n\n'
        f'Complete: 256 frozen trajectories / 256 image families. All 12 required artifacts verified.\n\n'
        f'{integrity["token_rows"]:,} reasoning-token rows; {len(events):,} primary gap=4 episodes; '
        f'{len(selected)} outcome-independent review events. Completion: 238 normal, 18 capped.\n\n'
        'Native generations, detector and threshold are unchanged. Original 32 reviewed outcomes retained; '
        'new extraction provenance is frozen before grading. No correctness-conditioned analysis or semantic '
        'annotation was performed. ROI source feasibility remains explicitly unreviewed pending source identification.\n\n'
        'Token features include all eight native passive features, raw/standardized four-dimensional vectors, '
        'absolute indices, normalized phases and validity masks. First-token R remains undefined. '
        'Geometry uses adjacent valid pairs, float64 and epsilon=1e-12. Sensitivity gaps 0/8 are separate.\n\n'
        'Scope limits: local deterministic/manual extraction does not reproduce upstream GPT-4o fallback; '
        'unsupported equivalence remains unresolved. Passive features do not certify causal grounding.\n\n'
        'Next: consume this freeze under the separately written Block 1 plan. That plan is currently absent '
        'from the repository; no substitute analysis was launched.\n')
    target('summary.md').write_text(summary)
    required = ['cohort_manifest.json','outcome_table.csv','completion_table.csv','token_retrieval_features.parquet',
                'retrieval_episode_table.parquet','trajectory_metrics.csv','phase_metrics.parquet',
                'trajectory_geometry.csv','review_membership.json','roi_feasibility_table.csv','summary.md']
    source = json.loads((ROOT/'audit'/'input_freeze.json').read_text())
    std = json.loads((ROOT/'audit'/'standardization_freeze.json').read_text())
    artifact_hashes = {str(target(n)):digest(target(n)) for n in required}
    extra = [ROOT/'audit'/'automatic_extraction_freeze.json',ROOT/'audit'/'manual_extraction_freeze.json',
             ROOT/'audit'/'standardization_freeze.json',ROOT/'audit'/'outcome_scoring_provenance.json',
             ROOT/'audit'/'preprocessing_integrity.json',ROOT/'audit'/'execution_source_freeze.json']
    extra += [target(f'retrieval_episode_gap{g}_sensitivity.parquet') for g in [0,8]]
    save(target('freeze.json'), dict(at=datetime.now(timezone.utc).isoformat(), complete=True,
        cohort_sha256=digest(target('cohort_manifest.json')), detector=source['detector'], tau_R=TAU,
        primary_gap=4, sensitivity_gaps=[0,8], gap_rule='number of inactive intervening tokens; missing R splits',
        coordinates='native zero-based reasoning-token index divided by reasoning length; prediction alignment retained',
        phase_boundaries=[0,.25,.5,.75,1], phase_closure='left closed, right open, last includes 1',
        feature_definitions=Z_KEYS, concentration='1 minus native max-over-heads normalized visual entropy',
        standardization=std, geometry=dict(spaces=['raw','standardized'], dtype='float64',epsilon=EPSILON,
            adjacency='consecutive complete vectors only; no missing-data bridges', displacement='first to last valid vector'),
        review_rule=membership['rule'], selected_review_event_ids=selected,
        adapter_path='code/visual_reasoning/stage8b/v2_scoring.py',
        adapter_sha256=source['source_sha256']['code/visual_reasoning/stage8b/v2_scoring.py'],
        completion_rule='cap takes precedence; otherwise EOS normal; otherwise abnormal; labels independent',
        source_freeze=source, artifacts_sha256=artifact_hashes, supporting_sha256={str(p):digest(p) for p in extra},
        scientific_comparisons_performed=False, roi_semantic_feasibility_reviewed=False))
    freeze = json.loads(target('freeze.json').read_text())
    for path, expected in {**freeze['artifacts_sha256'], **freeze['supporting_sha256']}.items():
        assert digest(path) == expected
    save(ROOT/'audit'/'final_verification.json', dict(verified=True, required_artifacts=12,
        freeze_sha256=digest(target('freeze.json')), examples=256, families=256,
        token_rows=integrity['token_rows'], primary_episodes=len(events), selected_events=len(selected)))
    print(json.dumps(dict(event='block0_frozen', examples=256, required_artifacts=12)), flush=True)


if __name__ == '__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('stage',choices=['moments','tables','finish'])
    globals()[ap.parse_args().stage]()
