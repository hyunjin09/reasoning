"""Terminal stage decision; fresh-set failure takes generalization precedence."""


def decide(d, candidates, validation):
    if not d['pass']:
        return 'D_INVALID'
    assert candidates is not None
    if not any(r['pass'] for r in candidates.values()):
        return 'C_INVALID'
    assert validation is not None and len(validation) == 2 and 'D' in validation
    return 'CONTRACT_VALID' if all(r['pass'] for r in validation.values()) else 'CONTRACT_UNSTABLE'
