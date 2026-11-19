"""Save explicitly reviewed intact claims with exact native token evidence."""
import argparse
import bisect
import json
from scripts.stage6a.inventory import OUT
from scripts.stage6a.prepare_candidates import write


def main():
    p=argparse.ArgumentParser();p.add_argument('--batch',required=True);a=p.parse_args();assert a.batch.isidentifier()
    packet={r['base_id']:r for r in json.loads((OUT/f'review/c1_native_{a.batch}.json').read_text())}
    decisions=json.loads((OUT/f'review/c1_native_{a.batch}_decisions.json').read_text())
    path=OUT/'c1_diagram_stress/intact_local_claim_review.jsonl'
    previous=[json.loads(s) for s in path.read_text().splitlines()] if path.exists() else []
    seen={r['base_id'] for r in previous};added=[]
    for key,decision in decisions.items():
        if key in seen:continue
        row=packet[key];assert decision['membership_status'] in ['eligible','ineligible','unresolved']
        generation_path=OUT/row['raw_generation_artifact'].split('outputs/stage6a/')[-1]
        generation=json.loads(generation_path.read_text());raw=generation['raw_decoded_response']
        evidence={}
        if decision['membership_status']=='eligible':
            assert row['complete']
            quote=decision.get('claim_quote') or row['target_value_highlights'][decision['highlight_index']]['text']
            assert quote in raw.split('</think>')[0] and decision['readout'] in quote
            start=raw.index(quote);end=start+len(quote)
            tokens=[json.loads(s) for s in (generation_path.parent/'tokens.jsonl').read_text().splitlines()]
            offsets=[0]
            for token in tokens:offsets.append(offsets[-1]+len(token['decoded_token']))
            left=bisect.bisect_right(offsets,start)-1;right=bisect.bisect_left(offsets,end)
            evidence=dict(claim_quote=quote,char_start=start,char_end=end,token_start=left,token_end=right,
                exact_native_token_ids=[t['token_id'] for t in tokens[left:right]],
                native_token_window_text=''.join(t['decoded_token'] for t in tokens[left:right]),
                full_prior_history_artifact=str(generation_path),temporal_history_status='Not assigned by local membership review')
        added.append(dict(base_id=key,event_id=row['event_id'],target=row['target'],intact_complete=row['complete'],
            **{**decision,**evidence},review_packet=f'review/c1_native_{a.batch}.json',
            membership_selected_by_correctness=False,attention_or_causal_data_used=False,
            review_scope='Local source/readout semantics and final answer; no claim of full per-span temporal annotation.'))
    path.parent.mkdir(exist_ok=True);write(path,previous+added)
    print('Saved',len(added),'explicit native local-claim reviews')


if __name__=='__main__':main()
