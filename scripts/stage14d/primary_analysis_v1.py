"""Frozen family-level analysis of *new* reviewed continuations; no inference.

Caller must first seal raw completeness, answer extraction and evidence reviews.
This module deliberately has no command that reads unreviewed model outputs.
"""
import hashlib
from collections import Counter

from scripts.stage14d.design import ARMS, holm_two, pair_effect, paired_exact_p

ANSWER = {'CORRECT', 'WRONG', 'UNSCORABLE', 'TECHNICAL_MISSING', 'INAPPLICABLE'}
EVIDENCE = {'EXPLICIT_CORRECT', 'EXPLICIT_INCORRECT', 'PARTIAL_OR_APPROXIMATE',
            'CONTRADICTORY', 'NOT_DEMONSTRATED', 'UNSCORABLE',
            'TECHNICAL_MISSING', 'INAPPLICABLE'}


def validate_rows(rows):
    seen = set()
    for row in rows:
        key = (row['family_id'], row['model'], row['arm'])
        if key in seen:
            raise ValueError('Repeated family/model/arm cannot become an independent replicate')
        seen.add(key)
        if row['model'] not in ('I', 'T') or row['arm'] not in ARMS:
            raise ValueError('Unknown model/arm')
        if row['answer'] not in ANSWER or row['evidence'] not in EVIDENCE:
            raise ValueError('Unknown endpoint label; missing is never implicitly wrong')


def summarize(rows, families, model, stratum, endpoint, field, target, control, wrong_rate=False):
    validate_rows(rows)
    if len(set(families)) != len(families):
        raise ValueError('Duplicate conservative family')
    index = {(r['family_id'], r['model'], r['arm']): r for r in rows}
    pairs, transitions = [], Counter()
    status = {target: Counter(), control: Counter()}
    for family in sorted(families):
        values = [index.get((family, model, arm), {}).get(field, 'INAPPLICABLE')
                  for arm in (target, control)]
        for arm, value in zip((target, control), values):
            status[arm][value] += 1
        # Transitions retain raw endpoint direction: control -> target.
        transitions[f'{values[1]}->{values[0]}'] += 1
        if wrong_rate:
            values = [{'CORRECT': 'WRONG', 'WRONG': 'CORRECT'}.get(v, v) for v in values]
        pairs.append(values)
    seed = int(hashlib.sha256(
        f'stage14d-stats-v1|20261011|{endpoint}|{model}|{stratum}'.encode()).hexdigest(), 16) % 2**32
    result = pair_effect(pairs, draws=10000, seed=seed)
    result.update(paired_exact_p(pairs))
    if field == 'answer':
        for a in ('CORRECT', 'WRONG'):
            for b in ('CORRECT', 'WRONG'):
                transitions.setdefault(f'{a}->{b}', 0)
    result.update(model=model, stratum=stratum, endpoint=endpoint, target=target,
                  control=control, field=field, wrong_rate=wrong_rate,
                  transitions=dict(transitions), status_counts={k: dict(v) for k, v in status.items()},
                  pair_direction='target minus control; transitions control -> target',
                  unit='conservative family', weighting='family equal',
                  absent_row='INAPPLICABLE only after caller certifies complete terminal inventory')
    return result


def primary_report(rows, cohorts, overlap):
    """Main report only. Secondary contrasts must follow its immutable seal."""
    validate_rows(rows)
    permitted = {(r['family_id'], model) for model, panel in [('T', cohorts), ('I', overlap)] for r in panel}
    if any((r['family_id'], r['model']) not in permitted for r in rows):
        raise ValueError('Outcome outside frozen model/family panel')
    s1 = [r['family_id'] for r in cohorts if r['stratum'] == 'S1']
    s3 = [r['family_id'] for r in cohorts if r['stratum'] == 'S3']
    if len(s1) != 100 or len(s3) != 100:
        raise ValueError('Planned denominator changed')
    result = {
        'P1': summarize(rows, s1, 'T', 'S1', 'P1', 'answer', 'LOOK_TARGET', 'LOOK_GENERIC'),
        'P2': summarize(rows, s1, 'T', 'S1', 'P2', 'evidence', 'LOOK_TARGET', 'LOOK_GENERIC'),
        'P3': summarize(rows, s3, 'T', 'S3', 'P3', 'answer', 'LOOK_TARGET', 'B0', wrong_rate=True),
        'P3_generic': summarize(rows, s3, 'T', 'S3', 'P3_generic', 'answer', 'LOOK_TARGET', 'LOOK_GENERIC', wrong_rate=True),
    }
    result['holm_adjusted'] = holm_two({k: result[k]['p_two_sided'] for k in ('P1', 'P2')})
    result['positive_co_primary_statistical_criterion'] = all(
        result[k]['effect'] is not None and result[k]['effect'] > 0
        and result['holm_adjusted'][k] is not None and result['holm_adjusted'][k] < .05
        for k in ('P1', 'P2'))
    result['automatic_next_stage_authorized'] = False
    return result
