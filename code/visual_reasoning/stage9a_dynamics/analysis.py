"""Frozen family-equal necessity estimands, independent of plotting/scoring."""
from collections import defaultdict
import numpy as np
from visual_reasoning.stage9a.statistics import paired, mean_interval

PRIMARY = {'P1_512':'cutoff512_damage', 'P1_2048':'cutoff2048_damage',
           'P2':'late_damage', 'P3':'demand_minus_control'}


def family_metrics(rows):
    groups=defaultdict(dict)
    for r in rows:
        key=(r['family_id'],r['arm']);name=r['condition_id']
        if name in groups[key]:raise ValueError(f'Duplicate family/arm/condition: {key}:{name}')
        groups[key][name]=r
    output=[]
    for (family,arm),conditions in sorted(groups.items()):
        baseline=conditions['cutoff_full']['accuracy_no_credit']
        metrics={'baseline_accuracy':baseline}
        def damage(name):
            return baseline-conditions[name]['accuracy_no_credit'] if name in conditions else None
        for cutoff in (0,128,512,2048):metrics[f'cutoff{cutoff}_damage']=damage(f'cutoff_{cutoff}')
        for k in range(5):metrics[f'local{k}_damage']=damage(f'local20_{k}')
        late=[metrics[f'local{k}_damage'] for k in (3,4)]
        metrics['late_damage']=float(np.mean(late)) if all(x is not None for x in late) else None
        demand={r['role']:r for r in conditions.values() if r['assay']=='demand'}
        metrics.update(demand_damage=None,control_damage=None,demand_minus_control=None)
        if set(demand)=={'demand','control'}:
            metrics['demand_damage']=baseline-demand['demand']['accuracy_no_credit']
            metrics['control_damage']=baseline-demand['control']['accuracy_no_credit']
            metrics['demand_minus_control']=metrics['demand_damage']-metrics['control_damage']
        output.append(dict(family_id=family,arm=arm,primary=metrics))
    return output


def contrast(rows,key,*,left='thinking',right='instruct_cot',confidence=.9875,allowed=None):
    out=paired(rows,key,left=left,right=right,confidence=confidence,allowed=allowed)
    by=defaultdict(dict)
    for r in rows:
        if r['family_id'] in out['paired_families']:by[r['family_id']][r['arm']]=r['primary'][key]
    values=[r[left]-r[right] for r in by.values()]
    out['family_directions']={name:sum(test(x) for x in values) for name,test in
                             [('positive',lambda x:x>0),('negative',lambda x:x<0),('tie',lambda x:x==0)]}
    out['effect_unit']='accuracy fraction; multiply by100 for percentage points'
    return out


def descriptive(rows,arm,key,allowed=None):
    return mean_interval([r['primary'][key] for r in rows if r['arm']==arm and
                          (allowed is None or r['family_id'] in allowed)],confidence=.95)
