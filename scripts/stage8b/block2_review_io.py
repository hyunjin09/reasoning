"""Store explicit main-agent judgments with validated native quote/ROI provenance."""
import json,re
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
from visual_reasoning.stage8b.block1_data import digest,save
ROOT=Path('outputs/stage8b_block2/v1')


def record(item,judgments):
    packet_path=ROOT/'annotations/packets'/f'{item}.json'
    packet=json.loads(packet_path.read_text())
    assert len(judgments)==len(packet['events'])
    tokens=[json.loads(x) for x in Path(packet['token_file']).read_text().splitlines()]
    assert digest(packet['token_file'])==packet['token_sha256']
    pieces=[t['decoded_token'] for t in tokens];ends=np.cumsum([len(s) for s in pieces]);starts=np.r_[0,ends[:-1]];text=''.join(pieces)
    records=[]
    for event,j in zip(packet['events'],judgments):
        assert j['semantic'] in ['T','M','U'] and len(j['rationale'])>20
        row=dict(event,**j,item_id=item,family_id=packet['family_id'])
        if j['semantic']=='T':
            assert j['local'] in ['L+','L-','L?'] and j['source_image_reviewed']
            assert j['prior_context_check'] and j['source_identity']
            quote=j['quote'];readout=j.get('readout',quote);assert quote.count(readout)==1
            a=starts[event['association_start']];b=ends[event['association_end']-1]
            matches=[m for m in re.finditer(re.escape(quote),text) if a<=m.start()<b]
            assert len(matches)==1,(item,event['event_id'],quote,len(matches))
            left=matches[0].start()+quote.index(readout);right=left+len(readout)
            chosen=np.flatnonzero((starts<right)&(ends>left));assert len(chosen) and chosen[0]>0
            row.update(claim_char_start=int(left),claim_char_end=int(right),claim_start_token=int(chosen[0]),claim_end_token=int(chosen[-1]+1),predicting_generated_query=int(chosen[0]-1),quoted_native_text=text[left:right])
            for source in j.get('sources',[]):
                x0,y0,x1,y1=source['roi'];w,h=packet['image_size'];assert 0<=x0<x1<=w and 0<=y0<y1<=h
            row['source_localizable']=any(s['role']=='T' for s in j.get('sources',[]))
        else:
            assert j.get('local') is None
            row.update(local=None,source_localizable=False,sources=[],claim_start_token=None,claim_end_token=None)
        records.append(row)
    save(ROOT/'annotations/reviews'/f'{item}.json',dict(at=datetime.now(timezone.utc).isoformat(),item_id=item,reviewer='main agent; single annotator',packet_sha256=digest(packet_path),packet_masking='feature values/final labels omitted; prior project context known',image_sha256=packet['image_sha256'],protocol_sha256=digest('plan/stage8b_block2_execution_protocol_v1.md'),events=records))
    return len(records)


def show(start,count):
    f=json.loads((ROOT/'audit/preparation_freeze.json').read_text());items=list(dict.fromkeys(e['item_id'] for e in f['events']))
    for i,item in list(enumerate(items))[start:start+count]:
        p=json.loads((ROOT/'annotations/packets'/f'{item}.json').read_text())
        tokens=[json.loads(s)['decoded_token'] for s in Path(p['token_file']).read_text().splitlines()]
        print(f'ITEM {i}: {item} IMAGE {p["image"]} SIZE {p["image_size"]}\nQUESTION {p["question"]}')
        for e in p['events']:
            s,h=e['start_token'],e['end_token']+1
            print(f'  EVENT {e["episode_index"]} [{s}:{h}]\nBEFORE:'+''.join(tokens[max(0,s-96):s])+'\nEPISODE:'+''.join(tokens[s:h])+'\nAFTER:'+''.join(tokens[h:min(p['reasoning_tokens'],h+128)])+'\n')


if __name__=='__main__':
    import sys
    show(int(sys.argv[1]),int(sys.argv[2]))
