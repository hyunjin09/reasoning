"""Compile exact native token readouts from manually reviewed semantic claims.

Snapshots are preparatory; --freeze requires every native trace in the split to
have a completed review. No scores or hidden-state artifacts are read.
"""
import argparse
import hashlib
from decimal import Decimal, InvalidOperation
from transformers import AutoTokenizer
from scripts.stage7a.common import ROOT, OUT, read_json, read_jsonl, write_json, write_jsonl, sha
from scripts.stage7a.annotation_helpers import normalized_value
from visual_reasoning.stage6b.protocol import candidate_event


def surface_value(value, actual):
    if normalized_value(value)==normalized_value(actual): return actual
    if value.lower() in ('yes','no') and actual.lower() in ('yes','no'):
        return value.upper() if actual.isupper() else (value.capitalize() if actual.istitle() else value.lower())
    try:
        number=Decimal(value.replace(',',''))
        if ',' in actual:
            places=max(0,-number.as_tuple().exponent)
            return format(number,f',.{places}f')
    except InvalidOperation: pass
    return value


def compile_claim(row, review, claim, index, native, tokenizer):
    tokens=read_jsonl(native/'tokens.jsonl'); raw=''.join(t['decoded_token'] for t in tokens)
    a,b=claim['readout_char_start'],claim['readout_char_end']
    assert raw[a:b]==claim['readout']
    physical=claim['source_id']; other='X' if physical=='T' else 'T'
    claim={**claim,'wrong_claim_matches_alternative':bool(row['fields'] and
           normalized_value(claim['readout'])==normalized_value(row['fields'][other]['value']))}
    truth=claim['ground_truth']; actual=claim['readout']
    # Same-source pre-reviewed CF preserves the quantity's semantic type. The
    # alternative field's original content remains an independent named readout.
    foil=row['fields'][physical]['counterfactual'] if row['fields'] else ('no' if row['present'] else 'yes')
    binding=claim.get('readout_type')=='B'
    correct=claim['correct_readout'] if binding else surface_value(truth,actual)
    foil=claim['foil_readout'] if binding else surface_value(foil,actual)
    event=candidate_event(tokens,a,b,correct,foil,tokenizer)
    # All named candidates share the exact native byte-carrying anchor/history.
    left=len(event['history_before_ed_text'])
    right=left+len(event['native_claim_suffix_text'])
    named={'correct':event['original_divergent_suffix_ids'],'foil':event['counterfactual_divergent_suffix_ids'],'native':event['native_claim_suffix_ids']}
    semantic={}
    for label,source in [('target_semantic',physical),('alternative_semantic',other),('alternative_original',other)]:
        if binding or source not in row['fields']:continue
        value=surface_value(row['fields'][source]['value' if label=='alternative_original' else 'counterfactual'],actual)
        text=raw[left:a]+value+raw[b:right]
        ids=tokenizer.encode(text,add_special_tokens=False)
        assert tokenizer.decode(ids,skip_special_tokens=False,clean_up_tokenization_spaces=False)==text
        named[label]=ids;semantic[label]=value
    event.update(candidate_ids=named,semantic_alternatives=semantic,readout_char_start=a,readout_char_end=b)
    meta=read_json(native/'input.json');visual=meta['visual_token_indices']
    groups={}
    if visual:
        for role,source in [('T',physical),('X',other),('I','I')]:
            # The frozen I footprint was matched to physical T only. A demand
            # switch to physical X does not silently rematch that control.
            if role=='I' and physical!='T':continue
            local=row['local_source_groups'].get(source,[])
            if local: groups[role]=[visual[j] for j in local]
        groups['G']=visual
    w2=[s for s in ['T','X','I','G'] if s in groups]
    sensitivity=(row['split']=='discovery' or int(hashlib.sha256(row['base_id'].encode()).hexdigest(),16)%3==0)
    w8=[s for s in ['T','X'] if s in groups] if sensitivity else []
    aliases={}
    if claim.get('previous_source')==other:aliases['P']='X'
    # No-image/unrelated source-semantic variants are not the same visual source.
    cf_sources=[s for s in [physical,other] if s in row['fields']] if row['condition'] not in ['no_image','unrelated'] else []
    if row['condition']=='mask':cf_sources=[s for s in cf_sources if s!='T']
    if binding:cf_sources=[]
    fixed_controls=[]
    if claim['kind'] in ['primary','extra_error'] and row['condition'] in ['intact','strong','mask','unrelated','no_image']:
        fixed_controls=[s for s in ['intact','mask','unrelated','no_image'] if s!=row['condition']]
    return dict(id=row['event_id']+f'__e{index:02d}',event_id=row['event_id'],base_id=row['base_id'],split=row['split'],
        cohort=row['cohort'],dataset=row['dataset'],group_id=row['group_id'],template_family=row['template_family'],
        condition=row['condition'],row=row,event=event,reviewed_claim=claim,downstream_review=review['downstream'],
        source_groups=groups,source_aliases=aliases,physical_demanded_source=physical,physical_alternative_source=other,
        irrelevant_control_valid_for_current_demand='I' in groups,
        source_separation_valid=row['source_separation_valid'],w2_sources=w2,w8_sources=w8,
        cf_physical_sources=cf_sources,fixed_prefix_controls=fixed_controls,
        native_input_path=str(native/'input.json'),native_generation_path=str(native/'generation.json'),
        native_tokens_path=str(native/'tokens.jsonl'),review_path=str(OUT/'annotations/native_reviews'/(row['event_id']+'.json')),
        review_sha256=sha(OUT/'annotations/native_reviews'/(row['event_id']+'.json')),
        native_input_sha256=sha(native/'input.json'),native_generation_sha256=sha(native/'generation.json'),
        native_tokens_sha256=sha(native/'tokens.jsonl'),readout_type=claim.get('readout_type','V'),
        roles=dict(demanded='T',alternative='X' if 'X' in groups else None,previous='X' if aliases else None),
        selection_used_causal_or_passive_scores=False)


def main():
    p=argparse.ArgumentParser();p.add_argument('--split',required=True,choices=['discovery','confirmation']);p.add_argument('--freeze',action='store_true');args=p.parse_args()
    rows=[r for r in read_jsonl(OUT/'cohort/native_manifest.jsonl') if r['split']==args.split]
    tokenizer=AutoTokenizer.from_pretrained(read_json(OUT/'config/stage7a_config.json')['model_checkpoint'],local_files_only=True)
    events=[];missing=[];failures=[];reviews=[]
    for row in rows:
        path=OUT/'annotations/native_reviews'/(row['event_id']+'.json')
        if not path.exists():missing.append(row['event_id']);continue
        review=read_json(path);native=OUT/'native/native_01/examples'/row['event_id']
        assert review['generation_sha256']==sha(native/'generation.json') and review['tokens_sha256']==sha(native/'tokens.jsonl')
        mechanical_exclusion=(review.get('native_generation_complete') is False and not review['claims'] and review['behavior']=='incomplete_generation')
        assert (review['full_native_text_reviewed'] or mechanical_exclusion) and not review['causal_or_passive_scores_used'];reviews.append(review)
        for i,claim in enumerate(review['claims']):
            try:events.append(compile_claim(row,review,claim,i,native,tokenizer))
            except (ValueError,RuntimeError) as error:failures.append(dict(event_id=row['event_id'],claim_index=i,reason=str(error)))
        binding_path=OUT/'annotations/binding_reviews'/(row['event_id']+'.json')
        if binding_path.exists():
            binding=read_json(binding_path)
            assert binding['generation_sha256']==sha(native/'generation.json')
            if not binding.get('eligible',True):continue
            try:
                compiled=compile_claim(row,review,binding['claim'],len(review['claims']),native,tokenizer)
                compiled.update(binding_review_path=str(binding_path),binding_review_sha256=sha(binding_path))
                events.append(compiled)
            except (ValueError,RuntimeError) as error:failures.append(dict(event_id=row['event_id'],readout_type='B',reason=str(error)))
    if args.freeze and (missing or failures):
        write_json(OUT/'audit'/(args.split+'_event_freeze_blockers.json'),dict(missing=missing,failures=failures))
        raise RuntimeError('Complete the selected split reviews and mechanical readouts before freezing')
    name=f'{args.split}_events'+('' if args.freeze else '_snapshot')
    path=OUT/'config'/(name+'.jsonl');write_jsonl(path,events,freeze=args.freeze)
    write_json(OUT/'audit'/(name+'.json'),dict(status='FROZEN' if args.freeze else 'PARTIAL_SNAPSHOT',events=len(events),
        reviewed_traces=len(reviews),expected_traces=len(rows),missing=missing,failures=failures,manifest_sha256=sha(path),
        semantic_selection_before_scores=True),freeze=args.freeze)
    print(args.split,'events',len(events),'reviewed traces',len(reviews),'missing',len(missing),'mechanical failures',failures)


if __name__=='__main__':main()
