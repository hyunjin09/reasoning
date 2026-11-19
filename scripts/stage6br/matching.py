"""Score-free, frozen semantic matching constraints and no-reuse assignment."""
import math


def match_priority(transition, hold, rules):
    if any(transition[k] != hold[k] for k in ('split', 'condition', 'readout_type', 'evidence_class')):
        return None
    gap_a, gap_b = transition['token_gap'], hold['token_gap']
    if min(gap_a, gap_b) <= 0:
        return None
    ratio = max(gap_a, gap_b) / min(gap_a, gap_b)
    delta = abs(transition['normalized_progress'] - hold['normalized_progress'])
    same = transition['base_id'] == hold['base_id']
    if same:
        tolerance = rules['same_base_tolerances']
        if delta > tolerance['maximum_absolute_progress_difference'] or ratio > tolerance['maximum_token_gap_ratio']:
            return None
    else:
        if (transition['dataset'] != hold['dataset']
                or math.floor(transition['normalized_progress'] / .2) != math.floor(hold['normalized_progress'] / .2)
                or ratio > rules['cross_base_maximum_token_gap_ratio']):
            return None
    return (not same, transition['demand_after'] != hold['demand_after'] if same else False,
            delta, ratio, hold['id'])


def maximum_matching(transitions, holds, rules):
    """Deterministic augmenting paths maximize count without reusing a hold.

    Each adjacency list follows the declared semantic priority. This is not a
    claim of a global minimum-cost assignment among all maximum matchings.
    """
    graph = {}
    for t in transitions:
        choices = [(match_priority(t, h, rules), h['id']) for h in holds]
        graph[t['id']] = [hid for score, hid in sorted(
            (score, hid) for score, hid in choices if score is not None)]
    return match_graph(graph), graph


def match_graph(graph):
    """Match interval IDs, keeping alternative readouts from multiplying units."""
    held = {}

    def assign(tid, seen):
        for hid in graph[tid]:
            if hid in seen:
                continue
            seen.add(hid)
            if hid not in held or assign(held[hid], seen):
                held[hid] = tid
                return True
        return False

    for tid in sorted(graph, key=lambda key: (len(graph[key]), key)):
        assign(tid, set())
    return sorted((tid, hid) for hid, tid in held.items())
