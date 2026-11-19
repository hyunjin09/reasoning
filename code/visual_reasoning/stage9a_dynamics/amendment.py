"""Prospective metadata-only allocation for the user compute amendment."""
import hashlib
from collections import defaultdict

SEED='stage9a_compute_amendment_v1:920260924'
CUTOFFS=(0,128,512,2048,None)


def rank(value):
    return hashlib.sha256((SEED+':'+str(value)).encode()).hexdigest()


def stratified_select(rows,n,fields=('subject','difficulty','answer_format'),prefix=''):
    """Hamilton quotas at each metadata level; hash ties and within-cell order."""
    assert 0<=n<=len(rows)
    if not fields:return sorted(rows,key=lambda r:rank(r['family_id']))[:n]
    groups=defaultdict(list)
    for row in rows:groups[str(row[fields[0]])].append(row)
    quotas={k:n*len(v)//len(rows) for k,v in groups.items()} if rows else {}
    remaining=n-sum(quotas.values())
    order=sorted(groups,key=lambda k:(-(n*len(groups[k])%len(rows)),rank(prefix+fields[0]+':'+k)))
    for k in order[:remaining]:quotas[k]+=1
    selected=[]
    for k in sorted(groups):
        selected.extend(stratified_select(groups[k],quotas[k],fields[1:],prefix+fields[0]+':'+k+'/'))
    return sorted(selected,key=lambda r:rank(r['family_id']))


def choose_demand(rows):
    eligible=[r for r in rows if r['valid_full_radius16']]
    later=[r for r in eligible if r['normalized_position']>.25]
    return min(later or eligible,key=lambda r:(r['demand_token'],r['event_id'])) if eligible else None


def matched_control(d,start,end,accepted_centers,precomputed=None):
    """Prefer an already frozen nearby window, else nearest admissible shift.

    Conservatively exclude every accepted event's ±32 neighborhood, keeping
    the legacy exclusion semantics. The selected demand itself is also excluded.
    """
    demand=(d-16,d+17);left=max(1,start);right=end-33
    def valid(a):return left<=a<=right and all(a+33<=c-32 or a>=c+33 for c in accepted_centers)
    if precomputed and precomputed[1]-precomputed[0]==33 and valid(precomputed[0]):
        if abs(precomputed[0]-demand[0])/max(1,end-start)<=.10:return tuple(precomputed),'frozen_nearby_control'
    choices=[a for a in range(left,right+1) if valid(a)]
    if not choices:return None,'no_admissible_control'
    chosen=min(choices,key=lambda a:(abs(a-demand[0]),rank(str(d)+':'+str(a))))
    return (chosen,chosen+33),'nearest_admissible_shift'
