"""Persist an explicit human/agent visual-semantic review packet; no selection."""
import argparse
from bisect import bisect_left,bisect_right
from decimal import Decimal
from scripts.stage4a.prepare_config import ROOT,OUT,read_json,read_jsonl,write_jsonl
from visual_reasoning.stage4a.cohort import equivalent_numeric_matches


def main():
    p=argparse.ArgumentParser();p.add_argument('packet');args=p.parse_args()
    packet=read_json(args.packet);existing=read_jsonl(OUT/'cohort/manual_annotations.jsonl')
    screen=read_jsonl(OUT/'cohort/prospective_screen_manifest.jsonl')
    raw=read_jsonl(OUT/'cohort/reused_native_outcomes.jsonl')
    raw+=[read_json(p) for p in (OUT/'prospective_generation/raw').glob('shard_*/examples/*/result.json')]
    by_id={r['example_id']:r for r in raw}
    for review in packet:
        base=str(review['base_problem_id']);assert base not in {r['base_problem_id'] for r in existing}
        source=next(r for r in screen if r['base_problem_id']==base and (not review.get('example_id') or r['example_id']==review['example_id']))
        outcome=by_id[source['example_id']];assert outcome['complete'] and not outcome['truncated']
        tokens=read_jsonl(ROOT/outcome['artifact_dir']/'tokens.jsonl');pieces=[t['decoded_token'] for t in tokens]
        starts=[];ends=[];cur=0
        for piece in pieces:starts.append(cur);cur+=len(piece);ends.append(cur)
        full=''.join(pieces);end=full.find('</think>');full=full[:end] if end>=0 else full
        facts={};events={}
        for x in ['A','B']:
            fact=review['facts'][x]
            facts[x]={**fact,'background_mode':'roi_bright_median','renderer':'preserve_crossing_strokes'}
        for event,x,pos,reason in zip(['A1','B','A2'],['A','B','A'],review['positions'],review['reasons']):
            matches=equivalent_numeric_matches(full,facts[x]['original_value'])
            match=next((m for m in matches if bisect_right(starts,m.start())-1==pos),None)
            assert match is not None, f'base={base} event={event}: no exact fact match at token {pos}'
            stop=bisect_left(ends,match.end())+1
            events[event]={'candidate_start_token':pos,'candidate_end_token':stop,'match_start':match.start(),'match_end':match.end(),
                           'text_span':match.group(),'context':full[max(0,match.start()-130):match.end()+160].replace('\n',' '),
                           'fact':x,'semantic_judgment':reason,'event_type':'grounded_fact_identification_or_use','current_query_zero_based':pos-1}
        assert min(review['positions'][1]-review['positions'][0],review['positions'][2]-review['positions'][1])>=12
        existing.append({k:source[k] for k in ['base_problem_id','example_id','screen_order','source_image','question']}|
                        {'artifact_dir':outcome['artifact_dir'],'facts':facts,'events':events,'review_note':review['note'],
                         'semantic_reviewed':True,'edits_reviewed':False,'token_map_validated':False,'retained':False,
                         'attention_used':False,'causal_scores_available':False})
    write_jsonl(OUT/'cohort/manual_annotations.jsonl',sorted(existing,key=lambda r:r['screen_order']))
    print(f'Appended{len(packet)} explicit review records; total{len(existing)} provisional annotations')


if __name__=='__main__':main()
