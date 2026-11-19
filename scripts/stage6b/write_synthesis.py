"""Evidence-linked Stage6B acceptance and one recommendation; no next-stage run."""
from collections import Counter
from scripts.stage6b.common import OUT,read_json,read_jsonl,write_json,sha


def main():
    c1=read_json(OUT/'c1_mirage/claim_assessment.json');c2=read_json(OUT/'c2_alignment_retrieval/claim_assessment.json')
    c3=read_json(OUT/'c3_object_stress/replication_assessment.json');c4=read_json(OUT/'c4_natural_validation/exploratory_effects.json')
    mirage=read_json(OUT/'c1_mirage/mirage_confirmation.json');dynamic=read_json(OUT/'c1_dynamics/demand_coupling.json')
    geometry=read_json(OUT/'trajectory/pca_discovery.json');coverage=read_json(OUT/'audit/native_endpoint_coverage.json')
    native_meta=read_json(OUT/'audit/native_acquisition_context.json')['condition_summaries']
    resources=read_json(OUT/'audit/resource_summary.json');replay=read_json(OUT/'audit/causal_score_replay.json')
    template=read_json(OUT/'analysis/template_robustness.json');sink=read_json(OUT/'sink/future_sink_gate.json')
    sink_confirmation=read_json(OUT/'sink/sink_descriptive_statistics.json')['C1_strict_mirage_comparisons']['confirmation']
    assert coverage['passive_endpoints']==14906 and replay['status']=='PASS'
    classes=read_jsonl(OUT/'c1_dynamics/wandering_fixation_classes.jsonl')
    failures=[r for r in classes if r['causal_state_class'] in ['WANDERING','FIXATION_STALE'] and r['split']=='confirmation']
    error=read_json(OUT/'c1_dynamics/error_readout_diagnostics.json')
    rescue={'rescue_ready':False,'minimum_qualified_confirmation_events':24,
        'C1_strict_candidate_events':mirage['strict_event_count'],'C1_strict_candidate_bases':mirage['strict_base_count'],
        'C1_post_label_candidate_preferences':mirage['post_label_outcomes'],
        'confirmation_strict_wandering_or_fixation_comparisons':len(failures),
        'error_promoting_sources_established':error['error_promoting_sources_claimed'],
        'C3_secondary_candidates':c3['confirmation_mirage_like_candidates'],
        'qualified_native_error_linked_confirmation_events':0,
        'correctly_oriented_native_error_mechanism_established':False,
        'mechanism_matched_intervention_and_nonfailure_control_predictions_established':False,
        'reason':'Nine strict C1 fixed-prefix candidates are fewer than24 and do not establish a generated native error mechanism. Dynamics lack matched holds and a geometric-error contrast. C3masks preserve context; C4has passive wrong-claim anchors without exact causal states.',
        'rescue_experiments_run':0}
    write_json(OUT/'analysis/rescue_readiness.json',rescue)
    claims={
        'O1_alignment_retrieval_dissociation':{'strong_claim':c2['strong_focal_alignment_retrieval_dissociation'],
            'finding':'Focal demand changes source necessity robustly; expected alignment attention/QK and matched high-attention yield do not satisfy the full gate.',
            'evidence':'c2_alignment_retrieval/claim_assessment.json'},
        'O2_grounding_to_mirage':{'strong_claim':c1['strong_mirage_claim'],
            'finding':'Strong/mask target grounding losses survive sham controls. Strict held-out candidates exist, but continuous engagement-grounding divergence fails the full robustness gate.',
            'strict_events':mirage['strict_event_count'],'strict_bases':mirage['strict_base_count'],
            'dataset_heterogeneity':'MathVision attention-divergence subgroup passes its frozen gate; MathVerse/MathVista and every leave-one-dataset-out attention-divergence contrast do not.',
            'evidence':'c1_mirage/claim_assessment.json'},
        'O3_demand_aligned_dynamic_retrieval':{'strong_claim':False,
            'finding':'Selected causal switches are observed; stable-demand stability cannot be tested with zero matched no-change pairs.',
            'selected_pair_counts':dynamic['observed_selected_pair_counts'],'evidence':'c1_dynamics/demand_coupling.json'},
        'O4_wandering':{'strong_claim':False,'status':'UNIDENTIFIED_NO_MATCHED_HOLDS'},
        'O5_fixation_staleness':{'strong_claim':False,'status':'NONE_STRICTLY_IDENTIFIED_IN_SELECTED_PANEL; no cohort prevalence claim'},
        'O6_path_length_reinterpretation':{'strong_claim':False,
            'finding':'Discovery-only PCA and original-space metrics are descriptive. The sparse causal panel cannot establish that demand coupling outperforms path length at cohort scale.'},
        'O7_object_replication':{'strong_claim':c3['replication_support'],'evidence':'c3_object_stress/replication_assessment.json'},
        'O8_natural_validation':{'strong_claim':False,'status':'EXPLORATORY_PASSIVE_DESCRIPTORS_ONLY',
            'causal_replication_established':c4['causal_replication_established'],'evidence':'c4_natural_validation/exploratory_effects.json'}}
    write_json(OUT/'analysis/paper_claim_assessment.json',{'claims':claims,'template_robustness':template['status'],
        'sink_causality_gate':sink['recommend_sink_causality'],'thresholds_relaxed':False,
        'scope':'Negative and underidentified findings remain distinct. No PCA coordinate, answer persistence, or passive similarity supplies an unmeasured causal mechanism.'})
    # The alternatives are ranked from their stated gates, not from a search for positivity.
    assert not rescue['rescue_ready'] and not c2['strong_focal_alignment_retrieval_dissociation']
    assert not c1['strong_mirage_claim'] and not c3['replication_support'] and not dynamic['cohort_rate_claim_permitted']
    recommendation={'recommendation':'GO — Cohort/Assay Repair','execute_next_stage':False,
        'primary_underidentification':'Dynamic source/readout assay: 20 eligible bases, 34 primary transitions, 0 matched no-change pairs, and no explicit geometric-error contrast. Compound semantic spans do not resolve a single within-span information demand.',
        'selected_action':'Prepare a bounded repair plan for demand and truth-oriented readout annotation on the existing C1 cohort. Resolve compound spans into source-specific subgoals and establish mechanically valid paired transition/hold readouts before any new causal experiment.',
        'preserve':'Retain current cohorts/splits, all negative C1/C2 evidence, failed attempts, and existing thresholds. Re-annotation of already inspected traces supplies repair evidence, not fresh confirmation by itself. Any subsequent confirmatory assessment must remain independent of repair decisions and tuning.',
        'why_other_options_do_not_qualify':{
            'Mechanism-Guided Failure Rescue':'No 24 coherent fresh error-linked confirmation events or matched intervention/control prediction.',
            'Causal Meaning of Text↔Visual Alignment':'C2 does not strongly establish the required dissociation.',
            'Targeted Natural Failure Extension':'Controlled mechanism signatures are not strong enough for natural sample size to be the main remaining gap.'},
        'why_repair_is_justified':'The primary dynamic assay cannot identify its stable-demand comparison or geometric-error linkage. C1/C2 mixed results alone do not justify rerunning or repairing a valid assay.',
        'stop':'Stage6B ends here. A new approved plan is required before implementing this recommendation.'}
    write_json(OUT/'summaries/next_stage_recommendation.json',recommendation)
    (OUT/'summaries/next_stage_recommendation.md').write_text(
        '# Next-stage recommendation\n\n**GO — Cohort/Assay Repair.**\n\n'+recommendation['selected_action']+'\n\n'+
        recommendation['primary_underidentification']+'\n\n'+recommendation['why_repair_is_justified']+'\n\n'+
        recommendation['preserve']+'\n\n'+recommendation['stop']+'\n')
    criteria=[
        ('Canonical A6000 exact scoring','audit/canonical_path_audit.json'),
        ('Unchanged Stage6A splits','audit/split_integrity.json'),
        ('C2 source roles frozen before scoring','audit/c2_source_readout_freeze.json'),
        ('All 31 C2 families retained','c2_alignment_retrieval/claim_assessment.json'),
        ('C1 same fixed textual prefix','audit/fixed_prefix_replay_audit.json'),
        ('Target/sham mechanical isolation','audit/stress_condition_audit.json'),
        ('Independent counterfactual semantics','c1_mirage/counterfactual_followability.json'),
        ('W2 primary source assay','config/stage6b_config.json'),
        ('W8 predeclared sensitivity','config/stage6b_config.json'),
        ('Discovery-frozen mirage rule applied unchanged','config/mirage_discovery_rule.json'),
        ('Semantic-only dynamic selection','audit/dynamic_readout_coverage_diagnostic.json'),
        ('Dynamic sampling frozen before scoring','c1_dynamics/transition_pairs.jsonl'),
        ('Causal source states define dynamic labels','c1_dynamics/wandering_fixation_classes.jsonl'),
        ('No error-promoting claim without oriented contrast','audit/readout_orientation_audit.json'),
        ('Discovery-only PCA fit','trajectory/pca_discovery.json'),
        ('Confirmation projection only','trajectory/pca_confirmation_projection.jsonl'),
        ('Original-space trajectory metrics','trajectory/trajectory_metrics.jsonl'),
        ('No automatic C3 mask hallucination label','c3_object_stress/replication_assessment.json'),
        ('C4 exploratory at frozen sample size','c4_natural_validation/exploratory_effects.json'),
        ('No rescue/substitution/sink intervention','analysis/rescue_readiness.json'),
        ('Exactly one next-stage recommendation','summaries/next_stage_recommendation.json')]
    figures=sorted(OUT.joinpath('analysis/figures').glob('[0-9][0-9]_*.json'))
    assert sorted(read_json(p)['number'] for p in figures)==list(range(1,25))
    for p in figures:
        f=read_json(p);assert (p.parent/f['png']).is_file() and (p.parent/f['pdf']).is_file()
    for _,path in criteria:assert (OUT/path).is_file()
    write_json(OUT/'summaries/stage6b_acceptance.json',{'technical_status':'PASS','criteria_count':21,
        'criteria':[{'number':i,'criterion':name,'status':'PASS','evidence':path,'sha256':sha(OUT/path)} for i,(name,path) in enumerate(criteria,1)],
        'figure_categories':24,'scientific_gates_need_not_pass_for_technical_acceptance':True,
        'dynamic_panel_status':'Below minimum; mandatory descriptive fallback used.',
        'all_native_events':1199,'all_native_endpoints':14906,'failed_attempts_preserved':True,
        'CPU_validation':read_json(OUT/'audit/cpu_checks_final.json'),
        'policy_exception':read_json(OUT/'audit/cache_configuration.json'),
        'no_new_allocation':resources['new_slurm_allocations']==0})
    c3present=read_jsonl(OUT/'c3_object_stress/present_object_scores.jsonl')
    behavior={cond:dict(Counter(r['native_answer'] for r in c3present if r['condition']==cond)) for cond in ['intact','strong','mask','no_image']}
    lines=['# Stage6B summary','',
        '**Complete: 21/21 technical criteria pass. The broad failure-mechanism claims are not established.** All work used the existing two RTX A6000GPUs in Slurm110860/node03/tmux9; no new allocation or dataset download.','',
        'This stage tests whether visual engagement and movement track task-demanded causal evidence, and whether degraded evidence produces mirage or source-tracking failures.','',
        'W2 and W8 suppress source contributions at the last two or eight query positions. VSD measures the resulting change in the predeclared mean candidate log-probability contrast, in nats per token; it measures local source necessity rather than the time of initial acquisition.','',
        '| Completed component | Coverage |','|---|---|',
        '| C2factorial source assay |31families,124events |',
        '| C1fixed-prefix stress |109bases,1199condition events |',
        '| C1exact dynamics |20bases,78anchors,34primary transitions,0matched holds,19selected refreshes |',
        '| C1native passive / geometry |1199traces,14906endpoints; manual and programmatic scopes kept separate |',
        '| C3object stress |63present +73absent families,660native readouts |',
        '| C4natural validation |10cases +10controls,358endpoints including45predeclared wrong-claim anchors |','',
        '## Findings','',
        'C2focal-source necessity increases with focal demand: confirmation W2median1.426,18/19positive,Holmp=.000793; W8median1.063,17/19positive,p=.001099. The disjoint-ROI sensitivity remains positive14/14. Expected alignment attention/QK effects and matched high-attention yield fail the full gate (only1eligible confirmation match). All four cells demand some visual source; this does not establish global image independence. [Evidence](../c2_alignment_retrieval/claim_assessment.json).','',
        'C1strong and mask grounding losses survive matched sham controls: held-out sham-minus-stress VSD medians1.688 and2.719;57/62 and58/62bases are positive. All62confirmation bases validate the semantic counterfactual beyond render sham. There are9strict mirage candidates across8/62bases (7independent source groups), and all9also collapse underW8. The post-label preferences are4benign and5error-associated; these are fixed-prefix candidate preferences, not newly generated native hallucinations. Continuous divergence does not satisfy the full75%positive-base robustness rule, so the broad mirage claim remains unsupported. [Evidence](../c1_mirage/claim_assessment.json).','',
        'Dynamics provide9held-out demand-aligned switches and7mixed comparisons in the selected transition/refresh set. The minimum panel gate fails. There is no matched-hold test of wandering, no strictly identified fixation in the selected panel, and no cohort failure-rate estimate. Selected numeric claims are correct even when geometric roles are wrong; the numeric contrast cannot establish causation of geometric errors. First observed dominance is not an acquisition time. [Evidence](../c1_dynamics/demand_coupling.json).','',
        f"Native geometry uses{geometry['discovery_rows']}manually reviewed intact discovery endpoints from{geometry['discovery_bases']}bases in{geometry['training_source_groups']}source groups. PC1/PC2 explain{geometry['explained_variance_ratio'][0]:.1%}/{geometry['explained_variance_ratio'][1]:.1%}of discovery variance. Confirmation is projection-only; original11-dimensional path metrics are also saved. Extraction covers1766manual-prefix,18other reviewed and13122conservative programmatic endpoints;125216unreviewed unresolved spans remain outside the labeled endpoint panel, and{coverage['zero_endpoint_traces']}traces have zero eligible endpoints. Sparse causal coverage prevents a cohort-level superiority claim for demand coupling. [Evidence](../trajectory/pca_discovery.json).",'',
        f"In the frozen native traces, mask conditions average{native_meta['mask']['mean_tokens']:.0f}generated tokens versus{native_meta['intact']['mean_tokens']:.0f}for intact. {native_meta['mask']['truncated']}/109mask traces and{native_meta['sham_mask']['truncated']}/109sham-mask traces reach the cap; all109intact traces finish with EOS. These are descriptive native adaptations, not causal failure-mode labels. [Native condition summary](../c1_mirage/native_condition_summary.json).",'',
        f"C3does not pass the full replication gate for sham-controlled target-VSD degradation or continuous divergence. There are{c3['confirmation_mirage_like_candidates']}held-out mirage-like candidates. Across63present-object bases, native Yes answers number{behavior['intact'].get('yes',0)}for intact,{behavior['strong'].get('yes',0)}for strong,{behavior['mask'].get('yes',0)}for mask and{behavior['no_image'].get('yes',0)}for no-image. Each condition uses its own native prefix; final-readout W2 does not measure earlier acquisition. Mask+yes is not automatically hallucination. One absent-reference yes remains an unresolved stools/chairs category boundary, and neither tested distractor shows the joint error-promoting direction. [Evidence](../c3_object_stress/replication_assessment.json).",'',
        'C4reports matched passive effect sizes and individual cases only. In the5confirmation pairs, visual-mass/sink/entropy directions match the frozen controlled descriptor in1/5,2/5and3/5pairs; all three mean-effect confidence intervals include zero. Its wrong-claim anchors do not provide the missing truth-oriented causal source contrasts. Global descriptor trends do not establish strict mirage, wandering or fixation replication. No natural cohort extension or new prevalence claim was made. [Cases and controls](../c4_natural_validation/individual_cases.md).','',
        f"Across8strict-candidate bases in7source groups, sink mass is lower than intact by a mean{-sink_confirmation['mirage_minus_intact_sink']['mean']:.4f}. The signed candidate-minus-intact95%bootstrap interval is[{sink_confirmation['mirage_minus_intact_sink']['bootstrap_mean_ci95'][0]:.4f},{sink_confirmation['mirage_minus_intact_sink']['bootstrap_mean_ci95'][1]:.4f}]. After the declared discovery-only control for global visual mass and entropy, the signed mean is{sink_confirmation['generic_attention_controlled']['mean']:.4f}, with interval[{sink_confirmation['generic_attention_controlled']['bootstrap_mean_ci95'][0]:.4f},{sink_confirmation['generic_attention_controlled']['bootstrap_mean_ci95'][1]:.4f}]. These selected-case associations do not identify sink mediation or a causal behavioral prediction; the future-sink gate remains closed. [Sink statistics](../sink/sink_descriptive_statistics.json).",'',
        'Dataset and leave-one-dataset analyses preserve frozen thresholds. Grounding losses remain robust in every leave-one-dataset-out comparison. Attention divergence passes the secondary MathVision subgroup gate (19/21positive bases,13source groups,Holmp=.0281), but not MathVerse/MathVista or any leave-one-dataset-out gate. Validated template-family labels are absent, so template-family robustness remains unidentified. No surrogate, rescue, training, representation substitution, head search or sink intervention was run.','',
        '## Validation and execution limits','',
        'Exact native/no-op/passive controls, independent source arithmetic, frozen splits, readout orientation and mechanics-to-primary replay checks pass. BF16 weights and the canonical maximum2048-token chunk/8-query barrier path are preserved. A long-prefix OOM required CPU residency for inactive caches and expandable allocator segments; the focused allocator comparison matched18common-prefix logits, and10long-context endpoints matched fresh canonical roots and all cached layers on both GPUs. Failed attempts remain available. [Audit](../audit/causal_score_replay.json) · [Resources](../audit/resource_summary.json).','',
        'Two cache-path exceptions are recorded in the resource audit: early Matplotlib imports may have used the default external cache, and pytest updated the project-root cache outside the allowed write list. Later plotting uses the allowed project cache, and the documented test reproduction command specifies an allowed cache directory. The existing pytest cache was left untouched after read-only verification; no external cache path was inspected or cleaned. [Cache audit](../audit/cache_configuration.json).','',
        '## Next stage','',
        '**GO — Cohort/Assay Repair.** Repair the primary dynamic demand/readout panel on the existing C1cohort: resolve compound subgoals and obtain valid paired transition/hold and error-oriented readouts. This addresses an identification gap; retain all current negative and mixed findings. No failure class meets the24-event rescue gate, C2does not strongly establish alignment/retrieval dissociation, and natural sample size is not the main missing evidence. [One recommendation](next_stage_recommendation.md).','',
        'Stage6B stops here. [Technical acceptance](stage6b_acceptance.json) · [All24figure categories](../analysis/figures/index.md) · [Paper-claim assessment](../analysis/paper_claim_assessment.json) · [Rescue readiness](../analysis/rescue_readiness.json).']
    import re
    text='\n'.join(lines).replace('[All24figure categories]','[All 24 figure categories]')+'\n'
    # Keep Markdown link targets intact while spacing compact stage/quantity prose.
    chunks=re.split(r'(\[[^\]]*\]\([^)]*\))',text)
    for i in range(0,len(chunks),2):
        prose=chunks[i].replace('Stage6B','STAGE_SIX_B')
        prose=re.sub(r'(?<=[a-z])(?=\d)|(?<=\d)(?=[A-Za-z])',' ',prose)
        prose=prose.replace('%of','% of').replace('underW8','under W8')
        prose=re.sub(r'([,;])(?=\S)',r'\1 ',prose)
        prose=re.sub(r'%(?=[A-Za-z])','% ',prose)
        prose=prose.replace('mean is-','mean is -')
        chunks[i]=prose.replace('STAGE_SIX_B','Stage6B').replace('Holmp','Holm p')
    text=''.join(chunks)
    (OUT/'summaries/stage6b_summary.md').write_text(text)
    print('Stage6B technical acceptance PASS; one Cohort/Assay Repair recommendation; STOP.')


if __name__=='__main__':main()
