"""Resolve manually reviewed claims to exact native token boundaries on CPU."""
import argparse,re
from bisect import bisect_right
from transformers import AutoProcessor
from scripts.stage5a.prepare import ROOT,OUT,read_json,read_jsonl,write_json,write_jsonl,sha
from visual_reasoning.stage5a.annotation import exact_semantic_candidate,eligibility,temporal_annotation,cf_eligible,semantic_axes


def quote_matches(text,quote):
    pattern=r'\s+'.join(re.escape(p) for p in quote.split())
    return list(re.finditer(pattern,text))


def main():
    p=argparse.ArgumentParser();p.add_argument('--review',required=True);args=p.parse_args()
    config=read_json(OUT/'config/stage5a_config.json')
    processor=AutoProcessor.from_pretrained(config['model_checkpoint'],local_files_only=True)
    screen=read_jsonl(OUT/'cohort/prospective_screen_manifest.jsonl');by={r['base_problem_id']:r for r in reversed(screen)}
    records=read_json(args.review);result=[];failures=[]
    for record in records:
        b=record['base'];item=by[b];artifact=ROOT/item['native_reuse']['artifact_dir']
        tokens=read_jsonl(artifact/'tokens.jsonl');native=''.join(r['decoded_token'] for r in tokens)
        end=native.find('</think>');reasoning=native[:end] if end>=0 else native
        events=[]
        for n,review in enumerate(record['events']):
            print(f'resolving base={b} event={n+1} readout={review["readout"]!r}',flush=True)
            matches=quote_matches(reasoning,review['quote'])
            if not matches:
                failures.append({'base':b,'event':n,'reason':'quote_not_found','quote':review['quote']});continue
            match=matches[-1] if review.get('use_last') else matches[review.get('occurrence',0)]
            local=match.group();offset=local.find(review['readout'])
            if offset<0:raise ValueError('Readout missing from exact quote')
            char_start=match.start()+offset;char_end=char_start+len(review['readout'])
            fact=record['facts'][review['source']];actual=review['readout'];truth=review['truth']
            if actual==truth:
                alternative=review.get('alternative',fact['counterfactual'])
                candidate=exact_semantic_candidate(tokens=tokens,match_start=char_start,match_end=char_end,
                    counterfactual_value=alternative,tokenizer=processor.tokenizer)
                actual_ids=candidate['original_divergent_suffix_ids'];actual_direction='original'
            else:
                alternative=actual
                candidate=exact_semantic_candidate(tokens=tokens,match_start=char_start,match_end=char_end,
                    counterfactual_value=truth,tokenizer=processor.tokenizer)
                actual_ids=candidate['original_divergent_suffix_ids'];actual_direction='counterfactual'
                for tail in ('ids','text'):
                    left='original_divergent_suffix_'+tail;right='counterfactual_divergent_suffix_'+tail
                    candidate[left],candidate[right]=candidate[right],candidate[left]
                candidate['original_candidate_exact_generated_tokens']=False
            start=candidate['ed_generated_index']
            if start<8:
                failures.append({'base':b,'event':n,'reason':'fewer_than8_prior_queries'});continue
            source=review['source']
            temporal=temporal_annotation(review,reasoning[:char_start])
            joint_sources=record.get('joint_event_sources',{}).get(f'E{n+1}',[source])
            cf=cf_eligible(review,fact,alternative,joint_sources)
            events.append({**review,**candidate,'event_id':f'{b}_E{n+1}','source':source,'event':f'E{n+1}',
                'candidate_start_token':start,'current_query_zero_based':start-1,'claim_char_span':[match.start(),match.end()],
                'readout_char_span':[char_start,char_end],'actual_generated_candidate_ids':actual_ids,
                'actual_candidate_direction':actual_direction,'truth_candidate':truth,'alternative_candidate':alternative,
                'cf_semantics_eligible':cf,'readout_kind':review.get('readout_kind','numeric_fact'),
                **temporal,'joint_source_ids':joint_sources,
                'reasoning_progress':char_start/max(1,len(reasoning)),
                'progress_definition':'character offset within pre-think-terminator reasoning',
                **semantic_axes(review),'semantic_reviewed':True,
                'review_evidence':str(PathReview(args.review)),'attention_used':False,'causal_scores_available':False})
        positions=[e['candidate_start_token'] for e in events]
        if positions!=sorted(set(positions)):
            failures.append({'base':b,'reason':'event_order_or_duplicate','positions':positions});continue
        outcome=read_json(artifact/'result.json')
        natural_ok,atlas_ok=eligibility(record,outcome['complete'],events)
        result.append({**item,**record,'base_problem_id':b,'artifact_dir':str(artifact.relative_to(ROOT)),
            'events':events,'final_correct':outcome['status']=='correct','complete':outcome['complete'],
            'semantic_reviewed':True,'roi_reviewed':False,'attention_used':False,'causal_scores_available':False,
            'local_incorrect':any(e['local_correctness']=='INCORRECT' for e in events),
            'eligible':natural_ok,'atlas_eligible':atlas_ok})
    stem=PathReview(args.review).stem
    write_jsonl(OUT/f'annotations/provisional_{stem}.jsonl',result)
    write_json(OUT/f'cohort/review/{stem}_span_audit.json',{'passed':not failures,'bases':len(result),'events':sum(len(r['events']) for r in result),'failures':failures})
    print({'bases':len(result),'events':sum(len(r['events']) for r in result),'failures':failures})
    if failures:raise SystemExit(1)


def PathReview(value):
    from pathlib import Path
    return Path(value)


if __name__=='__main__':main()
