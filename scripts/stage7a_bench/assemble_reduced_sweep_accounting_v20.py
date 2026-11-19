"""Assemble completed-sweep denominators without ranking or new experiments."""
import argparse
from collections import Counter
from scripts.stage7a.common import ROOT,read_json,sha,write_json
from scripts.stage7a_bench.native_report_v2 import verify_hashes

O=ROOT/'outputs/stage7a_bench_v2'

def assemble(comparison_path):
    path=(ROOT/comparison_path).resolve()
    if not path.is_relative_to(O/'analysis/comparison_batches'):
        raise ValueError('Use a completed comparison artifact')
    comparison=read_json(path);verify_hashes(comparison['artifact_sha256'])
    feasibility_path=O/'analysis/reduced_selection_feasibility_with_controls_v20.json'
    feasibility=read_json(feasibility_path);verify_hashes(feasibility['source_sha256'])
    selection={r['benchmark']:r for r in feasibility['rows']}
    coverage_path=O/'analysis/reduced_state_assay_coverage_v21.json'
    coverage=read_json(coverage_path);verify_hashes(coverage['source_sha256'])
    coverage_rows={r['benchmark']:r for r in coverage['rows']}
    semantic_path=O/'analysis/reduced_semantic_control_coverage_v24.json'
    semantic=read_json(semantic_path);verify_hashes(semantic['source_sha256'])
    semantic_rows={r['benchmark']:r for r in semantic['rows']}
    hashes={str(path.relative_to(ROOT)):sha(path),str(feasibility_path.relative_to(ROOT)):sha(feasibility_path)}
    hashes[str(coverage_path.relative_to(ROOT))]=sha(coverage_path)
    hashes[str(semantic_path.relative_to(ROOT))]=sha(semantic_path)
    yields={}
    for key,digest in comparison['artifact_sha256'].items():
        if '/causal_pilot/reports/' in key and key.endswith('/yield.json'):
            result=read_json(ROOT/key)
            if result.get('status')=='COMPLETED_PILOT_YIELD_ONLY':
                yields[result['benchmark']]=result
    rows=[]
    expected={'phantom_0','charxiv','mathvision_wild','mmmu_pro','mmlongbench_doc'}
    if {r['benchmark'] for r in comparison['rows']}!=expected:raise ValueError('Reduced roster changed')
    for raw in comparison['rows']:
        bid=raw['benchmark'];dim=raw['dimensions'];native=dim['A_native']['value'];causal=dim['F_causal_failure']['value']
        if native is None or bid!='phantom_0' and causal is None:raise ValueError('All retained native reports and eligible pilots must complete')
        reviewed=sum(c['generated'] for c in native.values());frozen=sum(c['frozen'] for c in native.values())
        base_n=200
        states=causal['states'] if causal else None
        pilot_n=causal['pilot']['events'] if causal else 0
        if states and sum(s['events'] for s in states.values())!=pilot_n:raise ValueError('State accounting differs from pilot')
        strong=causal['strong_unfaithful']['events'] if causal else None
        source_failure_names=('PRIOR_FILL','WRONG_SOURCE_READ','STALE_SOURCE_READ','SOURCE_COUPLED_EXTRACTION_ERROR')
        source_failures=sum(states[k]['certified_events'] for k in source_failure_names) if states else None
        condition_rows={}
        for condition,r in native.items():
            metrics=r['metrics'];final=metrics['final'];n=r['generated']
            if final['denominator']+final['unknown']!=n:raise ValueError('Unknown final judgments lost')
            condition_rows[condition]=dict(reviewed=n,frozen=r['frozen'],excluded=r['unavailable'],metrics=metrics,
                final_accuracy_identification_bounds=([final['numerator']/n,(final['numerator']+final['unknown'])/n]
                    if n and final['denominator'] else None),
                bounds_scope='Worst/best assignment of unadjudicated responses; not confidence intervals or comparable benchmark scores.')
        row=dict(benchmark=bid,native_conditions_reviewed=reviewed,native_conditions_frozen=frozen,
            frozen_native_bases=base_n,conditions=condition_rows,
            source_identifiability=dim['B_source_identifiability']['value'],
            structural_readout_feasibility=dim['C_readout_feasibility']['value'],
            event_readout_source_feasibility=selection.get(bid),
            faithful_control_yield=dim['E_faithful']['value'],
            counterfactual_editability=dim['D_counterfactual_editability']['value'],
            paired_conditions=dim['G_paired_conditions']['value'],diversity=dim['H_diversity']['value'],
            causal_pilot_events=pilot_n,causal_pilot=causal['pilot'] if causal else None,
            state_counts=states,strong_unfaithful_events=strong,
            certified_source_faithfulness_failures=source_failures,
            source_failure_states=list(source_failure_names),
            source_failure_subtotal_scope='Excludes downstream integration, which has a correct source/local read; legacy aggregate retained separately.',
            frozen_state_assay_coverage=coverage_rows.get(bid),
            frozen_semantic_control_coverage=semantic_rows.get(bid),
            candidate_anomaly_flags_nested_within_unresolved=yields.get(bid,{}).get('candidate_anomaly_events'),
            strong_faithful=yields.get(bid,{}).get('strong_faithful'),
            strong_unfaithful_events_per_100_reviewed_native_conditions=(100*strong/reviewed if strong is not None else None),
            strong_unfaithful_events_per_100_frozen_native_bases=(100*strong/base_n if strong is not None else None),
            strong_unfaithful_events_per_pilot_event=(strong/pilot_n if pilot_n else None),
            gpu_cost=dim['J_gpu_cost']['value'],reliable_annotation_minutes=None,
            annotation_burden=dict(full_response_reviews=reviewed,
                source_readout_candidates_prepared=selection.get(bid,{}).get('prepared_events'),
                unique_reviewed_local_control_images=selection.get(bid,{}).get('reviewed_control_images')))
        if bid=='mmlongbench_doc':
            row['annotation_burden'].update(full_response_characters=2122005,
                documented_review_agent_elapsed_minutes_approx=135,
                note='Agent elapsed review time only; excludes some source/control preparation and is not measured human annotation time.')
        rows.append(row)
    assert sum(r['native_conditions_reviewed'] for r in rows)==1382
    assert sum(r['native_conditions_frozen'] for r in rows)==1392
    assert sum(r['causal_pilot_events'] for r in rows)==187
    totals=Counter();certified=Counter()
    for r in rows:
        for state,c in (r['state_counts'] or {}).items():totals[state]+=c['events'];certified[state]+=c['certified_events']
    result=dict(status='COMPLETED_REDUCED_SWEEP_ACCOUNTING',rows=rows,
        totals=dict(native_conditions_reviewed=1382,native_conditions_frozen=1392,frozen_native_bases=1000,
            native_bases_with_reviewed_responses=990,causal_pilot_events=187,state_events=dict(totals),certified_state_events=dict(certified)),
        source_sha256=hashes,assembler_sha256=sha(ROOT/'scripts/stage7a_bench/assemble_reduced_sweep_accounting_v20.py'),
        scope='Rates are captured yields, not natural-prevalence estimates. Repeated events/bases/families remain nested in rows. Phantom has no eligible source-localized pilot; N/A is not zero. Annotation minutes unknown. Candidate anomaly flags are not certified anomaly states.',
        primary_benchmark_selected=False,rankings_assigned=False,recommendation_executed=False)
    dest=O/'analysis/reduced_sweep_complete_accounting_v20.json'
    if dest.exists():raise FileExistsError('Preserve previous accounting')
    write_json(dest,result,freeze=True)
    print(dest)
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--comparison',required=True)
    assemble(parser.parse_args().comparison)
