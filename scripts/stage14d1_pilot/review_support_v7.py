"""Persist explicit reviewer judgments, never infer labels from solver outcomes."""
from scripts.stage14d1_pilot.common import P,load,save,sha,now

def annotate(records):
    for r in records:
        item=r.pop('item_id')
        paths=list((P/'data/source_packets').glob(f'main_v6_rank*/{item}.json'))
        assert len(paths)==1
        packet=paths[0];s=load(packet)
        aq=P/'annotations/query_only'/f'{item}.json';aa=P/'annotations/address_only'/f'{item}.json'
        assert not aq.exists() and not aa.exists()
        st=load(P/'raw'/packet.parent.name/'acquisition'/f'{item}.json')
        query=r.pop('query');address=r.pop('address')
        common=dict(at=now(),item_id=item,family_id=s['family_id'],packet=str(packet),packet_sha256=sha(packet),
                    original_image_inspected=True,final_answers_hidden=True,readouts_hidden=True,
                    annotator='main_AI',independent_review=False,prior_image_exposure=True)
        save(aq,dict(common,query_generation=st['query_generation'],query_generation_sha256=sha(st['query_generation']),**query))
        save(aa,dict(common,**address))

def packet_batch(ids):
    import json
    for item in ids:
        p=next((P/'data/source_packets').glob(f'main_v6_rank*/{item}.json'));d=load(p)
        print('\nITEM',item)
        print(json.dumps({k:d[k] for k in ('question','prefix','raw_query','query_valid','address')},ensure_ascii=False))

def readout_batch(ids):
    import json
    for item in ids:
        p=next((P/'raw').glob(f'main_v6_rank*/acquisition/{item}.json'))
        print(item,json.dumps(load(p)['readouts'],ensure_ascii=False))

def annotate_readouts(item, judgments, selection='Frozen 24-family source-stratified hash sample', final_answers_hidden=True):
    """Store supplied judgments; absent helper calls are transport facts only."""
    p=next((P/'raw').glob(f'main_v6_rank*/acquisition/{item}.json'));s=load(p)
    records=[]
    for arm, r in s['readouts'].items():
        if r['value'] is None:
            assert arm not in judgments
            j=dict(status='not_emitted',source_fact_correct=None,demand_answered=None,
                   new_visual_information=None,note='No helper readout emitted under the frozen NONE/invalid-query fallback. Not an observed incorrect visual fact.')
        else:
            j=judgments.pop(arm)
        records.append(dict(arm=arm,**j,readout=r['value'],generation_path=r['generation_path'],
                            alias_of=r['alias_of'],generation_sha256=sha(r['generation_path']) if r['generation_path'] else None))
    assert not judgments
    save(P/'annotations/readouts'/f'{item}.json',dict(at=now(),item_id=item,family_id=s['family_id'],
        records=records,selection=selection,
        original_image_inspected=True,final_answers_hidden=final_answers_hidden,annotator='main_AI',
        independent_review=False,prior_image_exposure=True))
