import numpy as np


def contrasts(x):
    x=np.asarray(x,dtype=float)
    assert x.ndim==3 and x.shape[1:]==(2,5)
    return np.column_stack((x[:,0,4]-x[:,0,0],x[:,1,4]-x[:,1,0],
                            x[:,0,3]-x[:,0,1],x[:,1,3]-x[:,1,1]))


def mask_cutoff(prefix_tokens):
    assert prefix_tokens>=0
    return max(0,prefix_tokens-1)


def earliest_transition(pairs):
    assert len(pairs)==5
    yes=[i for i,p in enumerate(pairs) if p is not None and all(p)]
    if not yes:return dict(H=None,later_reversals=[])
    h=yes[0]
    return dict(H=f'A{h}',later_reversals=[f'A{i}' for i in range(h+1,5) if pairs[i] is not None and not all(pairs[i])])


def multiplicity_interval(draws):
    return np.quantile(draws,[.00625,.99375],axis=0)
