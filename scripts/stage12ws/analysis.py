"""Small-family, missingness-aware implementation of the frozen thresholds."""
from scripts.stage12ws.protocol import paired

def conjunction(values):
    return False if False in values else None if None in values else True

def signature(full,minus_d,estar_d,estar,eligible):
    return conjunction([eligible,paired(full,minus_d)['at_least_3'],paired(estar_d,estar)['at_least_3']])

def distributed(single_bounds,composite,control,length_ratio):
    single=False if any(lo>=4 for lo,hi in single_bounds) else None if any(hi>=4 for lo,hi in single_bounds) else True
    combo=True if composite[0]>=4 else False if composite[1]<4 else None
    matched=None if control is None else True if control[1]<4 else False if control[0]>=4 else None
    adequate=True if length_ratio is not None and .8<=length_ratio<=1.25 else None
    return conjunction([single,combo,matched,adequate])
