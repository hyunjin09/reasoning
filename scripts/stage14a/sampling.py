"""Deterministic source-stratified selection, frozen before eligibility review."""
import json
from collections import defaultdict

from scripts.stage14a.common import digest


def strata(rows, fields, prefix):
    if len({r['family_id'] for r in rows}) != len(rows):
        raise ValueError('Family IDs must be unique')
    groups = defaultdict(list)
    for row in rows:
        key = json.dumps([row.get(k) for k in fields], ensure_ascii=False)
        groups[key].append(row)
    return {k: sorted(v, key=lambda r: (digest(prefix + r['family_id']), r['family_id']))
            for k, v in groups.items()}


def stratified_order(rows, fields, prefix):
    groups = strata(rows, fields, prefix)
    total, used, result = len(rows), {k: 0 for k in groups}, []
    for index in range(total):
        available = [k for k, v in groups.items() if used[k] < len(v)]
        key = min(available, key=lambda k: (
            -((index + 1) * len(groups[k]) - used[k] * total), digest(prefix + 'stratum|' + k)))
        result.append(groups[key][used[key]])
        used[key] += 1
    return result


def confirm(rows, n, fields, prefix):
    if not 0 <= n <= len(rows):
        raise ValueError('Requested confirmation size exceeds available families')
    groups = strata(rows, fields, prefix)
    total = len(rows)
    quotas = {k: n * len(v) // total for k, v in groups.items()}
    for k in sorted(groups, key=lambda k: (-(n * len(groups[k]) % total), digest(prefix + 'quota|' + k)))[:n - sum(quotas.values())]:
        quotas[k] += 1
    selected = [r for k in sorted(groups) for r in groups[k][:quotas[k]]]
    return sorted(selected, key=lambda r: (digest(prefix + r['family_id']), r['family_id']))


def map_versions(rows):
    groups = defaultdict(dict)
    for row in rows:
        key, version = str(row['problem_index']), row['problem_version']
        if version in groups[key]:
            raise ValueError(f'Duplicate family/version: {key}/{version}')
        groups[key][version] = row
    for key, versions in groups.items():
        if len({r['answer'] for r in versions.values()}) != 1:
            raise ValueError(f'Inconsistent source gold: {key}')
    return dict(groups)
