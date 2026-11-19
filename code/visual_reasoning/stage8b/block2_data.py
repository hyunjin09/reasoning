"""Frozen Block2 event assembly, semantic geometry and deterministic matching."""
import json
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

from visual_reasoning.stage3b7.roi import map_changed_pixels_to_tokens

ROOT = Path('outputs/stage8b_block2/v1')
B0 = Path('outputs/stage8b_block0/v1')
PREFIX = 'stage8b_block2_'
P1 = ['R_onset', 'auc_above_tau', 'mean_qk_visual_nonvisual', 'mean_visual_mass']
P2 = ['qk_T_X', 'share_T_X', 'target_rank', 'target_share']
P3 = ['source_entropy', 'top2_margin', 'target_consensus']
SECONDARY = ['peak_R', 'mean_R', 'duration', 'mean_visual_concentration', 'delta_R_pre32',
             'claim_R', 'claim_qk_visual_nonvisual', 'claim_visual_mass']
TRANSPORT = ['target_alphaV_norm', 'target_X_alphaV_margin', 'visual_alphaV_norm',
             'target_postWO_norm', 'visual_postWO_norm', 'visual_residual_ratio',
             'head_cancellation_ratio', 'target_X_value_cosine']


def source_positions(sources, metadata):
    """Existing any-pixel grid mapping; shared cells are excluded from all sources.

    Collision exclusion is geometrical and deterministic. No nearest-token
    expansion, source relabeling or attention-based fallback is permitted.
    """
    width, height = metadata['original_image_size']
    temporal, rows, cols = metadata['visual_mapping']['merged_grid_shape']
    visual = metadata['visual_token_indices']
    assert temporal == 1 and len(visual) == rows*cols
    raw = {}
    for source in sources:
        mask = np.zeros((height, width), dtype=bool)
        x0, y0, x1, y1 = source['roi']; mask[y0:y1, x0:x1] = True
        raw[source['role']] = map_changed_pixels_to_tokens(mask, merged_rows=rows, merged_cols=cols)
    counts = Counter(i for group in raw.values() for i in group)
    shared = sorted(i for i, count in counts.items() if count > 1)
    mapped = {role: [visual[i] for i in group if counts[i] == 1] for role, group in raw.items()}
    return mapped, dict(raw_local_cells=raw, excluded_shared_local_cells=shared,
                        source_token_counts={k: len(v) for k, v in mapped.items()},
                        rule='existing any-pixel mapping, shared cells excluded from every source')


def event_features():
    local = pd.read_parquet(ROOT/(PREFIX+'local_read_table.parquet'))
    events = pd.read_parquet(B0/'stage8b_block0_retrieval_episode_table.parquet')
    cols = ['event_id', 'normalized_start', 'peak_R', 'mean_R', 'auc_above_tau', 'duration',
            'mean_qk_visual_nonvisual', 'mean_visual_mass', 'mean_visual_concentration']
    local = local.merge(events[cols], on='event_id', validate='one_to_one')
    needed = ['item_id', 'token_index', 'R', 'visual_mass', 'qk_visual_nonvisual']
    tokens = pd.read_parquet(B0/'stage8b_block0_token_retrieval_features.parquet', columns=needed)
    aligned = []
    for item, group in local.groupby('item_id', sort=False):
        token = tokens.loc[tokens.item_id == item].set_index('token_index')
        for index, row in group.iterrows():
            onset = int(row.start_token); claim = int(row.claim_start_token)
            local.loc[index, 'R_onset'] = token.loc[onset, 'R']
            before = token.loc[max(0, onset-32):onset-1, 'R'].dropna()
            local.loc[index, 'delta_R_pre32'] = token.loc[onset, 'R']-before.median() if len(before) >= 4 else np.nan
            for key in ['R', 'visual_mass', 'qk_visual_nonvisual']:
                local.loc[index, 'claim_'+key] = token.loc[claim, key]
            for offset in range(-32, 33):
                if onset+offset in token.index:
                    point = token.loc[onset+offset]
                    aligned.append(dict(event_id=row.event_id, family_id=row.family_id, local=row.local,
                                        offset=offset, **{key: point[key] for key in ['R', 'visual_mass', 'qk_visual_nonvisual']}))
    return local, pd.DataFrame(aligned)


def match_events(frame):
    eligible = frame.loc[frame.source_localizable & frame.local.isin(['L+', 'L-'])].sort_values('review_order')
    failures = eligible.loc[eligible.local == 'L-']
    controls = eligible.loc[eligible.local == 'L+'].copy()
    pairs, unmatched = [], []
    for _, event in failures.iterrows():
        pool = controls.loc[(controls.subtype == event.subtype) & (controls.roi_type == event.roi_type)]
        if not len(pool):
            unmatched.append(dict(failure=event.event_id, reason='No unused L+ in exact subtype/ROI-type stratum'))
            continue
        completed = pool.loc[pool.completion == event.completion]
        completion_exact = bool(len(completed))
        if completion_exact:
            pool = completed
        cost = ((pool.normalized_start-event.normalized_start).abs() + (pool.R_onset-event.R_onset).abs()
                + .25*(np.log(pool.reasoning_tokens)-np.log(event.reasoning_tokens)).abs()
                + .25*(pool.log_question_length-event.log_question_length).abs())
        chosen = pool.loc[cost.idxmin()]
        pairs.append(dict(pair_id=f'p{len(pairs):03d}', failure=event.event_id, control=chosen.event_id,
                          cost=float(cost.min()), completion_exact=completion_exact,
                          subtype=event.subtype, roi_type=event.roi_type))
        controls = controls.loc[controls.event_id != chosen.event_id]
    return pairs, unmatched
