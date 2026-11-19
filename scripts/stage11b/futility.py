"""Finite-cohort logical impossibility, not a sequential significance test."""
def forward_upper_bound(pairs):
    for thinking, cot in pairs:
        if thinking not in (True, False, None) or cot not in (True, False, None):
            raise ValueError('Each observed correctness must be boolean or unknown')
    return sum(thinking is not False and cot is not True for thinking, cot in pairs)
