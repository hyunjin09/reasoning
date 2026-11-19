"""Score-blind event ordering and fixed native dynamic classification."""
import re
from decimal import Decimal

_NUMBER = re.compile(r'(?<![\w.+-])[+-]?\d+(?:\.\d+)?(?!\d|\.\d)')


def equivalent_numeric_matches(text, value):
    """Propose equal numeric surfaces, retaining signs and exact character spans.

    A following variable is allowed for coefficients (2x). These are proposals;
    fact identity, inference relevance and expression meaning need manual review.
    """
    number = Decimal(str(value))
    return [match for match in _NUMBER.finditer(text) if Decimal(match.group()) == number]


def choose_event_triplet(a_positions,b_positions):
    aa=sorted(set(map(int,a_positions)));bb=sorted(set(map(int,b_positions)))
    if not aa:return None
    first=aa[0]
    for gap in [24,12]:
        candidates=[(first,b,a) for b in bb for a in aa if b-first>=gap and a-b>=gap]
        if candidates:return min(candidates)
    return None


def dynamic_class(vsd,floor=.05):
    s1=vsd['A1']['A']-vsd['A1']['B'];sb=vsd['B']['B']-vsd['B']['A'];s2=vsd['A2']['A']-vsd['A2']['B']
    switch=s1+sb;refresh=sb+s2
    high=all(vsd[e][x]>floor for e,x in [('A1','A'),('B','B'),('A2','A')])
    return {'S_A1':s1,'S_B':sb,'S_A2':s2,'Switch_AB':switch,'Refresh_BA':refresh,
            'dynamic':s1>0 and sb>0 and s2>0 and high and switch>0 and refresh>0}
