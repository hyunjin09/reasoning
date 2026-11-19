"""Exact causal states and the predeclared sparse-panel fallback."""
import argparse
from collections import Counter,defaultdict
import numpy as np
from scripts.stage6b.common import OUT,SOURCE,read_json,read_jsonl,write_json,write_jsonl,sha
from scripts.stage6b.event_results import load_run,feature_values

MANIFEST=OUT/'c1_dynamics/exact_anchor_manifest_v2.jsonl'


def dominant(scores,floor,margin):
    if len(scores)<2:return 'UNRESOLVED'
    ranked=sorted(scores,key=lambda k:(-scores[k],k))
    if scores[ranked[0]]<=floor:return 'NONE'
    if scores[ranked[0]]-scores[ranked[1]]<=margin:return 'MIXED'
    return ranked[0]


def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['freeze','analyze']);args=p.parse_args()
    if args.action=='freeze':
        assert not (OUT/'raw/dynamics_confirmation_01').exists()
        entries,results,_=load_run('dynamics_discovery_01',MANIFEST,'discovery')
        off=[]
        for eid,e in entries.items():
            r=results[eid];d=e['roles']['demanded']
            off.extend(abs(r['arms']['N']['D']-r['arms'][s+'_W2']['D']) for s in e['w2_sources'] if s!=d)
        threshold=max(.05,float(np.quantile(off,.75))) if off else .05
        write_json(OUT/'config/dominance_thresholds.json',{'effect_floor':.05,'dominance_margin':threshold,
            'fit':'Predeclared discovery Q75 absolute non-demanded-source VSD, floored at0.05; conservative empirical separation, not a validated noise distribution.',
            'off_demand_values':len(off),'discovery_anchors':len(entries),'manifest_sha256':sha(MANIFEST),
            'correctness_or_confirmation_used':False},freeze=True)
        print('Dominance margin frozen:',threshold);return
    threshold=read_json(OUT/'config/dominance_thresholds.json');entries={};results={}
    for split in ['discovery','confirmation']:
        e,r,_=load_run('dynamics_'+split+'_01',MANIFEST,split);entries.update(e);results.update(r)
    states={};exact=[];diagnostics=[]
    for eid,e in entries.items():
        r=results[eid];n=r['arms']['N'];d=e['roles']['demanded']
        scores={s:n['D']-r['arms'][s+'_W2']['D'] for s in e['w2_sources']}
        sensitivity={s:n['D']-r['arms'][s+'_W8']['D'] for s in e['w8_sources']}
        state={'id':eid,'base_id':e['base_id'],'split':e['split'],'dataset':e['dataset'],'span_index':e['span_index'],
            'demanded_source':d,'source_scores':scores,'source_scores_w8':sensitivity,
            'dominant_source':dominant(scores,threshold['effect_floor'],threshold['dominance_margin']),
            'demanded_source_margin':scores[d]-max(v for k,v in scores.items() if k!=d),
            'local_correctness':e['event']['reviewed_claim']['local_visual_correctness'],
            'numeric_label_correctness':e['event']['reviewed_claim']['numeric_label_correctness'],
            'final_correctness':e['final_correctness']['final_answer_correctness'],'native_D':n['D'],
            'causal_label_scope':'Numeric-label contrast only; geometric-role errors require a separately oriented claim contrast.'}
        state['coupled']=state['dominant_source']==d;states[eid]=state;exact.append(state)
        if state['local_correctness']!='CORRECT':
            diagnostics.append({'id':eid,'readout_orientation_valid_for_numeric_label':True,'explicit_wrong_numeric_claim':False,
                'error_promoting_claim_permitted':False,'reason':'Reviewed numeric label is correct; geometric-role misbinding is not measured by the numeric candidate pair.',
                'native_observed_claim_logP':r['passive'].get('observed_claim_candidate',{}).get('mean_log_probability')})
    pairs=read_jsonl(OUT/'c1_dynamics/transition_pairs.jsonl');holds=read_jsonl(OUT/'c1_dynamics/no_change_pairs.jsonl');refreshes=read_jsonl(OUT/'c1_dynamics/refresh_events.jsonl')
    classes=[];latencies=[];selected_refresh_ids={p['pair_id'] for p in refreshes}
    for pair in list({p['pair_id']:p for p in pairs+holds+refreshes}.values()):
        pre=states[pair['pre_id']];post=states[pair['post_id']];sources=pair['sources']
        a=dominant({s:pre['source_scores'][s] for s in sources},threshold['effect_floor'],threshold['dominance_margin'])
        b=dominant({s:post['source_scores'][s] for s in sources},threshold['effect_floor'],threshold['dominance_margin'])
        psource,tsource=pair['pre_source'],pair['post_source']
        if not pair['strict_source_identity_valid']:label='UNRESOLVED_OVERLAPPING_SOURCE_TOKENS'
        elif a in sources and b in sources:
            if pair['kind']=='transition':
                label='DEMAND_ALIGNED_SWITCH' if a==psource and b==tsource else 'FIXATION_STALE' if a==psource and b==psource else 'OTHER_CAUSAL_SWITCH'
            else:label='WANDERING' if a!=b else 'DEMAND_ALIGNED_HOLD' if b==tsource else 'STABLE_OFF_DEMAND'
        else:label='NO_SWITCH_OR_'+('MIXED' if 'MIXED' in [a,b] else 'NONE_OR_UNRESOLVED')
        classes.append({**pair,'pre_dominant':a,'post_dominant':b,'causal_state_class':label,
            'local_correctness_after':post['local_correctness'],'final_correctness':post['final_correctness'],
            'failure_causing_claim':False,'numeric_error_readout_available':False,
            'tier':'Tier1_causal_state_only' if label in ['DEMAND_ALIGNED_SWITCH','DEMAND_ALIGNED_HOLD','WANDERING','FIXATION_STALE'] else 'Tier2_or_unresolved'})
        if pair['kind']=='transition':
            available=sorted(((pair['latency_offsets'][eid],eid) for eid in pair['latency_anchor_ids'] if pair['latency_offsets'][eid]>=0))
            latency=None;observed=[];censor='end_of_reviewed_valid_window'
            for offset,eid in available:
                s=states[eid]
                if s['demanded_source']!=tsource:censor='demand_changed_again';break
                dom=dominant({k:s['source_scores'][k] for k in sources},threshold['effect_floor'],threshold['dominance_margin'])
                observed.append({'offset':offset,'id':eid,'dominant':dom})
                if dom==tsource and latency is None:latency=offset
            if not pair['strict_source_identity_valid']:latency=None;censor='overlapping_sources_not_identifiable'
            unobserved_earlier=latency is not None and any(i not in {r['offset'] for r in observed} for i in range(latency))
            latencies.append({'pair_id':pair['pair_id'],'base_id':pair['base_id'],'split':pair['split'],
                'refresh':pair['pair_id'] in selected_refresh_ids,'semantic_refresh_flag':pair['refresh'],
                'latency_reviewed_spans':latency,'right_censored':latency is None,'censor_reason':censor if latency is None else None,
                'latency_interpretation':'First observed dominant-source anchor; not an unmeasured acquisition/onset time.',
                'earlier_post_transition_spans_unobserved':unobserved_earlier,
                'delay_established_at_observed_span_resolution':latency is not None and latency>0 and not unobserved_earlier,
                'observed_anchors':observed,'refresh_class':('successful_refresh' if latency==0 else 'observed_refresh_latency_unresolved' if unobserved_earlier else 'delayed_refresh' if latency is not None else 'failed_or_unresolved_refresh') if pair['pair_id'] in selected_refresh_ids else None})
    gate=read_json(OUT/'audit/dynamic_panel_gate.json')
    counts={split:dict(Counter(c['causal_state_class'] for c in classes if c['split']==split)) for split in ['discovery','confirmation']}
    bybase=defaultdict(list)
    for s in exact:bybase[s['base_id']].append(s)
    write_jsonl(OUT/'c1_dynamics/exact_source_scores.jsonl',exact)
    write_jsonl(OUT/'c1_dynamics/wandering_fixation_classes.jsonl',classes)
    write_json(OUT/'c1_dynamics/demand_coupling.json',{'panel_gate':gate['status'],'cohort_rate_claim_permitted':gate['primary_cohort_rate_claim_permitted'],
        'descriptive_base_summaries':[{'base_id':b,'split':s[0]['split'],'anchors':len(s),'mean_DCM':float(np.mean([x['demanded_source_margin'] for x in s])),
            'within_selected_anchors_coupling':float(np.mean([x['coupled'] for x in s]))} for b,s in bybase.items()],
        'observed_selected_pair_counts':counts,'no_change_comparison':'Not estimable: no qualifying matched exact no-change pairs. No cohort wandering/fixation rates or confirmatory p-values.'})
    write_json(OUT/'c1_dynamics/transition_latency.json',{'rows':latencies,'scope':'Sparse reviewed numeric-readout anchors; right censoring is not a proven failure.'})
    write_json(OUT/'c1_dynamics/correctness_association.json',{'counts':[{'class':label,'local_correctness':correct,'pairs':n} for (label,correct),n in Counter((c['causal_state_class'],c['local_correctness_after']) for c in classes).items()],
        'causal_failure_link':'Not established by numeric contrast for geometric-role errors; states assigned before outcome strata.'})
    write_json(OUT/'c1_dynamics/error_readout_diagnostics.json',{'events':diagnostics,'error_promoting_sources_claimed':0,
        'reason':'No explicitly wrong numeric claim among the exact selected source-readout anchors; geometric role errors preserved as separate outcomes.'})
    w8=[]
    for pair in pairs:
        pre=states[pair['pre_id']];post=states[pair['post_id']];p,t=pair['pre_source'],pair['post_source']
        if not all(source in state['source_scores_w8'] for state in [pre,post] for source in [p,t]):continue
        pre_margin=pre['source_scores_w8'][p]-pre['source_scores_w8'][t]
        post_margin=post['source_scores_w8'][t]-post['source_scores_w8'][p]
        w8.append({'pair_id':pair['pair_id'],'base_id':pair['base_id'],'split':pair['split'],
            'pre_P_minus_T_W8':pre_margin,'post_T_minus_P_W8':post_margin,
            'pre_P_minus_T_W2':pre['source_scores'][p]-pre['source_scores'][t],
            'post_T_minus_P_W2':post['source_scores'][t]-post['source_scores'][p],
            'positive_P_to_T_W8_margins':pre_margin>threshold['dominance_margin'] and post_margin>threshold['dominance_margin'],
            'source_token_overlap':not pair['strict_source_identity_valid']})
    write_json(OUT/'c1_dynamics/w8_sensitivity.json',{'paired_source_comparisons':w8,
        'scope':'Frozen demanded/previous-source subset; alternative X was not scored underW8. These pairwise margins do not establish full-source W8dominance or cohort rates.'})
    print('Descriptive causal classes:',counts)


if __name__=='__main__':main()
