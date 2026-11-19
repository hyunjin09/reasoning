"""Fixed source-review panel only; unknown facts remain explicitly unknown."""
import numpy as np
from scripts.stage14d1_pilot.common import P,load,save,now
from scripts.stage14d1_pilot.statistics import bootstrap_indices,interval


def main():
    selected=load(P/'protocol/offline_review_selection.json')['selected']
    arms=['G','Q','QI','QIA','QGL']
    records={r['item_id']:{x['arm']:x for x in load(P/'annotations/readouts'/f"{r['item_id']}.json")['records']} for r in selected}
    ix=bootstrap_indices([r['stratum'] for r in selected])
    metrics={
        'verified_correct_explicit_record':lambda r:r['source_fact_correct'] is True,
        'explicitly_wrong_record':lambda r:r['source_fact_correct'] is False,
        'new_correct_demand_answer':lambda r:r['source_fact_correct'] is True and r['new_visual_information'] is True and r['demand_answered'] is True,
    }
    out={}
    for name,fn in metrics.items():
        x=np.array([[float(fn(records[r['item_id']][a])) for a in arms] for r in selected])
        summaries={a:dict(count=int(x[:,j].sum()),denominator=24,rate=float(x[:,j].mean()),bootstrap_95ci=interval(x[ix,j].mean(axis=1))) for j,a in enumerate(arms)}
        contrasts={}
        for base,treatment in [('G','QI'),('Q','QI'),('QI','QGL'),('QIA','QGL')]:
            delta=x[:,arms.index(treatment)]-x[:,arms.index(base)]
            contrasts[treatment+'-'+base]=dict(difference=float(delta.mean()),bootstrap_95ci=interval(delta[ix].mean(axis=1)),families=24)
        out[name]=dict(arms=summaries,contrasts=contrasts)
    save(P/'analysis/readout_stats_v8.json',dict(at=now(),families=24,metrics=out,
        bootstrap=dict(draws=4000,seed=20261019,strata='frozen offline opportunity context: 12 global, 6 local, 6 local+global',unit='family'),
        interpretation='Rates are verified record yields per assigned sampled family, not accuracy with unknown facts imputed wrong. Correct text may be redundant, source-given, or produced without new image use. New-correct-demand metric is single-reviewer supporting evidence, not proof of acquisition mediation. Source-flagged and additional technical cases excluded.'))
    print('Frozen 24-family readout statistics saved; no solver answers loaded.')

if __name__=='__main__':main()
