"""Family-level pilot endpoints with explicit undefined denominators."""
import math
import numpy as np

def endpoints(rows):
    assert rows
    e=np.array([r['e'] for r in rows],dtype=bool)
    d=np.array([r['d'] for r in rows],dtype=bool)
    c=np.array([r['c'] for r in rows],dtype=bool)
    available=e&~d;unavailable=~e&~d
    a=float(c[available].mean()) if available.any() else None
    u=float(c[unavailable].mean()) if unavailable.any() else None
    return dict(n=len(rows),E_plus=int(e.sum()),D_plus=int(d.sum()),C_plus=int(c.sum()),
        L=int(available.sum()),rescued=int((available&c).sum()),
        F1=int(unavailable.sum()),F2=int(available.sum()),F3=int((available&c).sum()),F4=int((available&~c).sum()),
        unavailable_rescued=int((unavailable&c).sum()),P1=float(e.mean()),P2=float(available.mean()),
        R_avail=a,R_unavail=u,delta=a-u if a is not None and u is not None else None)

def wilson(k,n):
    z=1.959963984540054;p=k/n;den=1+z*z/n
    center=(p+z*z/(2*n))/den
    radius=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return [max(0.,center-radius),min(1.,center+radius)]

def estimate(rows,seed,draws=4000):
    point=endpoints(rows);rng=np.random.default_rng(seed)
    samples={k:[] for k in ['R_avail','R_unavail','delta']}
    for _ in range(draws):
        p=endpoints([rows[i] for i in rng.integers(0,len(rows),len(rows))])
        for k in samples:
            if p[k] is not None:samples[k].append(p[k])
    intervals={k:dict(ci95=np.percentile(v,[2.5,97.5]).tolist() if v and point[k] is not None else None,
        defined_draws=len(v),undefined_draws=draws-len(v)) for k,v in samples.items()}
    return dict(point=point,P1_wilson95=wilson(point['E_plus'],point['n']),
        P2_wilson95=wilson(point['L'],point['n']),bootstrap=dict(seed=seed,draws=draws,
        unit='one whole conservative problem/image family',intervals=intervals))
