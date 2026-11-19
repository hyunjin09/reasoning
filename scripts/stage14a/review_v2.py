"""User-clarified atom counting. Original v1 review code/receipts stay immutable."""
import argparse
import json
from scripts.stage14a.common import ROOT, load, save, sha, now
from scripts.stage14a.review import validate as validate_v1, rendering

def validate(source,receipt):
    validate_v1(source,receipt)
    if receipt['decision']=='EXCLUDE':return
    assert len(receipt['atom_metadata'])==len(receipt['e_star_atoms'])
    for a in receipt['atom_metadata']:
        assert a['atom_type'] in ['scalar_relation','structured_layout']
        if a['atom_type']=='structured_layout':
            assert isinstance(a['structured_subfact_count'],int) and a['structured_subfact_count']>0
            assert a['size_unit'].strip() and a['coherent_source_object'].strip()
            assert a['minimality_note'].strip()
        else:assert a.get('structured_subfact_count') is None

def commit(path):
    order=load(ROOT/'stage14a_mathvision_candidate_order.json')['rows']
    by={r['item_id']:r for r in load(ROOT/'audit/mathvision_census_source_snapshot.json')['rows']}
    previous=[load(p) for p in sorted((ROOT/'audit/reviews/mathvision_v2').glob('*.json'))]
    rows=load(path);accepted=sum(r['decision']=='ACCEPT' for r in previous)
    for i,r in enumerate(rows,len(previous)):
        assert accepted<1000
        assert r['item_id']==order[i]['item_id']
        validate(by[r['item_id']],r)
        accepted+=r['decision']=='ACCEPT'
    # Validate the complete batch before any write.
    for i,r in enumerate(rows,len(previous)):
        r=dict(r,rank=i+1,family_id=order[i]['family_id'],at=now(),reviewer='main agent',
               model_outcomes_used=False,receipt_version=2,original_receipt_sha256=sha(path),
               amendment='audit/atom_count_user_amendment_v2.json')
        if r['decision']=='ACCEPT':r['equal_evidence_rendering']=rendering(by[r['item_id']],r['e_star_atoms'])
        save(ROOT/'audit/reviews/mathvision_v2'/f'{i+1:04d}_{r["item_id"]}.json',r)
        with (ROOT/'audit/eligibility_log_v2.jsonl').open('a') as f:f.write(json.dumps(r,ensure_ascii=False)+'\n')
    print('V2_SCREENED',len(previous)+len(rows),'FINAL_ACCEPTED',accepted)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--path',required=True);a=p.parse_args();commit(a.path)
