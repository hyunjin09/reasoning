"""Immutable local-claim review packets; a correct target is never eligibility."""
import argparse
import json
import re
from scripts.stage6a.inventory import OUT
from visual_reasoning.stage6a.readouts import readout_matches


def main():
    p=argparse.ArgumentParser();p.add_argument('--batch',required=True);p.add_argument('--count',type=int,default=16);a=p.parse_args()
    assert a.batch.isidentifier()
    index=[json.loads(s) for s in (OUT/'traces/controlled_native_index.jsonl').read_text().splitlines()]
    review_path=OUT/'c1_diagram_stress/intact_local_claim_review.jsonl'
    reviewed={r['base_id'] for r in map(json.loads,review_path.read_text().splitlines())} if review_path.exists() else set()
    rows=sorted([r for r in index if r['cohort']=='C1' and r['condition']=='intact' and r['base_id'] not in reviewed],key=lambda r:r['base_id'])[:a.count]
    packet=[]
    for row in rows:
        raw=row['raw_decoded_response'];body=raw.split('</think>')[0]
        paragraphs=[m for m in re.finditer(r'[^\n]+',body) if m.group().strip()]
        # Ground truth highlights assist review, but every trace is included;
        # missing/mismatching values trigger full-trace review, never exclusion.
        highlighted=[dict(text=m.group(),char_start=m.start(),char_end=m.end()) for m in paragraphs if readout_matches(m.group(),row['target']['value'])]
        packet.append(dict(event_id=row['event_id'],base_id=row['base_id'],target=row['target'],answer=row['answer'],
            complete=row['complete'],question=row['question'],raw_generation_artifact=row['generation_artifact'],
            initial_context=body[:2000],target_value_highlights=highlighted[:5],
            final_context=raw.split('</think>')[-1][-2000:] if '</think>' in raw else None,
            rule='Review the semantic link between T and an asserted local claim; correct, wrong and later-corrected claims all eligible. Read full raw trace when highlighted context is insufficient.'))
    dest=OUT/f'review/c1_native_{a.batch}.json';assert not dest.exists();dest.write_text(json.dumps(packet,indent=2)+'\n')
    for row in packet:
        print('\n'+row['base_id']+' '+json.dumps(row['target'])+' complete='+str(row['complete']))
        for h in row['target_value_highlights'][:3]:print(repr(h['text']))
        if not row['target_value_highlights']:print('FULL TRACE REVIEW REQUIRED: '+row['raw_generation_artifact'])
        print('FINAL_TAIL',repr((row['final_context'] or '')[-350:]))
    print(dest)


if __name__=='__main__':main()
