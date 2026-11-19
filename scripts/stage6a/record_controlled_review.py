"""Record manually reviewed final answers and source-linked exact native quotes."""
import argparse
import bisect
import json
from scripts.stage6a.inventory import OUT
from scripts.stage6a.prepare_candidates import write


def main():
    p=argparse.ArgumentParser();p.add_argument('--cohort',choices=['C1','C2','C3'],required=True);p.add_argument('--batch',required=True);a=p.parse_args();assert a.batch.isidentifier()
    packet=json.loads((OUT/f'review/{a.cohort.lower()}_{a.batch}.json').read_text())
    decisions=json.loads((OUT/f'review/{a.cohort.lower()}_{a.batch}_decisions.json').read_text())
    path=OUT/'traces/controlled_manual_reviews.jsonl';previous=[json.loads(s) for s in path.read_text().splitlines()] if path.exists() else []
    existing={r['event_id']:r for r in previous};added=[]
    for row in packet:
        eid=row['event_id']
        if eid not in decisions:continue
        if a.cohort=='C1':assert row['condition']!='intact', 'Preserve the dedicated intact membership review'
        if eid in existing:assert existing[eid]['review_packet']==f'review/{a.cohort.lower()}_{a.batch}.json', 'Conflicting review packet'
        decision=decisions[eid];raw=row['raw_decoded_response'];claims=[]
        tokens=[json.loads(s) for s in (OUT/row['tokens_artifact'].split('outputs/stage6a/')[-1]).read_text().splitlines()]
        offsets=[0]
        for token in tokens:offsets.append(offsets[-1]+len(token['decoded_token']))
        assert raw==''.join(t['decoded_token'] for t in tokens)
        for claim in decision['source_claims']:
            quote=claim['quote'];start=raw.index(quote);end=start+len(quote)
            assert end<=raw.find('</think>') if '</think>' in raw else True
            left=bisect.bisect_right(offsets,start)-1;right=bisect.bisect_left(offsets,end)
            claims.append(dict(**claim,char_start=start,char_end=end,token_start=left,token_end=right,
                exact_native_token_ids=[t['token_id'] for t in tokens[left:right]]))
        added.append(dict(event_id=eid,base_id=row['base_id'],cohort=row['cohort'],condition=row['condition'],
            **{**decision,'source_claims':claims},complete_native_trace=row['complete'],
            raw_generation_artifact=row['generation_artifact'],review_packet=f'review/{a.cohort.lower()}_{a.batch}.json',
            scope='Explicitly reviewed source-linked claims and final answer; other attributes/fields/reasoning are not certified.',
            attention_or_causal_data_used=False))
    replaced={r['event_id'] for r in added}
    write(path,[r for r in previous if r['event_id'] not in replaced]+added);print('Saved',len(added),'controlled native reviews')


if __name__=='__main__':main()
