"""Fixed metadata matching for the secondary held-out probe comparison."""
from visual_reasoning.stage7a.thresholds import matching_metadata


def match_test_events(rows, entries, tolerances):
    """Greedy nearest metadata pairs, without looking at any passive feature."""
    metadata = {r['id']: matching_metadata(entries[r['id']]) for r in rows}
    candidates = []
    left = sorted((r for r in rows if r['label'] == 0), key=lambda r: r['id'])
    right = sorted((r for r in rows if r['label'] == 1), key=lambda r: r['id'])
    for a in left:
        for b in right:
            if a['group_id'] == b['group_id']: continue
            ma, mb = metadata[a['id']], metadata[b['id']]
            if any(ma['exact'][k] != mb['exact'][k] for k in tolerances['exact_keys']): continue
            if set(ma['continuous']) != set(mb['continuous']): continue
            distances = {k: abs(ma['continuous'][k]-mb['continuous'][k])/tolerances['continuous'][k]['tolerance']
                         for k in ma['continuous']}
            if any(value > 1. for value in distances.values()): continue
            candidates.append((sum(distances.values()), a['id'], b['id'], distances))
    used, pairs = set(), []
    for distance, a, b, values in sorted(candidates, key=lambda p: p[:3]):
        if a in used or b in used: continue
        used.update((a, b))
        pairs.append(dict(negative_id=a, positive_id=b, normalized_distance=distance, covariate_distances=values))
    selected = [r for r in rows if r['id'] in used]
    return selected, dict(pairs=pairs, events=len(selected),
                         groups_per_class={str(label): len({r['group_id'] for r in selected if r['label'] == label})
                                           for label in (0, 1)},
                         causal_magnitudes_used=False, passive_features_used=False,
                         rule='Prospective exact metadata keys and discovery-only calipers; distinct image family per pair; no event reused')
