"""Pre-outcome image-family aliases retain same-item pairs but cluster inference."""
import numpy as np
from visual_reasoning.stage8b.block3a import replication


def replication_by_family(pairs):
    clustered=[dict(p,family_id=p['analysis_family_id']) for p in pairs]
    result=replication(clustered)
    result['items']=len({p['item_id'] for p in pairs})
    result['family_rule']='Direct image crosscheck aliases1707/1245; original source IDs retained in paired table'
    for metric,summary in result['metrics'].items():
        if 'median' not in summary:continue
        strata={}
        for category in sorted({p['category'] for p in clustered}):
            rows=[p for p in clustered if p['category']==category]
            families={p['family_id'] for p in rows}
            values=[np.median([p[metric] for p in rows if p['family_id']==f]) for f in sorted(families)]
            strata[category]=dict(families=len(families),median=float(np.median(values)))
        breadth=sum(v['families']>=2 and v['median']>0 for v in strata.values())>=2
        summary.update(categories=strata,breadth_pass=breadth,
            pass_gate=bool(summary['median']>0 and summary['ci95'][0]>0 and breadth))
    result['pass']=bool(result['yield_pass'] and result['items']>=16 and any(v['pass_gate'] for v in result['metrics'].values()))
    return result
