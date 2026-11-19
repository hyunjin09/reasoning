"""Set-demand semantics and score-free annotation packet fields."""


def demand_type(sources):
    if sources is None:
        return 'UNRESOLVED'
    count = len(set(sources))
    return 'NONE_VISUAL' if count == 0 else 'SINGLETON' if count == 1 else 'COMPOUND'


def transition_type(pre, post):
    if pre is None or post is None:
        return 'UNRESOLVED'
    pre, post = set(pre), set(post)
    if pre == post:
        return 'T0'
    if not pre or not post:
        return 'T5'
    if pre.isdisjoint(post):
        return 'T1'
    if pre < post:
        return 'T2'
    if post < pre:
        return 'T3'
    return 'T4'


def primary_semantic_eligible(pre, post):
    return (demand_type(pre) == demand_type(post) == 'SINGLETON'
            and transition_type(pre, post) in {'T0', 'T1'})


def blind_span(row):
    return {key: row[key] for key in (
        'span_id', 'text', 'char_start', 'char_end', 'token_start',
        'token_end', 'normalized_token_progress')}
