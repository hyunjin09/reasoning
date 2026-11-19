#!/usr/bin/env python3
"""Generate numeric-use proposals only; acceptance requires manual semantic review."""
import argparse,re
from bisect import bisect_left,bisect_right
from scripts.stage4a.prepare_config import ROOT,OUT,read_json,read_jsonl,write_json,write_jsonl
from visual_reasoning.stage4a.cohort import choose_event_triplet,equivalent_numeric_matches
from visual_reasoning.stage3c8.fresh import numeric_surface_matches,propose_counterfactual_numeric_value


def main():
    p=argparse.ArgumentParser();p.add_argument('--limit',type=int,default=800);a=p.parse_args()
    screen=read_jsonl(OUT/'cohort/prospective_screen_manifest.jsonl')[:a.limit]
    new={r['example_id']:r for r in [read_json(p) for p in (OUT/'prospective_generation/raw').glob('shard_*/examples/*/result.json')]}
    reused={r['example_id']:r for r in read_jsonl(OUT/'cohort/reused_native_outcomes.jsonl')}
    proposals=[];audit=[]
    for item in screen:
        outcome=new.get(item['example_id']) or reused.get(item['example_id'])
        if not outcome:audit.append({'example_id':item['example_id'],'screen_order':item['screen_order'],'reason':'not_generated'});continue
        basic={'example_id':item['example_id'],'base_problem_id':item['base_problem_id'],'screen_order':item['screen_order'],
               'complete':outcome['complete'],'correct':outcome['correct'],'status':outcome['status']}
        if not outcome['complete'] or outcome['truncated']:
            audit.append({**basic,'reason':'not_naturally_complete'});continue
        if len(item['candidate_facts'])<2:
            audit.append({**basic,'reason':'fewer_than_two_static_candidate_facts','manual_visual_supplement_possible':True});continue
        tokens=read_jsonl(ROOT/outcome['artifact_dir']/'tokens.jsonl');pieces=[str(r['decoded_token']) for r in tokens]
        full=''.join(pieces);bounds=[];cur=0
        for t,piece in enumerate(pieces):bounds.append((cur,cur+len(piece)));cur+=len(piece)
        # Only reasoning text; do not obtain A2 from the final-answer section.
        starts=[b[0] for b in bounds];ends=[b[1] for b in bounds]
        end=full.find('</think>');end=end if end>=0 else len(full)
        facts=[]
        for fi,f in enumerate(item['candidate_facts']):
            v=f['original_value'];matches=equivalent_numeric_matches(full[:end],v)
            mentions=[]
            for match in matches:
                start=bisect_right(starts,match.start())-1
                stop=bisect_left(ends,match.end())+1
                if start<8:continue
                mentions.append({'candidate_start_token':start,'candidate_end_token':stop,'match_start':match.start(),'match_end':match.end(),
                    'context':full[max(0,match.start()-130):min(end,match.end()+160)].replace('\n',' '),
                    'text_span':full[match.start():match.end()]})
            facts.append({**f,'fact_id':fi,'counterfactual_value_proposal':propose_counterfactual_numeric_value(v,f['context']),
                          'mentions':mentions,'proposals_are_not_semantic_labels':True})
        pairs=[]
        for x in facts:
            for y in facts:
                if x['fact_id']==y['fact_id']:continue
                triplet=choose_event_triplet([m['candidate_start_token'] for m in x['mentions']],[m['candidate_start_token'] for m in y['mentions']])
                if triplet:pairs.append({'A_fact_id':x['fact_id'],'B_fact_id':y['fact_id'],'proposed_event_indices':triplet})
        reason='manual_semantic_review_required' if pairs else 'no_numeric_ABA_proposal'
        audit.append({**basic,'reason':reason,'numeric_fact_count':len(facts),'numeric_ABA_pair_count':len(pairs)})
        if pairs:proposals.append({**basic,'source_image':item['source_image'],'question':item['question'],'text_dominant_question':item['text_dominant_question'],
            'artifact_dir':outcome['artifact_dir'],'facts':facts,'pairs':pairs,'attention_used':False,'causal_scores_available':False})
    write_jsonl(OUT/'cohort/numeric_proposals.jsonl',proposals);write_jsonl(OUT/'cohort/proposal_screen_audit.jsonl',audit)
    write_json(OUT/'cohort/proposal_accounting.json',{'screen_limit':a.limit,'native_outcomes':sum(r['reason']!='not_generated' for r in audit),
        'numeric_ABA_candidate_trajectories':len(proposals),'candidate_unique_bases':len({r['base_problem_id'] for r in proposals}),
        'missing_generation':sum(r['reason']=='not_generated' for r in audit),'manual_semantic_validation_pending':True})
    print(read_json(OUT/'cohort/proposal_accounting.json'))

if __name__=='__main__':main()
