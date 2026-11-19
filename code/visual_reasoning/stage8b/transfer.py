"""Deterministic transfer audit; labels must be sealed before calling this module."""
import numpy as np


def reasoning_length(pieces):
    """Number of complete native tokens preceding the final-answer boundary."""
    text = ''.join(pieces)
    boundary = text.find('</think>')
    if boundary < 0:
        return len(pieces)
    cursor = 0
    for i, piece in enumerate(pieces):
        cursor += len(piece)
        if cursor > boundary:
            return i
    raise ValueError('Unreachable reasoning boundary')


def evaluate_transfer(scores, demands, events, *, threshold):
    """Scores contain reasoning predictions only, with the first query undefined."""
    if set(scores) != set(demands):
        raise ValueError('Item coverage mismatch')
    active = {}
    for item, values in scores.items():
        values = np.asarray(values, dtype=float)
        if values.ndim != 1 or not np.isfinite(values[1:]).all():
            raise ValueError('Invalid score array')
        active[item] = np.isfinite(values) & (values > threshold)
    positive = [k for k, value in demands.items() if value is True]
    covered = sum(bool(active[k].any()) for k in positive)
    coverage = covered / len(positive) if positive else None
    seen = set()
    group = {key: [] for key in ('T', 'M', 'nonvisual')}
    undefined = []
    for event in events:
        item, query, category = event['item_id'], event['query_index'], event['category']
        if item not in scores or type(query) is not int or not 0 <= query < len(active[item]):
            raise ValueError('Query out of range')
        if category not in group:
            raise ValueError('Unsupported audit category')
        if (item, query) in seen:
            raise ValueError('Duplicate native query')
        seen.add((item, query))
        if not np.isfinite(scores[item][query]):
            undefined.append(event)
            continue
        hit = bool(active[item][max(0, query-8):query+9].any()) if category == 'T' else bool(active[item][query])
        group[category].append(dict(item_id=item, query_index=query, hit=hit))
    counts = {key: len(value) for key, value in group.items()}
    t_hits = sum(x['hit'] for x in group['T'])
    t_rate = t_hits / counts['T'] if counts['T'] else None
    negatives = group['M'] + group['nonvisual']
    false_alarms = sum(x['hit'] for x in negatives)
    false_rate = false_alarms / len(negatives) if negatives else None
    item_count = len({x['item_id'] for values in group.values() for x in values})
    adequate = counts['T'] >= 24 and len(negatives) >= 24 and item_count >= 16 and bool(positive)
    passed = adequate and coverage >= .7 and t_rate >= .7 and false_rate <= .2
    negative_classes = {}
    for key in ('M', 'nonvisual'):
        hits = sum(x['hit'] for x in group[key])
        negative_classes[key] = dict(queries=counts[key], false_alarms=hits,
                                     false_alarm_rate=hits/counts[key] if counts[key] else None)
    return dict(status='PASS' if passed else 'FAIL' if adequate else 'INCONCLUSIVE',
                demanding_items=len(positive), items_with_retrieval=covered, item_coverage=coverage,
                T=dict(queries=counts['T'], aligned_queries=t_hits, alignment_rate=t_rate),
                negative=dict(queries=len(negatives), false_alarms=false_alarms, false_alarm_rate=false_rate),
                negative_classes=negative_classes, annotated_items_with_valid_queries=item_count,
                undefined_queries=undefined, sufficient_manual_coverage=adequate,
                event_results=group, threshold=float(threshold), alignment_radius=8)
