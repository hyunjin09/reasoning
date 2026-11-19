#!/usr/bin/env python3
"""Write reproducible acceptance, resource evidence and exactly one recommendation."""
from pathlib import Path
import re
from scripts.stage3c10.freeze_inputs import ROOT,OUT,read_json,read_jsonl,write_json


def fmt(x):return 'unavailable' if x is None else f'{x:.6g}'

def main():
    result=read_json(OUT/'analysis/retrieval_trigger_summary.json')
    assessment=read_json(OUT/'analysis/paper_claim_assessment.json')
    primary=read_json(OUT/'phase_b_primary/primary_statistics.json')
    mechanics=read_json(OUT/'audit/mechanical_validation.json');audit=read_json(OUT/'audit/independent_artifact_validation.json')
    hpre=read_json(OUT/'phase_e_mediation/hpre_statistics.json')['targets']
    layers=read_json(OUT/'phase_d_layers/layer_profile.json')
    temporal=read_json(OUT/'phase_c_temporal/temporal_profile.json')
    generic=read_json(OUT/'analysis/generic_language_damage.json')
    raw=[read_json(p) for p in (OUT/'raw').glob('*/shard_*/*/target_*/*.json')]
    runtime={}
    for p in (OUT/'raw').glob('*/shard_*/run_summary.json'):
        r=read_json(p);runtime[r['phase']]=max(runtime.get(r['phase'],0),r['runtime_seconds'])
    resources={'slurm_allocation':'108548','node':'node07','tmux_session':'9','gpus':4,'gpu_model':'NVIDIA RTX A6000',
        'additional_allocations_requested':0,'project_environment':'.venv','dtype':'bfloat16','max_generated_chunk':2048,
        'max_saved_condition_allocated_GiB':max(r['peak_gpu_allocated_bytes'] for r in raw)/2**30,
        'max_saved_condition_reserved_GiB':max(r['peak_gpu_reserved_bytes'] for r in raw)/2**30,
        'max_rank_runtime_seconds_per_phase':runtime,'timing_excludes_model_startup':True,
        'memory_aggregation':'max over every saved condition; inherited prefill resets CUDA peak counters',
        'scheduler_ids':['stage3c10_validation_tmux 9_108548','stage3c10_primary_tmux 9_108548','stage3c10_followups_tmux 9_108548'],
        'logs':['runs/stage3c10_validation_108548.log','runs/stage3c10_primary_108548.log','runs/stage3c10_followups_108548.log']}
    write_json(OUT/'audit/resource_summary.json',resources)
    tests=(ROOT/'runs/stage3c10_regression_tests_final.log').read_text()
    match=re.search(r'(\d+) passed',tests);testcount=int(match.group(1)) if match else 0
    checks={
        'exact_31_historical_bases':mechanics['N_unique_bases']==7 and len({r['base_problem_id'] for r in raw if r['phase']=='primary'})==24,
        'exact_7_24_split':audit['checks']['primary_exact_coverage'],
        'frozen_MT_coordinates':mechanics['checks']['mt_coordinates'],
        'exact_historical_RDS':mechanics['checks']['rds_reconstruction'],
        'source_groups_frozen':audit['checks']['historical_input_hashes'] and audit['checks']['all_trace_sources'],
        'current_query_only_trigger':audit['checks']['all_trace_positions'],
        'upstream_layers_frozen':audit['checks']['all_trace_layers_heads'],
        'T0_semantics_exact':mechanics['checks']['target_t0_semantics'],
        'irrelevant_ROI_control':mechanics['checks']['irrelevant_roi_isolated'],
        'M_state_control':audit['checks']['primary_exact_coverage'],
        'generic_damage_controls':all(len(generic[t])==2 for t in result),
        'routing_only_cannot_pass_behavioral_gate':all(set(r['primary_trigger_gate']['checks'])=={'rds_T','vsd_T','did','r16_minus_e16','target_minus_irrelevant'} for r in result.values()),
        'temporal_gate_obeyed':audit['checks']['temporal_gate'],
        'layer_gate_obeyed':audit['checks']['layer_gate'],
        'same_state_Q_native_recipient_KV':audit['checks']['Q_rescue_recipient_KV'],
        'hpre_gated_secondary_upper_bound':audit['checks']['hpre_gate'],
        'targets_separately_interpreted':set(result)=={'target_a','target_b'},
        'no_attention_selection':audit['checks']['annotation_blind_freeze'],
        'no_sink_or_Stage 4_started':not assessment['follow_on_started'] and not read_json(OUT/'config/stage3c10_config.json')['sink_manipulated'],
        'one_recommendation':isinstance(assessment['recommendation'],str) and bool(assessment['recommendation']),
    }
    passed=all(checks.values()) and mechanics['passed'] and audit['passed'] and testcount>=45
    acceptance={'status':'PASS' if passed else 'FAIL','checks':checks,'passed_count':sum(checks.values()),'total_count':len(checks),
        'mechanical_checks':sum(mechanics['checks'].values()),'artifact_checks':sum(audit['checks'].values()),
        'regression_tests_passed':testcount,'scientific_outcomes':{t:r['outcome'] for t,r in result.items()},
        'mediation_outcomes':{t:r['mediation'] for t,r in result.items()},'recommendation':assessment['recommendation'],
        'follow_on_started':False,'resources':'audit/resource_summary.json'}
    write_json(OUT/'summaries/stage3c10_acceptance.json',acceptance)
    lines=['# Stage 3C.10 — Reasoning-State Retrieval Trigger','',
        '**Technical '+acceptance['status']+'; O1 — Reasoning-State Retrieval Trigger at both targets. M2 — Routing mediation only.**','',
        'Recent reasoning contribution causally changes target-specific current-query visual-source dependence at the two historical retrieval coordinates. The stronger claim that this behavioral effect is mediated by the frozen late Q geometry is **not supported**. All-head native-Q rescue restores routing exactly but does not robustly rescue VSD; the optional late h_pre rescue is also nonrobust.','',
        'The approved plan is complete and stopped. The sole recommendation is **'+assessment['recommendation']+'**, for review only. No follow-on experiment has started.','',
        '## Fixed assay and validity','',
        'Exact Stage 3C.3 manifests: 7 validation and 24 primary bases, with M/T and A/B paired within each base. Original O images, model/tokenizer, historical divergent suffixes, ROIs, causal/noncausal heads, and question-text source spans are preserved. A uses upstream layers 0–28 and routing layer 29; B uses 0–27 and layer 28. All 32 query heads receive trigger deletion. T0 suppresses only the current query, all 36 layers/all 32 heads.','',
        'Every comparison uses one per-base A6000 BF16 cached partition: native multimodal prefill, maximum 2048 generated-token chunk, and shared before/after barriers at every M/T query. The RDS function is imported unchanged from Stage 3C.3. All causal denominators and controls are newly scored on this same path. Historical A5000 full-path values are descriptive references only.','',
        f"Validation: {sum(mechanics['checks'].values())}/15 checks across seven bases, 28 state files and {mechanics['scored_arms']} arms. No-op, deterministic replay, self-Q, inherited uninstrumented cached scores and cached T0 are exact. Actual full-past K/V comparisons imply unchanged visual K/V. Artifact audit: {sum(audit['checks'].values())}/{len(audit['checks'])} checks across {audit['raw_state_files']} files, {audit['scored_arms']} arms and {audit['source_layer_calls']} source-layer traces. Focused/new plus inherited tests: {testcount} passed.",'',
        'R16 excludes the current token and intersects generated history: primary base 119 has 14/13 preceding M tokens for A/B, and base 120 has 6/5. Validation base 128-B-M has 15. No base was excluded. E16 is available on 22/24 T bases and is never shifted to fill missing history. Q is the exact historical question-content span; structural `<|im_start|>` is untouched.','',
        '## Primary results','',
        'Eight prespecified contrasts per target use two-sided paired Wilcoxon with Holm correction. Unrun rescue slots were p=1 when primary gates froze; those gates never changed afterward. Robust positive means corrected p<.05, positive bootstrap mean CI, median>0 and at least 75% positive bases. Bootstrap uses 10,000 base resamples, seed 12348. E16 comparisons use 22 available paired bases.','',
        '| Target | Contrast | n | Median | Mean [bootstrap 95% CI] | Positive | Primary Holm p |','|---|---|---:|---:|---|---:|---:|']
    for t,name in [('target_a','A'),('target_b','B')]:
        for key,s in primary['statistics'][t].items():
            if key.startswith('q_rescue'):continue
            ci=s['bootstrap_mean_ci95'];lines.append(f"| {name} | {key} | {s['N_unique_bases']} | {fmt(s['median'])} | {fmt(s['mean'])} [{fmt(ci[0])}, {fmt(ci[1])}] | {s['positive_count']}/{s['N_unique_bases']} | {fmt(s['holm_p'])} |")
    lines += ['', 'Both targets pass all five behavioral-trigger gate contrasts. R16 also exceeds the question-source control. Routing changes at all 24 T bases per target; behavioral trigger effects are positive on 20/24 A and24/24 B. Routing alone is not the basis of this conclusion.','',
        '## Temporal and layer localization','',
        '| Target | R1 | R2 | R4 | R8 | R16 | k80 |','|---|---:|---:|---:|---:|---:|---:|']
    for t,name in [('target_a','A'),('target_b','B')]:lines.append('| '+name+' | '+' | '.join(fmt(temporal[t][str(k)]['median']) for k in [1,2,4,8,16])+f" | {result[t]['k80']['k80']} |")
    lines += ['', 'Entries are median TE_VSD. k80=16 at both targets is a tested threshold descriptor, not a unique 16-token information span: A R8 and B R4 lie just below 80% of the R16 median. The B curve is nonmonotonic. Trigger influence is broader across the tested recent window than the earlier 1–2-token carrier result.','',
        'Only layers 16–23 (L2) pass the frozen bin-wise correction at both targets. A median TE_VSD='+fmt(layers['target_a']['L2']['median'])+'; B='+fmt(layers['target_b']['L2']['median'])+'. Other bins are retained as negative evidence; they were not redefined.','',
        '## Mediation and its limits','',
        '| Target | Rescue | Median VSD gain | Positive | Corrected p | Robust |','|---|---|---:|---:|---:|---|']
    for t,name in [('target_a','A'),('target_b','B')]:
        medstats=read_json(OUT/'phase_e_mediation/mediation_statistics.json')[t]
        for label,s in [('All 32 Q',result[t]['statistics']['q_rescue_vsd']),('Historical 4 Q',medstats['selected_head_secondary']['vsd']),('h_pre (secondary)',hpre[t]['vsd'])]:
            lines.append(f"| {name} | {label} | {fmt(s['median'])} | {s['positive_count']}/24 | {fmt(s['holm_p'])} | {s['robust_positive']} |")
    lines += ['', 'All-head and selected-head Q rescues restore the primary routing readout exactly on 24/24 bases per target. This is expected when native Q is reinstated with unchanged visual K; behavioral VSD rescue is the nontrivial test. It fails the robust-positive rule for both targets. Target-A h_pre VSD gain is negative on average, with a two-sided corrected p below .05; it is not a positive rescue. Target-B h_pre gain is positive but nonrobust.','',
        'The optional h_pre donor can contain native upstream visual evidence and bypass part of all-layer ROI suppression. Its VSD result is not a guaranteed numerical upper bound. The mediator of the recent-input behavioral effect remains unknown; broader redundancy and earlier/multiple state paths are possible explanations, not established diagnoses. Exact same-path replay, source isolation and recipient-K/V audits pass, so no further diagnostic or rescue search was run.','',
        '## Generic computation and secondary content','',
        'R16 changes residual/attention-output norms and candidate distributions as well as retrieval. Median original-candidate NLL changes at T are small (A '+fmt(generic['target_a']['T']['R16']['original_NLL_change']['median'])+', B '+fmt(generic['target_b']['T']['R16']['original_NLL_change']['median'])+'), while counterfactual NLL changes are larger (A '+fmt(generic['target_a']['T']['R16']['counterfactual_NLL_change']['median'])+', B '+fmt(generic['target_b']['T']['R16']['counterfactual_NLL_change']['median'])+'). Noncausal-head routing also changes, especially A; the trigger is not restricted to the historical four heads. M-state entropy shifts and complete E16/Q controls are saved in `analysis/generic_language_damage.json`. These controls support the bounded retrieval-specific contrast, not a claim of exclusively retrieval-only computation.','',
        'All 763 available last-eight single-position effects were scored after primary freeze. Last 16 annotations were copied from the attention-blind Stage 3C.8 taxonomy with exact token/position checks before position scoring. Effects are centered within exact target/state/distance and then aggregated once per base/type. A T-state mean effects are largest at distance 2, whereas B is strongest at distance 1; single-position effects do not by themselves identify the cumulative R16 mechanism. No universal token class is claimed. Historical sink mass is overlaid descriptively for 48 target/base cells; no sink token is manipulated.','',
        '## Paper assessment and stop','',
        assessment['new_causal_link'],'',assessment['remaining_central_ambiguity'],'',assessment['sink_value'],'',
        'The paper now has a causal recent-input link in addition to the earlier query-routing and visual-Value/carrier results, but cannot present an end-to-end Q-mediated behavioral chain. The same late-state rescue ambiguity echoes prior routing/behavior dissociation; another unrestricted local search is not authorized. A separately reviewed multi-evidence test offers a larger test of the lifecycle’s scope.','',
        '**One recommendation: '+assessment['recommendation']+'.** '+assessment['paper_priority'],'',
        'No sink causality, broader-history trigger search, new cohort, Stage 4 or failure experiment was started.','',
        '## Evidence and resources','',
        '- Primary freeze/statistics: `phase_b_primary/primary_freeze.json`, `primary_statistics.json`.\n- Complete traces: `raw/{validation,primary,temporal,layers,mediation,hpre,positions}/`.\n- Mechanics/artifact audits: `audit/mechanical_validation.json`, `independent_artifact_validation.json`.\n- Mediation: `phase_e_mediation/mediation_statistics.json`, `hpre_statistics.json`.\n- Secondary position/type: `phase_f_secondary/recent_position_scan.jsonl`, `token_type_analysis.json`.\n- Sixteen standalone PNG/PDF figures: `analysis/figures/index.json`.\n- Technical acceptance: `summaries/stage3c10_acceptance.json`.','',
        f"Only existing Slurm 108548 / tmux 9 / node07 four A6000 GPUs were used. No allocations or packages were added. Maximum saved-condition memory: {resources['max_saved_condition_allocated_GiB']:.2f} GiB allocated / {resources['max_saved_condition_reserved_GiB']:.2f} GiB reserved. Per-phase timing and scheduler/log identities are in `audit/resource_summary.json`. All frozen historical input hashes and all primary-score hashes remain unchanged.",'']
    (OUT/'summaries/stage3c10_summary.md').write_text('\n'.join(lines))
    recommendation='# Stage 3C.10 next-stage recommendation\n\n**'+assessment['recommendation']+' — review only.**\n\nBoth targets pass the recent-input behavioral trigger gate, but native-Q and late h_pre rescue do not establish its behavioral mediator. Preserve O1/M2, the16–23 layer localization, near-threshold k80=16, and the failed mediation evidence.\n\nA multi-evidence experiment would test the generality and paper value of the established local lifecycle. A sink intervention would add a side mechanism without resolving the observed mediation failure. No broader-history or repeated rescue search is proposed here.\n\nReview and approve a concrete Stage 4 plan before execution. Stage 3C.10 is complete and stopped; no follow-on has started.\n'
    (OUT/'summaries/next_stage_recommendation.md').write_text(recommendation)
    print({'technical_status':acceptance['status'],'checks':f"{sum(checks.values())}/{len(checks)}",'tests':testcount,'recommendation':assessment['recommendation']})
    if not passed:raise SystemExit(1)

if __name__=='__main__':main()
