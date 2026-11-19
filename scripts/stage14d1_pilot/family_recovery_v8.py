"""Keep complete families; rebuild partial families under one execution schedule."""
def family_policy(expected, completed):
    if not set(completed).issubset(expected):
        raise ValueError('Unexpected physical request in completed family')
    if set(completed) == set(expected):
        return dict(completed), set()
    return {}, set(expected)
