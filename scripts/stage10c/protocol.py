"""Frozen coordinates, matched controls and independent paired contrasts."""
import numpy as np

def matched_windows(b):
 assert b>=25
 return [b-24,b],[b,b+24]

def selected_queries(prompt,start,length,intervals):
 # Query absolute p+i-1 predicts native generated token i. Prefill is intact.
 return [j for j in range(length) if start+j>=prompt and any(lo<=start+j-prompt+1<hi for lo,hi in intervals)]

def contrasts(y,nll):
 y=np.asarray(y,float);nll=np.asarray(nll,float)
 assert y.shape==nll.shape and y.ndim==2 and y.shape[1]==5
 return np.column_stack([y[:,1]-y[:,2],nll[:,2]-nll[:,1],y[:,4]-y[:,3],nll[:,3]-nll[:,4]])

def choose_control(target,preferred,grid,excluded):
 t,h,w=grid;assert t==1
 available=set(range(h*w))-set(target)-set(excluded)
 if len(available)<len(target):raise ValueError('Cannot match a disjoint control to target token count')
 seed=set(preferred)&available
 # Prefer original semantically irrelevant region. Without one use farthest
 # corner from target centroid; no attention/outcome is consulted.
 tx=np.mean([i%w for i in target]);ty=np.mean([i//w for i in target])
 if seed:cx=np.mean([i%w for i in seed]);cy=np.mean([i//w for i in seed])
 else:
  corner=max([0,w-1,(h-1)*w,h*w-1],key=lambda i:((i%w-tx)**2+(i//w-ty)**2,-i));cx,cy=corner%w,corner//w
 order=sorted(available,key=lambda i:(i not in seed,(i%w-cx)**2+(i//w-cy)**2,i))
 return sorted(order[:len(target)])
