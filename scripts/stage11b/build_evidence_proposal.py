"""Hide construction judgments before two independent sufficiency reviews."""
from scripts.stage11b.common import ROOT,load,save,sha,now

packet=ROOT/'packets/discovery_evidence_v2.json'
source=load(packet)['rows'];constructed={};reviews={}
for who in ['a','b']:
    p=ROOT/'annotations'/f'construction_{who}_v2.json';x=load(p)
    assert x['sealed'] and x['model_outcomes_opened'] is False
    assert x['packet_sha256']==sha(packet)
    reviews[who]=sha(p)
    for r in x['rows']:
        assert r['item_id'] not in constructed
        assert r['image_inspected']
        constructed[r['item_id']]=r
assert set(constructed)=={r['item_id'] for r in source}
proposals=[]
for original in source:
    r=constructed[original['item_id']]
    assert r['family_id']==original['family_id']
    facts=r['facts']
    assert len(facts)<=4
    assert len({f['fact_id'] for f in facts})==len(facts)
    for f in facts:assert f['text'].strip() and f['source_ref']
    proposals.append(dict(original,facts=facts))
save(ROOT/'packets/discovery_sufficiency.json',dict(at=now(),rows=proposals,construction_judgments_hidden=True,
    model_outcomes_opened=False,source_packet_sha256=sha(packet),construction_sha256=reviews))
save(ROOT/'audit/discovery_construction_key.json',dict(at=now(),rows=list(constructed.values()),review_sha256=reviews))
print('128 shared proposals; construction judgments hidden; no model outputs opened')
