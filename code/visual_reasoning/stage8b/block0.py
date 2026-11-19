"""Outcome-blind Block 0 definitions; never modify the frozen native modules."""
import numpy as np

TAU = 0.5478025980771918
EPSILON = 1e-12
Z_KEYS = ['R', 'qk_visual_nonvisual', 'visual_mass', 'visual_concentration']
PLACEHOLDERS = ['event_semantic_type', 'local_read_outcome', 'demanded_source_id',
                'alternative_source_id', 'roi_available', 'local_claim_span',
                'evidence_use_token', 'same_fact_reused_later', 'review_status']


def phase(position):
    return np.minimum(np.floor(np.asarray(position) * 4).astype(int), 3) + 1


def episodes(scores, gap):
    scores = np.asarray(scores, dtype=np.float64)
    active = np.flatnonzero(np.isfinite(scores) & (scores > TAU))
    if not len(active):
        return []
    missing = np.r_[0, np.cumsum(~np.isfinite(scores))]
    split = ((np.diff(active) - 1 > gap) |
             (missing[active[1:]] - missing[active[:-1]+1] > 0))
    groups = np.split(active, np.flatnonzero(split) + 1)
    bounds = [(int(g[0]), int(g[-1])) for g in groups]
    rows = []
    for i, (start, end) in enumerate(bounds):
        segment = scores[start:end+1]
        rows.append(dict(episode_index=i, start_token=start, end_token=end,
                         duration=end-start+1, midpoint=(start+end)/2,
                         normalized_start=start/len(scores),
                         normalized_midpoint=(start+end)/2/len(scores),
                         phase=int(phase(start/len(scores))),
                         peak_R=float(segment.max()), mean_R=float(segment.mean()),
                         auc_above_tau=float(np.maximum(segment-TAU, 0).sum()),
                         active_tokens=int((segment > TAU).sum()), gap_rule=gap,
                         preceding_gap=start-bounds[i-1][1]-1 if i else None,
                         following_gap=bounds[i+1][0]-end-1 if i+1 < len(bounds) else None))
    return rows


def review_indices(rows):
    if len(rows) <= 3:
        return list(range(len(rows)))
    middle = min(range(len(rows)), key=lambda i: (abs(rows[i]['normalized_midpoint']-.5), i))
    return sorted({0, middle, len(rows)-1})


def completion(receipt, text):
    cap, eos = bool(receipt['at_length_cap']), bool(receipt['normal_eos'])
    think = '</think>' in text
    return dict(completion='capped' if cap else 'normal completed' if eos else 'other abnormal stop',
                raw_completion=receipt['completion'], eos_present=eos, think_end_present=think,
                token_cap_reached=cap, generated_token_count=receipt['tokens'],
                final_answer_section_present=think and bool(text.split('</think>', 1)[1].replace('<|im_end|>', '').strip()),
                abnormal_stop_subtype=('cap_after_think' if think else 'cap_without_think') if cap
                else None if eos else 'no_eos_no_cap')


def feature_vectors(features, scores):
    return np.column_stack([scores, features[:, 1], features[:, 0], 1-features[:, 5]])


def geometry(z, *, device='cpu'):
    """Torch float64 on the allocated GPU; CPU reference available for tests."""
    import torch
    x = torch.as_tensor(z, dtype=torch.float64, device=device)
    valid = torch.isfinite(x).all(1)
    pairs = valid[1:] & valid[:-1]
    distances = torch.linalg.vector_norm(x[1:]-x[:-1], dim=1)
    distances = torch.where(pairs, distances, torch.nan)
    indices = torch.nonzero(valid).flatten()
    count = int(pairs.sum().item())
    path = float(distances[pairs].sum().item()) if count else None
    first = int(indices[0].item()) if len(indices) else None
    last = int(indices[-1].item()) if len(indices) else None
    displacement = float(torch.linalg.vector_norm(x[last]-x[first]).item()) if len(indices) >= 2 else None
    return dict(path_length=path, transition_normalized_path_length=path/count if count else None,
                net_displacement=displacement,
                tortuosity=path/(displacement+EPSILON) if path is not None and displacement is not None else None,
                valid_transitions=count, first_valid_token=first, last_valid_token=last,
                valid_vectors=int(valid.sum().item())), distances.cpu().numpy()


def trajectory_metrics(scores, events, *, generated_tokens, post_think_tokens):
    scores = np.asarray(scores)
    length = len(scores)
    durations = [e['duration'] for e in events]
    peaks = [e['peak_R'] for e in events]
    gaps = [e['preceding_gap'] for e in events[1:]]
    row = dict(generated_tokens=generated_tokens, reasoning_tokens=length,
               post_think_tokens=post_think_tokens, retrieval_episode_count=len(events),
               retrieval_density=1000*len(events)/length if length else None,
               active_token_count=int(np.sum(scores > TAU)),
               active_token_fraction=float(np.sum(scores > TAU)/length) if length else None,
               valid_R_tokens=int(np.isfinite(scores).sum()),
               first_retrieval_token=events[0]['start_token'] if events else None,
               first_retrieval_normalized=events[0]['normalized_start'] if events else None,
               episodes_after_first=max(len(events)-1, 0))
    for label, values, functions in [('duration', durations, ['mean', 'median', 'max']),
                                     ('peak', peaks, ['mean', 'max']),
                                     ('gap', gaps, ['mean', 'median', 'min'])]:
        for name in functions:
            row[f'{name}_{label}'] = float(getattr(np, name)(values)) if values else None
    row['mean_auc'] = float(np.mean([e['auc_above_tau'] for e in events])) if events else None
    row['gap_cv'] = float(np.std(gaps)/np.mean(gaps)) if len(gaps) >= 2 and np.mean(gaps) > 0 else None
    for boundary in [32, 64, 128]:
        row[f'returns_after_gap_gt_{boundary}'] = sum(g > boundary for g in gaps)
    for boundary in [.25, .5, .75, .9]:
        row[f'late_episode_fraction_gt_{boundary}'] = sum(e['normalized_start'] > boundary for e in events)/len(events) if events else None
    return row


def phase_metrics(table, events, movements):
    rows = []
    phases = table['phase'].to_numpy()
    for p in range(1, 5):
        sub = table.loc[table['phase'] == p]
        n = len(sub)
        ecount = sum(e['phase'] == p for e in events)
        row = dict(phase=p, token_count=n, retrieval_episode_count=ecount,
                   retrieval_density=1000*ecount/n if n else None,
                   active_token_fraction=float(sub['active_retrieval'].sum()/n) if n else None)
        for feature in ['R', 'qk_visual_nonvisual', 'visual_mass', 'visual_concentration']:
            values = sub[feature].dropna().to_numpy()
            row['mean_'+feature] = float(values.mean()) if len(values) else None
            if feature == 'R':
                row['max_R'] = float(values.max()) if len(values) else None
        mask = (phases[:-1] == p) & (phases[1:] == p)
        for name, steps in movements.items():
            valid = mask & np.isfinite(steps)
            count = int(valid.sum())
            row[name+'_movement_transitions'] = count
            row[name+'_path_length'] = float(steps[valid].sum()) if count else None
            row[name+'_mean_movement'] = float(steps[valid].mean()) if count else None
        rows.append(row)
    return rows
