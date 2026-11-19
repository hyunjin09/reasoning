"""Review controlled claims without correctness filtering or membership edits."""
import argparse
import json
from scripts.stage6a.inventory import OUT


def main():
    p=argparse.ArgumentParser();p.add_argument('--cohort',choices=['C1','C2','C3'],required=True);p.add_argument('--batch',required=True);p.add_argument('--count',type=int,default=12)
    p.add_argument('--condition');a=p.parse_args()
    assert a.batch.isidentifier()
    if a.cohort=='C1':assert a.condition and a.condition!='intact', 'C1 intact membership uses its dedicated frozen review'
    previous=OUT/'traces/controlled_manual_reviews.jsonl'
    seen={r['event_id'] for r in map(json.loads,previous.read_text().splitlines())} if previous.exists() else set()
    rows=sorted([r for r in map(json.loads,(OUT/'traces/controlled_native_index.jsonl').read_text().splitlines()) if r['cohort']==a.cohort and r['event_id'] not in seen and (a.condition is None or r['condition']==a.condition)],key=lambda r:r['event_id'])[:a.count]
    packet=[]
    for r in rows:
        record={k:r.get(k) for k in ['event_id','base_id','cohort','condition','complete','prompt','answer','source_answer','target','other_sources','answers','demanded_sources','category','present','image_path','raw_decoded_response','generation_artifact','tokens_artifact']}
        packet.append(record)
        print('\n'+r['event_id']+' truth='+str(r['answer'])+' prompt='+r['prompt'])
        print(r['raw_decoded_response'])
    dest=OUT/f'review/{a.cohort.lower()}_{a.batch}.json';assert not dest.exists();dest.write_text(json.dumps(packet,indent=2)+'\n')


if __name__=='__main__':main()
