"""Family-equal cross-scale estimates; null-safe integer paired bootstrap."""
from collections import Counter
from scripts.stage13b.protocol import bootstrap_units,primary_gate


def majority(values):
    if values.count(1)>=2:return True
    if values.count(0)>=2:return False
    return None


def effects(rows):
    indexed={};scales={};bounds={};sensitivity={};transitions={};absolute={}
    for r in rows:
        key=(r['scale'],r['condition']);indexed.setdefault(key,{})
        assert r['family_id'] not in indexed[key]
        assert len(r['I'])==len(r['T'])==3
        assert set(r['I']+r['T'])<={0,1,None}
        indexed[key][r['family_id']]=r
    complete={};units={}
    for (s,c),families in indexed.items():
        assert len(families)==48
        complete[s,c]={f for f,r in families.items() if None not in r['I']+r['T']}
        units[s,c]={f:sum(families[f]['T'])-sum(families[f]['I']) for f in sorted(complete[s,c])}
        estimate=bootstrap_units(list(units[s,c].values()));estimate['family_ids']=sorted(complete[s,c])
        scales.setdefault(s,{})[c]=estimate;key=s+'_'+c
        lower=sum(sum(x or 0 for x in r['T'])-sum(1 if x is None else x for x in r['I']) for r in families.values())
        upper=sum(sum(1 if x is None else x for x in r['T'])-sum(x or 0 for x in r['I']) for r in families.values())
        bounds[key]=dict(n=48,lower_pp=100*lower/144,upper_pp=100*upper/144,
            I_missing=sum(r['I'].count(None) for r in families.values()),T_missing=sum(r['T'].count(None) for r in families.values()))
        short=[f for f in sorted(complete[s,c]) if all(families[f]['T_before32k'])]
        sensitivity[key]=dict(bootstrap_units([units[s,c][f] for f in short]),family_ids=short)
        labels=[]
        for r in families.values():
            i,t=majority(r['I']),majority(r['T'])
            labels.append('UNRESOLVED' if i is None or t is None else 'BOTH_CORRECT' if i and t else 'THINKING_ONLY' if t else 'INSTRUCT_ONLY' if i else 'BOTH_WRONG')
        counts=Counter(labels);transitions[key]={k:counts[k] for k in ['BOTH_CORRECT','THINKING_ONLY','INSTRUCT_ONLY','BOTH_WRONG','UNRESOLVED']}
        n=len(complete[s,c]);resolved={m:[x for r in families.values() for x in r[m] if x is not None] for m in ['I','T']}
        absolute[key]=dict(complete_families=n,
            **{m+'_primary_accuracy':sum(sum(families[f][m]) for f in complete[s,c])/(3*n) if n else None for m in ['I','T']},
            **{m+'_all_resolved_accuracy':sum(resolved[m])/len(resolved[m]) if resolved[m] else None for m in ['I','T']},
            **{m+'_resolved_calls':len(resolved[m]) for m in ['I','T']},
            both_near_floor=sum(sum(families[f]['I'])<=1 and sum(families[f]['T'])<=1 for f in complete[s,c])/n if n else None,
            both_near_ceiling=sum(sum(families[f]['I'])>=2 and sum(families[f]['T'])>=2 for f in complete[s,c])/n if n else None,
            discordant=sum((sum(families[f]['I'])>=2)!=(sum(families[f]['T'])>=2) for f in complete[s,c])/n if n else None)
    attenuation={}
    for s in scales:
        if (s,'EQ') in complete and (s,'img') in complete:
            common=sorted(complete[s,'EQ'] & complete[s,'img'])
            attenuation[s]={f:units[s,'img'][f]-units[s,'EQ'][f] for f in common}
            scales[s]['A']=dict(bootstrap_units(list(attenuation[s].values())),family_ids=common)
    common=sorted(set(attenuation.get('2B',{})) & set(attenuation.get('8B',{})))
    interaction=dict(bootstrap_units([attenuation['2B'][f]-attenuation['8B'][f] for f in common]),family_ids=common)
    states=[];small=primary_gate(scales['2B']['EQ']) if '2B' in scales and 'EQ' in scales['2B'] else False
    if small:states.append('SMALL_VLM_POST_EVIDENCE_GAIN')
    if all(s in scales and 'EQ' in scales[s] for s in ['2B','4B','8B']):
        estimates=[scales[s]['EQ'] for s in ['2B','4B','8B']]
        if all(e['n'] and e['effect_pp']>0 for e in estimates) and estimates[0]['ci95_pp'][0]>0 and sum(e['ci95_pp'][0]>0 for e in estimates)>=2:
            states.append('POST_EVIDENCE_GAIN_ACROSS_SCALES')
    shift=interaction['n']>=36 and abs(interaction['effect_pp'])>=5 and (interaction['ci95_pp'][0]>0 or interaction['ci95_pp'][1]<0)
    if shift:states.append('SCALE_ROLE_SHIFT')
    if 'A' in scales.get('2B',{}):
        a=scales['2B']['A'];im=scales['2B']['img']
        if a['n'] and im['n'] and im['effect_pp']>0 and a['effect_pp']>=5 and a['ci95_pp'][0]>0:states.append('IMAGE_SIDE_SMALL_SCALE_SIGNAL')
    if not small and not shift:states.append('CROSS_SCALE_ROLE_UNRESOLVED')
    return dict(scales=scales,R_shift=interaction,missingness=bounds,sensitivity=sensitivity,
                majority_transitions=transitions,absolute=absolute,states=states)
