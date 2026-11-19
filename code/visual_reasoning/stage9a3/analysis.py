"""Literal scoring and the prospectively defined image-level calibration gate."""
import re
from collections import defaultdict
import numpy as np
from .dataset import SEED


def extract_option(text):
    matches=re.findall(r'\{\s*([A-E])\s*\}',text)
    return matches[-1] if matches else None


def image_surface(rows):
    images=sorted({r['image_id'] for r in rows});policies=sorted({r['policy'] for r in rows})
    groups=defaultdict(list)
    for r in rows:groups[r['image_id'],r['policy']].append(float(r['correct']))
    assert all(len(groups[i,p])==2 for i in images for p in policies),'Every image has two queries in every cell'
    return images,policies,np.array([[np.mean(groups[i,p]) for p in policies] for i in images])


def bootstrap(values):
    rng=np.random.default_rng(SEED)
    return values[rng.integers(0,len(values),size=(4000,len(values)))].mean(axis=1)


def tie(meta,policy):
    fraction,token=meta[policy]
    return (float('inf') if token is None else token,fraction,policy)


def calibration(policies,values,meta,median_length):
    full=next(i for i,p in enumerate(policies) if meta[p]==(1,None))
    zero=next(i for i,p in enumerate(policies) if meta[p]==(0,0))
    means=values.mean(axis=0);damage=means[full]-means
    draws=bootstrap(values);d=draws[:,full,None]-draws;ci=np.quantile(d,[.025,.975],axis=0)
    clear=bool(damage[zero]>=.1 and ci[0,zero]>0)
    material=[i for i,p in enumerate(policies) if i!=full and
              (meta[p][0]<=.75 or (meta[p][1] is not None and meta[p][1]<median_length))]
    passing=sorted([i for i in material if damage[i]<=.05+1e-12],key=lambda i:tie(meta,policies[i]))
    chosen=passing[0] if passing else None
    stability=float(np.mean((d[:,zero]>0)&(d[:,chosen]<=.05+1e-12))) if chosen is not None else 0.
    passed=bool(clear and chosen is not None and stability>=.9)
    selected_counts=defaultdict(int)
    ordered=sorted(material,key=lambda i:tie(meta,policies[i]))
    for draw in d:
        selected=next((policies[i] for i in ordered if draw[i]<=.05+1e-12),None)
        selected_counts[selected or 'none']+=1
    reserve=bool(not passed and clear and any(damage[i]<=.1+1e-12 and ci[0,i]<=.05<=ci[1,i] for i in material))
    return dict(pass_=passed,**{'pass':passed},n_images=len(values),full_accuracy=float(means[full]),
        clear_restriction_damage=clear,zero_policy=policies[zero],selected_policy=policies[chosen] if chosen is not None else None,
        selected_fraction=meta[policies[chosen]][0] if chosen is not None else None,
        selected_token_cutoff=meta[policies[chosen]][1] if chosen is not None else None,
        bootstrap_joint_stability=stability,bootstrap_selection_counts=dict(selected_counts),bootstrap_draws=4000,seed=SEED,
        reserve_eligible=reserve,median_full_length=float(median_length),
        surface={p:dict(accuracy=float(means[i]),damage=float(damage[i]),ci95=ci[:,i].tolist(),
                        preservation_probability=float(np.mean(d[:,i]<=.05+1e-12))) for i,p in enumerate(policies)},
        gate_definition='Zero-access damage>=10pp with95% lower>0; material finite damage<=5pp;>=90% paired draws retain positive zero-access damage and selected damage<=5pp. Technical/baseline gates required separately.')
