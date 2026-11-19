"""Expose a fixed native prefix for source-demand review, without outcome filters."""
import argparse
import json
from collections import defaultdict
from scripts.stage6a.inventory import OUT


def main():
    p=argparse.ArgumentParser();p.add_argument('--start',type=int,required=True);p.add_argument('--count',type=int,default=2);p.add_argument('--remaining-strata',action='store_true');a=p.parse_args()
    scope=OUT/'config/c1_semantic_prefix_review_scope.json'
    if not scope.exists():scope.write_text(json.dumps(dict(
        stratum='All34MathVerse candidates in frozen construction order',
        span_scope='First20native reasoning spans, including the full prior prefix',
        selection='Fixed dataset and token-prefix scope; no correctness, attention, confidence or causal selection',
        labels='Current demanded/mentioned sources, explicit source-linked claims, unknown or no explicit demand',
        limitation='Prefix review is not exhaustive whole-trajectory annotation; all remaining spans retain conservative rules/UNRESOLVED'),indent=2)+'\n')
    order_name='c1_secondary_remaining_review_order' if a.remaining_strata else 'c1_secondary_source_review_order'
    order=[json.loads(s) for s in (OUT/f'cohort/{order_name}.jsonl').read_text().splitlines()]
    grouped=defaultdict(list)
    for span in map(json.loads,(OUT/'traces/controlled_reasoning_spans.jsonl').read_text().splitlines()):
        if span['cohort']=='C1' and span['condition']=='intact' and span['section']=='reasoning':grouped[span['base_id']].append(span)
    records=[]
    for row in order[a.start:a.start+a.count]:
        assert grouped[row['base_id']],row['base_id']
        spans=grouped[row['base_id']][:20]
        records.append(dict(base_id=row['base_id'],target=row['target'],spans=spans))
        print('\n'+row['base_id']+' T='+row['target']['entity']+' '+row['target']['value'])
        for i,s in enumerate(spans):print(str(i)+' '+s['span_id']+' '+repr(s['text']))
    stem='c1_semantic_prefix_remaining' if a.remaining_strata else 'c1_semantic_prefix'
    dest=OUT/f'review/{stem}_{a.start:03d}.json'
    assert not dest.exists();dest.write_text(json.dumps(records,indent=2)+'\n')


if __name__=='__main__':main()
