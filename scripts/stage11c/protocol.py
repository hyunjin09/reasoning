"""Frozen Stage11C gates and outcome-independent allocation rules."""
import hashlib
import math
from collections import defaultdict


def choose_cap(cap_hits, n=12, pathological_caps=()):
    assert n == 12 and set(cap_hits) == {4096, 8192}
    for cap in [4096, 8192]:
        counts = cap_hits[cap]
        assert len(counts) == 2 and all(0 <= x <= n for x in counts)
        if all(10*x < n for x in counts) and cap not in pathological_caps:
            return dict(cap=cap, completion_limited=False)
    return dict(cap=8192, completion_limited=True)


def completion_gate(thinking_caps, direct_caps):
    if len(thinking_caps) < 16 or len(direct_caps) < 16:
        return 'INCOMPLETE'
    assert len(thinking_caps) == len(direct_caps) == 16
    if any(x is None for x in thinking_caps + direct_caps):
        return 'INCOMPLETE'
    return 'STOP' if max(sum(thinking_caps), sum(direct_caps)) > 4 else 'PASS'


def native_gate(pairs, completion_pathology):
    assert len(pairs) >= 64 and all(type(t) is bool and type(d) is bool for t, d in pairs)
    n = len(pairs)
    t = sum(t for t, d in pairs)
    d = sum(d for t, d in pairs)
    forward = sum(t and not d for t, d in pairs)
    checks = dict(thinking_accuracy=4*t >= n, direct_accuracy=10*d >= n,
                  native_gap=10*(t-d) >= n, informative_pairs=forward >= 12,
                  completion_valid=not completion_pathology)
    return dict(n=n, thinking_correct=t, direct_correct=d, forward=forward,
                reverse=sum(d and not t for t, d in pairs), checks=checks,
                thinking_accuracy=t/n, direct_accuracy=d/n, gap=(t-d)/n,
                **{'pass': all(checks.values())})


def order_key(row, seed, purpose):
    return hashlib.sha256(f"stage11c:{seed}:{purpose}:{row['family_id']}".encode()).hexdigest()


def stratified(rows, n, seed, purpose, fields):
    assert 0 < n <= len(rows)
    groups = defaultdict(list)
    for row in rows:
        groups[tuple(str(row[f]) for f in fields)].append(row)
    counts = {k: math.floor(n*len(v)/len(rows)) for k, v in groups.items()}
    remainders = sorted(groups, key=lambda k: (-(n*len(groups[k])/len(rows)-counts[k]), k))
    for key in remainders[:n-sum(counts.values())]:
        counts[key] += 1
    selected = [row for key, group in sorted(groups.items())
                for row in sorted(group, key=lambda r: order_key(r, seed, purpose))[:counts[key]]]
    return sorted(selected, key=lambda r: order_key(r, seed, purpose+'-order'))
