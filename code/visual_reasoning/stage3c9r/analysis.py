"""Base-level summaries of the frozen event-window families."""

from collections import Counter
import statistics

from visual_reasoning.stage3c8.analysis import summarize_effect
from visual_reasoning.stage3c9.analysis import repeated_checkpoint_status
from visual_reasoning.stage3c9r.protocol import classify_family


def classify_bases(manifest, families, *, effect_floor=.05, final_gains=None):
    bases = []
    ranks = {'C0': 0, 'C1': 1, 'C2': 2, 'C3': 3}
    for item in manifest:
        base = str(item['base_problem_id'])
        events = []
        metrics = []
        for event in item['events']:
            eid = event['event_id']
            windows = {}
            for window in ('W8', 'W16'):
                if (base, eid, window) not in families:
                    continue
                result = classify_family(families[base, eid, window], effect_floor=effect_floor,
                    final_rescue_gains=(final_gains or {}).get((base, eid, window)))
                windows[window] = result
                metrics.append(result)
            if not windows:
                raise ValueError('No mechanically valid window for a frozen event')
            events.append({**event, 'classification': max((r['classification'] for r in windows.values()), key=ranks.get),
                'qualifying_windows': [w for w,r in windows.items() if r['functional_span_rescue']],
                'source_sensitive_windows': [w for w,r in windows.items() if r['source_sensitive']],
                'windows': windows})
        bases.append({'base_problem_id': base, 'events': events,
            'source_sensitive_event_count': sum(bool(e['source_sensitive_windows']) for e in events),
            **repeated_checkpoint_status(events),
            'median_source_loss': statistics.median(r['source_loss_mean'] for r in metrics),
            'median_event_rescue': statistics.median(r['rescue_gain_mean'] for r in metrics),
            'median_event_minus_neighbor': statistics.median(r['event_minus_neighbor'] for r in metrics)})
    return bases


def summarize_bases(bases):
    metrics = ['source_sensitive_event_count', 'checkpoint_count', 'repeated_checkpoint',
               'median_source_loss', 'median_event_rescue', 'median_event_minus_neighbor']
    return {
        'independent_unit': 'base_problem_id', 'N_unique_bases': len(bases),
        'bootstrap': '10000 draws of whole bases; seed 12348; empirical mean CI',
        'statistics': {m: summarize_effect({b['base_problem_id']: float(b[m]) for b in bases}) for m in metrics},
        'source_sensitive_events': sum(b['source_sensitive_event_count'] for b in bases),
        'checkpoint_events': sum(b['checkpoint_count'] for b in bases),
        'checkpoint_count_per_base': {str(k): sum(b['checkpoint_count'] == k for b in bases) for k in range(4)},
        'repeated_checkpoint_bases': sum(b['repeated_checkpoint'] for b in bases),
        'class_counts': dict(Counter(e['classification'] for b in bases for e in b['events'])),
    }
