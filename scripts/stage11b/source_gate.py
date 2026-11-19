"""Necessary discovery conditions that require no model outcomes."""
def source_possible(n, eligible, diversity_ok):
    if not 0 <= eligible <= n:
        raise ValueError('Eligible count must lie within the reviewed count')
    checks = dict(
        eligibility_rate=n > 0 and 5 * eligible >= 2 * n,
        enough_for_twelve_forward_under_accuracy_ceiling=3 * eligible >= 48,
        diversity_and_depth=bool(diversity_ok),
    )
    return dict(possible=all(checks.values()), necessary_checks=checks,
                sufficient_for_go=False)
