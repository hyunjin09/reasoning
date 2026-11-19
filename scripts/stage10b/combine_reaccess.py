"""Preserve historical missingness and append explicitly versioned passive repair."""
from scripts.stage10b.common import ROOT,load,save,sha,now
from scripts.stage10b.analyze import table


def main():
    hp=ROOT/'audit/reaccess_historical.json';historical=load(hp)
    by={r['event_id']:r for r in historical['rows']};sources={str(hp):sha(hp)};repaired=[]
    decision=load(ROOT/'audit/passive_repair_decision.json')
    if decision['execute']:
        mp=ROOT/'audit/passive_repair_manifest.json';manifest=load(mp)
        complete=load(ROOT/'repair/complete.json');assert complete['manifest_sha256']==sha(mp)
        assert complete['trajectories']==manifest['trajectories'] and len(complete['trajectories'])<=32
        sources[str(mp)]=sha(mp)
        for tid in complete['trajectories']:
            rp=ROOT/f'repair/{tid}/complete.json';receipt=load(rp);sources[str(rp)]=sha(rp)
            assert receipt['manifest_sha256']==sha(mp) and receipt['new_generated_tokens']==0
            for r in receipt['rows']:
                assert r['event_id'] in by and by[r['event_id']]['measured_tokens']==0
                assert r['semantic_clean'] and r['trajectory_id']==tid
                assert sha(r['passive_path'])==r['passive_sha256']
                r=dict(r,historical_classification=by[r['event_id']]['classification'])
                by[r['event_id']]=r
                repaired.extend(dict(event_id=r['event_id'],trajectory_id=tid,**q,
                                     passive_sha256=r['passive_sha256']) for q in r['rows'])
        table(repaired,ROOT/'stage10b_passive_reinstrumentation.parquet')
    save(ROOT/'audit/reaccess_combined.json',dict(at=now(),rows=list(by.values()),semantic_sha256=historical['semantic_sha256'],
        source_sha256=sources,passive_repair_executed=decision['execute'],
        original_historical_evidence_preserved=True,new_generations=0,causal_outcomes_used=False))
    print('COMBINED',len(by),'events; passive repair',decision['execute'],flush=True)


if __name__=='__main__':main()
