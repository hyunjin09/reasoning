"""Select exact transition anchors from frozen semantic reviews, without scores."""
import re
from collections import defaultdict,Counter
from decimal import Decimal,InvalidOperation
from transformers import AutoTokenizer
from scripts.stage6b.common import ROOT,OUT,SOURCE,read_json,read_jsonl,write_json,write_jsonl,sha,verify_stage6a
from visual_reasoning.stage6b.protocol import candidate_event


def numeric_span(quote,truth):
    try:target=Decimal(str(truth))
    except InvalidOperation:return None
    for m in re.finditer(r'(?<![\d.])-?\d+(?:\.\d+)?(?![\d.])',quote):
        if Decimal(m.group())==target:return m.span()
    return None


def main():
    verify_stage6a()
    tokenizer=AutoTokenizer.from_pretrained(read_json(OUT/'config/stage6b_config.json')['model_checkpoint'],local_files_only=True)
    release={r['event_id']:r for r in read_jsonl(SOURCE/'cohort/primary_release_events.jsonl') if r['cohort']=='C1' and r['condition']=='intact'}
    natives={r['event_id']:r for r in read_jsonl(SOURCE/'traces/controlled_native_index.jsonl') if r['event_id'] in release}
    truths=defaultdict(dict);maps=defaultdict(dict);spans=defaultdict(list)
    for r in read_jsonl(SOURCE/'regions/ground_truth_rois.jsonl'):
        if r['cohort']=='C1':truths[r['base_id']][r['source_id']]=r
    for r in read_jsonl(SOURCE/'regions/controlled_roi_maps.jsonl'):
        if r['event_id'] in release:maps[r['event_id']][r['source_id']]=r['absolute_token_indices']
    for r in read_jsonl(SOURCE/'traces/controlled_demand_annotations.jsonl'):
        if r['event_id'] in release and r.get('manual_prefix_review'):spans[r['event_id']].append(r)
    finals={r['event_id']:r for r in read_jsonl(SOURCE/'traces/controlled_final_correctness.jsonl')}
    all_candidates={};rejections=[];pairs=[];nochanges=[];refreshes=[];selected={};panels=[];interval_counts=[]
    for eid,row in release.items():
        base=row['base_id'];sequence=sorted(spans[eid],key=lambda x:x['token_start']);native=natives[eid]
        tokens=read_jsonl(native['tokens_artifact']);raw=''.join(t['decoded_token'] for t in tokens)
        candidates={}
        for i,s in enumerate(sequence):
            if s['unresolved'] or len(s['demanded_sources'])!=1:continue
            source=s['demanded_sources'][0]
            if source not in truths[base] or not maps[eid].get(source):continue
            truth=str(truths[base][source]['truth_value'])
            foil=truths[base][source]['counterfactual_value']
            if foil is None:
                others=[str(t['truth_value']) for k,t in sorted(truths[base].items()) if k!=source and str(t['truth_value'])!=truth]
                foil=others[0] if others else str(Decimal(truth)+2)
            errors=[]
            for claim in s.get('source_claims',[]):
                if claim['source_id']!=source:continue
                quote=claim['quote'];start=raw.find(quote,s['char_start'],s['char_end'])
                if start<0:errors.append('Reviewed quote not wholly in assigned native span');continue
                numeric=numeric_span(quote,truth)
                if numeric is None:errors.append('No literal truth-equivalent numeric readout in reviewed quote');continue
                a,b=numeric
                try:event=candidate_event(tokens,start+a,start+b,truth,str(foil),tokenizer)
                except ValueError as error:errors.append(str(error));continue
                event.update(reviewed_claim=claim,readout_char_start=start+a,readout_char_end=start+b,
                    readout_scope='Numeric label use; geometric role correctness and error causation are separate.')
                candidates[i]={'id':eid+'__'+s['span_id'],'event_id':eid,'base_id':base,'cohort':'C1',
                    'dataset':row['dataset'],'split':row['split'],'group_id':row['group_id'],'condition':'intact',
                    'phase':'c','row':row,'event':event,'span_id':s['span_id'],'span_index':i,
                    'semantic_state':s,'source_groups':maps[eid],'roles':{'demanded':source},
                    'native_input_path':native['input_metadata_artifact'],'native_generation_path':native['generation_artifact'],
                    'w2_sources':[],'w8_sources':[],'final_correctness':finals[eid],
                    'selection_rule':'Reviewed single-source numeric readout, no attention/effect selection',
                    'irrelevant_control':'No separately validated irrelevant C1 numeric ROI; absent rather than fabricated.'}
                break
            if i not in candidates:rejections.append({'event_id':eid,'span_id':s['span_id'],'reasons':errors or ['No independently reviewed source claim']})
        all_candidates.update({x['id']:x for x in candidates.values()})
        def readout_at(i):
            if i in candidates:return i
            if i+1<len(sequence) and sequence[i+1]['demanded_sources']==sequence[i]['demanded_sources'] and not sequence[i+1]['unresolved'] and i+1 in candidates:return i+1
            return None
        transitions=[];holds=[]
        for i in range(1,len(sequence)):
            pre,post=sequence[i-1],sequence[i]
            if pre['unresolved'] or post['unresolved'] or len(pre['demanded_sources'])!=1 or len(post['demanded_sources'])!=1:continue
            a,b=readout_at(i-1),readout_at(i)
            if a is None or b is None or a>=b:continue
            p,t=pre['demanded_sources'][0],post['demanded_sources'][0]
            alternatives=[x for x in sorted(maps[eid]) if x not in {p,t}]
            if p==t and not alternatives:continue
            compare=[p,t]+alternatives[:1]
            compare=list(dict.fromkeys(compare))
            overlap=[(x,y) for j,x in enumerate(compare) for y in compare[j+1:] if set(maps[eid][x])&set(maps[eid][y])]
            prior_return=p!=t and any(t in x['demanded_sources'] for x in sequence[:i-1] if not x['unresolved'])
            pair={'pair_id':eid+'__P'+str(i).zfill(3),'event_id':eid,'base_id':base,'split':row['split'],'group_id':row['group_id'],'dataset':row['dataset'],
                'transition_span_index':i,'pre_id':candidates[a]['id'],'post_id':candidates[b]['id'],
                'pre_source':p,'post_source':t,'kind':'transition' if p!=t else 'no_change','sources':compare,
                'source_token_overlap_pairs':overlap,'strict_source_identity_valid':not overlap,
                'normalized_progress':post['normalized_token_progress'],
                'span_length':post['token_end']-post['token_start'],'refresh':prior_return,
                'latency_anchor_ids':[candidates[j]['id'] for j in range(max(0,i-2),min(len(sequence),i+3)) if j in candidates],
                'latency_offsets':{candidates[j]['id']:j-i for j in range(max(0,i-2),min(len(sequence),i+3)) if j in candidates}}
            (transitions if p!=t else holds).append(pair)
        chosen=transitions[:2]
        interval_counts.append({'base_id':base,'reviewed_spans':len(sequence),
            'single_source_reviewed_spans':sum(len(s['demanded_sources'])==1 and not s['unresolved'] for s in sequence),
            'multi_source_reviewed_spans':sum(len(s['demanded_sources'])>1 and not s['unresolved'] for s in sequence),
            'valid_single_source_numeric_readouts':len(candidates),
            'eligible_transition_intervals_before_sampling':len(transitions),
            'eligible_no_change_intervals_before_matching':len(holds)})
        matched=[]
        for p in chosen:
            eligible=[h for h in holds if h['post_source']==p['post_source'] and h['pair_id'] not in {m['pair_id'] for m in matched}]
            if not eligible:continue
            strict=[h for h in eligible if abs(h['normalized_progress']-p['normalized_progress'])<=.2 and max(h['span_length'],p['span_length'])/max(1,min(h['span_length'],p['span_length']))<=2]
            pool=strict or eligible
            # First chronological match meeting the frozen tolerances; closest progress fallback recorded.
            h=min(pool,key=lambda h:h['transition_span_index'] if strict else abs(h['normalized_progress']-p['normalized_progress']))
            h={**h,'matched_transition_id':p['pair_id'],'matching_tolerances_met':bool(strict)};matched.append(h)
        refresh=next((p for p in transitions if p['refresh']),None)
        if not chosen:continue
        pairset={p['pair_id']:p for p in chosen+matched+([refresh] if refresh else [])}
        for pair in pairset.values():
            for aid in set([pair['pre_id'],pair['post_id']]+pair['latency_anchor_ids']):
                e=selected.setdefault(aid,all_candidates[aid])
                e['w2_sources']=sorted(set(e['w2_sources'])|set(pair['sources']))
                if pair['pair_id'] in {chosen[0]['pair_id']}|({matched[0]['pair_id']} if matched else set()):
                    if aid in [pair['pre_id'],pair['post_id']]:
                        e['w8_sources']=sorted(set(e['w8_sources'])|{pair['pre_source'],pair['post_source']})
        pairs+=chosen;nochanges+=matched
        if refresh:refreshes.append(refresh)
        panels.append({'base_id':base,'split':row['split'],'dataset':row['dataset'],'localized_sources':sorted(maps[eid]),
            'transition_pairs':[p['pair_id'] for p in chosen],'no_change_pairs':[p['pair_id'] for p in matched],
            'refresh_pair':refresh['pair_id'] if refresh else None,'valid_numeric_readout_spans':len(candidates)})
    entries=sorted(selected.values(),key=lambda r:(r['split']!='discovery',r['base_id'],r['span_index']))
    write_jsonl(OUT/'c1_dynamics/dynamic_panel_manifest.jsonl',panels,freeze=True)
    for name,value in [('transition_pairs',pairs),('no_change_pairs',nochanges),('refresh_events',refreshes),('exact_anchor_manifest',entries)]:
        write_jsonl(OUT/'c1_dynamics'/f'{name}.jsonl',value,freeze=True)
    strictpairs=[p for p in pairs if p['strict_source_identity_valid']];strictholds=[p for p in nochanges if p['strict_source_identity_valid']]
    valid=len(panels)>=48 and len(strictpairs)>=64 and len(strictholds)>=64
    gate={'status':'CONFIRMATORY_GATE_PASS' if valid else 'DESCRIPTIVE_EXACT_ANCHORS_ONLY','bases':len(panels),
        'transitions':len(pairs),'no_change':len(nochanges),'refresh':len(refreshes),'exact_anchors':len(entries),
        'disjoint_transitions':len(strictpairs),'disjoint_no_change':len(strictholds),
        'minimum':{'bases':48,'transitions':64,'no_change':64},'primary_cohort_rate_claim_permitted':valid,
        'readout_rejections':rejections,'single_source_readout_candidates':len(all_candidates),
        'limitation':'Claims lacking local numeric contrasts and multi-source spans do not become a forced source winner; geometric-role errors are not numeric-label errors.'}
    write_json(OUT/'audit/dynamic_panel_gate.json',gate,freeze=True)
    rules={'selection':'First up to2 reviewed single-source transitions and matched no-change pairs per base; first refresh; latency +/-2 reviewed spans with valid literal readouts.',
        'effect_floor':.05,'dominance_margin_fit':'max(0.05, discovery Q75 absolute VSD among tested sources absent from current semantic demand)',
        'w8':'Pre/post of first selected transition and first matched no-change per base; demanded and previous sources only.',
        'primary_window':2,'source_overlap':'All recorded; overlapping compared source footprints prohibit strict labels.',
        'not_error_promoting_from_numeric_role_mismatch':True,'gate':{k:v for k,v in gate.items() if k!='readout_rejections'},
        'manifest_sha256':sha(OUT/'c1_dynamics/exact_anchor_manifest.jsonl')}
    write_json(OUT/'config/dynamic_state_rules.json',rules,freeze=True)
    write_json(OUT/'audit/dynamic_readout_coverage_diagnostic.json',{'scope':'One semantic-only diagnostic of the failed panel gate; no effects, attention, cohort replacement or new scoring.',
        'by_base':interval_counts,'valid_numeric_readout_anchors':len(all_candidates),
        'total_eligible_no_change_before_matching':sum(r['eligible_no_change_intervals_before_matching'] for r in interval_counts),
        'total_eligible_transitions_before_sampling':sum(r['eligible_transition_intervals_before_sampling'] for r in interval_counts),
        'strict_single_source_interpretation':'Aggregate multi-source demand spans are retained in native passive extraction, but cannot identify a strict single-source winner change without resolving within-span subgoals.',
        'frozen_primary_manifest_reproduced':True},freeze=True)
    print({k:v for k,v in gate.items() if k!='readout_rejections'})


if __name__=='__main__':main()
