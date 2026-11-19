"""Family-equal held-out counts with exact descriptive intervals."""
from scipy.stats import beta
from scripts.stage12xs.protocol import majority,support,decision


def exact(k,n):
    if not n:return dict(numerator=k,denominator=n,estimate=None,exact95=None)
    return dict(numerator=k,denominator=n,estimate=k/n,exact95=[0.0 if k==0 else float(beta.ppf(.025,k,n-k+1)),1.0 if k==n else float(beta.ppf(.975,k+1,n-k))])

def bounded_endpoint(values):
    n=len(values);k=values.count(True);unknown=values.count(None)
    return dict(exact=exact(k,n-unknown),frozen_denominator=n,unknown=unknown,
        missingness_bounds=[k/n,(k+unknown)/n] if n else None,
        note='Exact interval uses observed families only; bounds retain every frozen family. Unknown is never scored as failure.')

def infer_transfer(ids,run_rows):
    families=[]
    for i in ids:
        panels={a:[next(r['correct'] for r in run_rows if r['item_id']==i and r['arm']==a and r['replicate']==k) for k in range(5)] for a in ['RT_T','RT_I','Q_I','Q_T','SH_I']}
        families.append(dict(item_id=i,panels=panels,majority={a:majority(v) for a,v in panels.items()},
            production_support=support(panels),strict_production_support=support(panels,True)))
    endpoints={a:bounded_endpoint([r['majority'][a] for r in families]) for a in ['RT_T','RT_I','Q_I','Q_T','SH_I']}
    for key in ['production_support','strict_production_support']:
        endpoints[key]=bounded_endpoint([r[key] for r in families])
    return dict(n_selected=len(ids),families=families,endpoints=endpoints,
        decision=decision(len(ids),[r['majority']['RT_T'] for r in families],[r['production_support'] for r in families]),
        independent_unit='Conservative visual family; seeds are within-family stochastic repeats, not independent population samples.')
