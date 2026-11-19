"""Prospectively fixed passive C5 screening; no causal inference."""
import numpy as np
from scripts.stage10b.protocol import qualifying_runs


def roi_indices(box,grid):
    if box is None:return []
    t,h,w=grid;assert t==1 and h>0 and w>0
    x0,y0,x1,y1=map(float,box);assert 0<=x0<x1<=1 and 0<=y0<y1<=1
    return [y*w+x for y in range(h) for x in range(w) if x0<=(x+.5)/w<x1 and y0<=(y+.5)/h<y1]


def reaccess(focus,scores,offsets,*,target,irrelevant,tau,observation_offset):
    x=np.asarray(focus,dtype=float);indices=np.asarray(offsets,dtype=int)
    assert x.ndim==2 and len(x)==len(indices) and len(set(indices))==len(indices)
    assert np.all((indices>=0)&(indices<32)) and np.all(np.diff(indices)>0)
    assert not(set(target)&set(irrelevant))
    complete=indices.tolist()==list(range(32)) and np.isfinite(x).all()
    base=dict(C5=False,lag=None,evidence_channel=None,coverage_complete=bool(complete),measured_tokens=len(x),rows=[])
    if not target or not irrelevant:return dict(base,classification='TARGET_AMBIGUOUS')
    assert max(target+irrelevant)<x.shape[1] and min(target+irrelevant)>=0
    mass=x.sum(1);target_mass=x[:,target].sum(1)/np.maximum(mass,1e-30)
    ratio=x[:,target].mean(1)/np.maximum(x[:,irrelevant].mean(1),1e-30)
    selective=np.isfinite(x).all(1)&(mass>0)&(target_mass>=.05)&(ratio>=1.5)
    score=np.asarray(scores,dtype=float) if scores is not None else np.full(len(x),np.nan)
    assert len(score)==len(x)
    detector=np.isfinite(score)&(score>tau)
    both=qualifying_runs(indices,selective&detector);routes=qualifying_runs(indices,selective)
    obs=observation_offset is not None and 0<=observation_offset<32
    candidates=[]
    if both:candidates.append((both[0],'detector_and_target_routing'))
    if routes and obs:candidates.append((routes[0],'routing_and_explicit_observation'))
    lag,channel=min(candidates) if candidates else (None,None)
    rows=[dict(offset=int(i),retrieval_score=float(s) if np.isfinite(s) else None,target_image_mass=float(m),
            target_control_mean_ratio=float(r),target_selective=bool(sel),detector_positive=bool(d))
          for i,s,m,r,sel,d in zip(indices,score,target_mass,ratio,selective,detector)]
    classification='CLEAN_REACCESS' if lag is not None else 'ROUTING_DATA_MISSING' if not complete else 'ATTENTION_ONLY' if detector.any() and not routes else 'NEW_DEMAND_NO_REACCESS'
    return dict(base,C5=lag is not None,lag=lag,evidence_channel=channel,classification=classification,rows=rows,
                target_positions=target,irrelevant_positions=irrelevant,explicit_observation_in_window=bool(obs),
                detector_available=bool(np.isfinite(score).any()),target_specific_run_onsets=routes)
