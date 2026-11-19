"""Persist explicit masked lineage judgments and validate quoted native spans."""
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from visual_reasoning.stage8b.block1_data import digest, save

ROOT = Path('outputs/stage8b_block3b/v1')


def record(index, *, states, rationale, observations=(), mutation=None, recovery=None,
           full_remainder=False, downstream='DU', coverage_note='', next_subgoal=None):
    anchors = json.loads((ROOT/'annotations/anchors.json').read_text())['rows']
    anchor = anchors[index]; packet = json.loads(Path(anchor['packet']).read_text())
    assert states and set(states) <= set('PRCMSAU')
    assert downstream in ['D1','D2','D3','D4','D5','DU'] and len(rationale)>30
    assert mutation in [None,0,1] and recovery in [None,0,1]
    if mutation == 0 or recovery == 0:
        assert full_remainder, 'No negative incidence without full remainder review'
    if anchor['local'] != 'L+':
        assert mutation is None
    if anchor['local'] != 'L-':
        assert recovery is None
    text = packet['reasoning_text']; ends = np.asarray(packet['token_char_ends'])
    records = []
    for raw in observations:
        observation = dict(raw); quote=observation['quote']
        after=int(observation.pop('after_char',anchor['claim_char_end']))
        last=observation.pop('last',False)
        left=text.find(quote,after) if not last else text.rfind(quote)
        if left < 0:
            import re
            matches=list(re.finditer(re.escape(quote),text[after:],flags=re.I))
            if matches:
                match=matches[-1] if last else matches[0]
                left=after+match.start(); quote=text[left:after+match.end()]
                observation['quote']=quote
        assert left>=anchor['claim_char_end'],(index,quote)
        right=left+len(quote); assert text[left:right]==quote
        start=int(np.searchsorted(ends,left,side='right'))
        end=int(np.searchsorted(ends,right-1,side='right'))+1
        assert start>anchor['t0'] or end>anchor['t0']+1
        observation.update(char_start=left,char_end=right,start_token=start,end_token=end)
        records.append(observation)
    if mutation == 1:assert any(r['kind']=='mutation' for r in records)
    if recovery == 1:assert any(r['kind']=='correction' for r in records)
    if downstream != 'DU':assert any(r['kind']=='downstream_failure' for r in records)
    if next_subgoal is not None:assert anchor['t0']<next_subgoal<=anchor['reasoning_tokens']
    out=dict(at=datetime.now(timezone.utc).isoformat(),anchor_index=index,event_id=anchor['event_id'],
        item_id=str(anchor['item_id']),local=anchor['local'],states=states,rationale=rationale,
        observations=records,mutation=mutation,recovery=recovery,downstream=downstream,
        full_remainder_reviewed=full_remainder,coverage_note=coverage_note,
        next_subgoal_token=next_subgoal,packet_sha256=digest(anchor['packet']),
        reviewer='main agent; single annotator',outcome_and_features_masked=True,
        protocol_sha256=digest('plan/stage8b_block3b_execution_protocol_v1.md'))
    save(ROOT/f'annotations/reviews/{index:03d}.json',out)
    return dict(index=index,event_id=anchor['event_id'],observations=len(records))


def show(indices, *, tail_chars=1200, pattern=None, context=250, limit=12):
    """Display masked reference windows, never labels/metrics from other stages."""
    import re
    anchors=json.loads((ROOT/'annotations/anchors.json').read_text())['rows']
    for index in indices:
        a=anchors[index];p=json.loads(Path(a['packet']).read_text());text=p['reasoning_text']
        start=max(0,a['claim_char_start']-300);finish=a['claim_char_end']
        print('\nINDEX',index,'ITEM',a['item_id'],a['local'],'SOURCE',a['source_identity'],
              '\nQUESTION',p['question'],'\nANCHOR',a['quote'],'\nRATIONALE',a['rationale'],
              '\nCONTEXT',text[start:finish+600])
        if pattern:
            matches=[m for m in re.finditer(pattern,text,flags=re.I) if m.start()>=finish]
            print('REFERENCE MATCHES',len(matches),'showing',min(len(matches),limit))
            if len(matches)>limit:
                keep=sorted(set(np.linspace(0,len(matches)-1,limit).astype(int)));matches=[matches[i] for i in keep]
            for m in matches:
                print('AT CHAR',m.start(),text[max(finish,m.start()-context):min(len(text),m.end()+context)].replace('\n',' '))
        print('TAIL',text[max(finish,len(text)-tail_chars):])


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('indices',type=int,nargs='+')
    parser.add_argument('--pattern');parser.add_argument('--tail-chars',type=int,default=1200)
    parser.add_argument('--context',type=int,default=250);parser.add_argument('--limit',type=int,default=12)
    args=parser.parse_args();show(args.indices,tail_chars=args.tail_chars,pattern=args.pattern,
                               context=args.context,limit=args.limit)
