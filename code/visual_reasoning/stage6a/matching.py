"""Outcome-defined natural atlas matching on observed non-model-state covariates."""
import numpy as np
from scipy.optimize import linear_sum_assignment


def match_controls(cases,controls,cost):
    pairs=[];unmatched=[]
    for split in sorted({r['split'] for r in cases}):
        left=sorted([r for r in cases if r['split']==split],key=lambda r:r['base_id'])
        right=sorted([r for r in controls if r['split']==split],key=lambda r:r['base_id'])
        if not right:
            unmatched.extend(r['base_id'] for r in left);continue
        values=np.asarray([[cost(a,b) for b in right] for a in left],dtype=float)
        assert np.isfinite(values).all()
        ii,jj=linear_sum_assignment(values)
        used=set(ii.tolist())
        pairs.extend(dict(case_base_id=left[i]['base_id'],control_base_id=right[j]['base_id'],
            split=split,matching_cost=float(values[i,j])) for i,j in zip(ii,jj))
        unmatched.extend(row['base_id'] for i,row in enumerate(left) if i not in used)
    return pairs,unmatched
