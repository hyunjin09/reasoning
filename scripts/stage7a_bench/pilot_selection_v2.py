"""Validate a reviewed candidate pool and proposed pilot membership without scoring.

The caller must load verified native artifacts, supply every frozen condition's
summary, and finish the human eligibility review before invoking this function.
This is a mechanical validation layer: it does not infer identifiability, choose
claims, certify provenance, persist a freeze, or set causal_pilot_frozen. A GPU
worker must separately verify the persisted freeze and recompile native entries.
"""
from collections import Counter
from copy import deepcopy

from scripts.stage7a_bench.causal_provenance_v2 import object_sha
from scripts.stage7a_bench.native_yield_v2 import indexed

GATE_CLASSES = ('local_error', 'unsupported', 'paired_disagreement', 'strong_faithful')


def validate_selection(screen, frozen_counts, entries, decisions, selected_ids, family_map):
    if not frozen_counts or set(screen) != set(frozen_counts):
        raise ValueError('All frozen benchmark conditions must be present')
    if max(frozen_counts.values()) < 200:
        raise ValueError('Complete initial 200-example screen is required')
    benchmarks = set()
    for condition, expected in frozen_counts.items():
        row = screen[condition]
        fields = ('frozen', 'generated', 'unavailable', 'reviewed', 'pending_generation', 'pending_review')
        if (type(expected) is not int or expected <= 0 or
                any(type(row.get(k)) is not int or row[k] < 0 for k in fields) or
                row['frozen'] != expected or row['generated']+row['unavailable'] != expected or
                row['reviewed'] != row['generated'] or row['pending_generation'] != 0 or
                row['pending_review'] != 0 or row.get('screen_complete') is not True or
                row.get('condition') != condition):
            raise ValueError('Every frozen condition requires complete generation and semantic review')
        benchmarks.add(row.get('benchmark'))
    if len(benchmarks) != 1 or not next(iter(benchmarks)):
        raise ValueError('A pilot selection covers exactly one benchmark')
    benchmark = next(iter(benchmarks))
    pool, reviews = indexed(entries, 'id'), indexed(decisions, 'id')
    if set(pool) != set(reviews):
        raise ValueError('Every prepared candidate requires an explicit eligibility decision')
    eligible = {'failure': [], 'faithful': []}
    gate = {name: set() for name in GATE_CLASSES}
    excluded = []
    for key, entry in pool.items():
        review = reviews[key]
        if review.get('entry_sha256') != object_sha(entry):
            raise ValueError('Eligibility review candidate digest differs')
        if (entry.get('selection_used_causal_or_passive_scores') is not False or
                review.get('causal_or_passive_scores_used') is not False or
                entry.get('causal_state') is not None or entry.get('causal_pilot_frozen') is not False):
            raise ValueError('Pilot selection must precede causal/passive scores and freezing')
        if (entry.get('benchmark') != benchmark or entry.get('condition') not in screen or
                entry.get('analysis_family_id') != family_map.get(entry.get('base_id')) or
                not entry.get('analysis_family_id')):
            raise ValueError('Candidate benchmark, condition or verified family mismatch')
        if type(review.get('eligible')) is not bool or not isinstance(review.get('review_note'), str) or not review['review_note'].strip():
            raise ValueError('Explicit eligibility and review reason required')
        if not review['eligible']:
            excluded.append(key)
            continue
        if review.get('structurally_identifiable') is not True:
            raise ValueError('Eligible candidate requires reviewed structural identifiability')
        if (entry.get('row', {}).get('no_image') is not False or benchmark == 'phantom_0' or
                not entry.get('source_groups', {}).get('G')):
            raise ValueError('Source-causal pilot requires an actual visual input')
        claim = entry['reviewed_claim']
        if claim.get('demand') != 'singleton' or type(claim.get('locally_correct')) is not bool:
            raise ValueError('Primary pilot read requires an adjudicated singleton claim')
        stratum, kind = review.get('pilot_stratum'), review.get('candidate_class')
        if stratum not in eligible or kind not in (*GATE_CLASSES, 'integration_error'):
            raise ValueError('Explicit candidate class and pilot stratum required')
        if (stratum == 'faithful' and (kind != 'strong_faithful' or claim['locally_correct'] is not True) or
                stratum == 'failure' and kind == 'strong_faithful' or
                kind == 'local_error' and claim['locally_correct'] is not False or
                kind == 'integration_error' and (claim['locally_correct'] is not True or not entry.get('downstream_review'))):
            raise ValueError('Candidate class/stratum contradicts the actual local claim or downstream review')
        eligible[stratum].append(key)
        if kind in gate:
            gate[kind].add(entry['base_id'])
    # Count distinct native bases at the entry gate; repeated claims must not
    # turn one native example into sixteen independent entry candidates.
    gate_counts = {k: len(v) for k, v in gate.items()}
    if max(gate_counts.values()) < 16:
        raise ValueError('Entry gate needs sixteen distinct reviewed native candidates in one class')
    if set(selected_ids) != set(eligible):
        raise ValueError('Both failure and faithful membership must be explicit')
    flattened = [key for stratum in eligible for key in selected_ids[stratum]]
    if len(flattened) != len(set(flattened)):
        raise ValueError('Duplicate selected candidate')
    for stratum, available in eligible.items():
        chosen = selected_ids[stratum]
        if not set(chosen) <= set(available):
            raise ValueError('Selected candidate is not eligible for its stratum')
        if stratum == 'faithful' and len(chosen) < 16:
            raise ValueError('At least sixteen faithful controls are required')
        target = min(32, len(available))
        if len(chosen) != target:
            raise ValueError('Select32 when available; otherwise use all eligible '+stratum+' candidates')
    selected = []
    for stratum in eligible:
        for key in selected_ids[stratum]:
            entry = deepcopy(pool[key])
            entry['pilot_stratum'] = stratum
            selected.append(entry)
    return dict(status='VALIDATED_SELECTION_NOT_FROZEN', benchmark=benchmark,
        entry_gate_passed=True, entry_gate_counts=gate_counts,
        eligible_counts={k: len(v) for k, v in eligible.items()},
        selected_counts={k: len(v) for k, v in selected_ids.items()},
        selected_unique_bases=len({e['base_id'] for e in selected}),
        selected_unique_families=len({e['analysis_family_id'] for e in selected}),
        small_failure_exception=len(eligible['failure']) < 16,
        excluded_ids=excluded, selected_entries=selected,
        candidate_pool_sha256=object_sha(entries), eligibility_review_sha256=object_sha(decisions),
        screen_sha256=object_sha(screen), frozen_counts_sha256=object_sha(frozen_counts),
        selected_screen_classes=dict(Counter(e.get('semantic_review', {}).get('screen_label') for e in selected)),
        causal_states_assigned=False, thresholds_retuned=False,
        scope='Claim-level reviewed eligibility; final accuracy and whole-response screening labels do not assign causal states. Persisted freeze, artifact verification and GPU mechanics remain mandatory.')
