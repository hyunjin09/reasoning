"""Prospectively specified matched subsets and conditional elimination."""
from itertools import combinations

def closest(blocks,eligible,target_tokens):
    ids=sorted(eligible);counts={b['block_id']:b['token_count'] for b in blocks}
    candidates=[c for n in range(1,len(ids)+1) for c in combinations(ids,n)]
    if not candidates:return None
    return list(min(candidates,key=lambda c:(abs(sum(counts[i] for i in c)-target_tokens),c)))

def elimination_status(loss_bounds):
    lo,hi=loss_bounds
    return 'ACCEPT' if hi<=1 else 'STOP_LOSS' if lo>=3 else 'STOP_INCONCLUSIVE'
