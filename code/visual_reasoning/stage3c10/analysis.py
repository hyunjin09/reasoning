"""Independent-base inference using inherited signed-rank, bootstrap and Holm."""
from visual_reasoning.stage3c8.analysis import inferential_summary, holm_adjust, robust_positive
from .protocol import PRIMARY, trigger_gate


def summarize_family(values, *, order=PRIMARY):
    result={name:{**inferential_summary(values.get(name,{})), 'values_by_base':values.get(name,{})} for name in order}
    adjusted=holm_adjust([result[name]['wilcoxon_p'] for name in order])
    for name,p in zip(order,adjusted):
        row=result[name];row['holm_p']=p
        row['robust_positive']=bool(robust_positive(row) and row['median'] is not None and row['median']>0)
    return result


def secondary(values, correction=1):
    result={**inferential_summary(values),'values_by_base':values}
    result['holm_p']=min(1.,result['wilcoxon_p']*correction)
    result['correction']=f'conservative Bonferroni x{correction}'
    result['robust_positive']=bool(robust_positive(result) and result['median'] is not None and result['median']>0)
    return result


def primary_gates(statistics):
    result=trigger_gate(statistics)
    result.update({'temporal_eligible':statistics['rds_T']['robust_positive'] or statistics['vsd_T']['robust_positive'],
                   'layers_eligible':result['passed']})
    return result


def k80_window(primary_r16, summaries):
    if not primary_r16['robust_positive'] or primary_r16['median']<=0:
        return {'k80':None,'reason':'R16 behavioral VSD effect not robust','monotonicity_assumed':False}
    threshold=.8*primary_r16['median']
    eligible=[int(k) for k,s in summaries.items() if s['median'] is not None and s['median']>=threshold and s['positive_fraction']>=.75]
    return {'k80':min(eligible) if eligible else None,'threshold':threshold,'monotonicity_assumed':False,
            'interpretation':'tested cumulative-window descriptor, not a unique information span'}
