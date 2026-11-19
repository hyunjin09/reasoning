"""Write the reviewed reduced-sweep decision; never launch its recommendation."""
import json
from datetime import datetime
from pathlib import Path
import hashlib

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
O = ROOT / 'outputs/stage7a_bench_v2'
ORDER = ['phantom_0', 'mmmu_pro', 'charxiv', 'mmlongbench_doc', 'mathvision_wild']
NAMES = dict(phantom_0='Phantom-0', mmmu_pro='MMMU-Pro', charxiv='CharXiv',
             mmlongbench_doc='MMLongBench-Doc', mathvision_wild='MathWild')
ROLES = dict(phantom_0='No valid source', mmmu_pro='Prior-fill bridge',
             charxiv='Source confusion', mmlongbench_doc='Document source confusion',
             mathvision_wild='Degraded extraction')

def read(path):
    return json.loads(path.read_text())

def ref(path):
    return dict(path=str(path.relative_to(ROOT)), sha256=hashlib.sha256(path.read_bytes()).hexdigest())

def write(path, value):
    if path.exists():
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value if isinstance(value, str) else json.dumps(value, indent=2, ensure_ascii=False)+'\n')

def metric(m):
    if not m or m['value'] is None:
        return 'N/A'
    return f"{m['numerator']}/{m['denominator']} ({100*m['value']:.1f}%); {m['unknown']} unknown"

def main():
    ap = O/'analysis/reduced_sweep_complete_accounting_v20.json'
    cp = O/'analysis/comparison_batches/reduced_sweep_complete_v20/benchmark_comparison.json'
    a = read(ap); c = read(cp); rows = {r['benchmark']: r for r in a['rows']}
    assert a['status'] == 'COMPLETED_REDUCED_SWEEP_ACCOUNTING'
    assert a['totals']['causal_pilot_events'] == 187
    assert a['totals']['certified_state_events']['WRONG_SOURCE_READ'] == 3
    assert rows['mmlongbench_doc']['strong_unfaithful_events'] == 2
    assert rows['charxiv']['strong_unfaithful_events'] == 1
    assert sum(r['strong_unfaithful_events'] or 0 for r in rows.values()) == 3
    now = datetime.now().astimezone().isoformat()
    sources = dict(accounting=ref(ap), raw_comparison=ref(cp),
        case_validity=ref(O/'audit/mmlong_certified_case_validity_review_v25.json'))
    costs = {}
    for bid, r in rows.items():
        g = r['gpu_cost']; p = g['pilot_accounting']
        costs[bid] = p['accounted_gpu_hours'] if p else g['native_generation_gpu_seconds']/3600
    native_path = O/'native_screen/reports/mmlong_pilot_bound_native_v18/report.json'
    native_cost = read(native_path)['cost_accounting']
    mmlong_overhead = native_cost['wrapper_gpu_hours']-native_cost['successful_native_outer_gpu_hours']
    mmlong_with_wrappers = costs['mmlongbench_doc']+mmlong_overhead
    evidence = {
        'mmlongbench_doc': 'Two strong wrong-source events from two document families; seven strong faithful controls. Highest captured failure yield, with expensive document scoring and only three alternative-control failure events.',
        'charxiv': 'One strong wrong-source event, six strong faithful and25 weaker faithful;32 unresolved. Preserved low-yield evidence; lower accounted cost per captured strong failure than MMLong.',
        'mathvision_wild': 'Semantic gate A passed, but48-event pilot captured no strong unfaithful state; three strong faithful controls. Paired response changes do not certify matched-demand extraction failures.',
        'mmmu_pro': 'Best retained behavioral bridge: three image-availability conditions and one certified image-present faithful read. No source-null PRIOR_FILL certificate was tested.',
        'phantom_0': 'Completed extreme absent-source behavioral reference; no visual faithful-control or source-localized causal pilot.'}
    for track, order in [('a', ['mmlongbench_doc','charxiv','mathvision_wild']),
                         ('b', ['mmmu_pro','phantom_0'])]:
        write(O/f'analysis/track_{track}_ranking.json', dict(status='REVIEWED_DESCRIPTIVE_RANKING',
            recorded_at=now, track=track.upper(), evidence_leader=order[0],
            ordering_scope='Captured mechanistic evidence and usable controls, not accuracy or an invented scalar score. Track B ordering is bridge utility, not certified PRIOR_FILL yield.',
            rows=[dict(rank=i+1, benchmark=b, rationale=evidence[b], primary_gate_demonstrated=False) for i,b in enumerate(order)],
            primary_expansion_selected=False, sources=sources))
    extrapolations = []
    for bid in ['charxiv','mmlongbench_doc']:
        n = rows[bid]['certified_source_faithfulness_failures']; factor = 24/n
        extrapolations.append(dict(benchmark=bid,observed_strong_failures=n,
            observed_failure_source_families=rows[bid]['state_counts']['WRONG_SOURCE_READ']['certified_source_families'],
            illustrative_scale_factor=factor,illustrative_frozen_bases=200*factor,
            illustrative_accounted_gpu_hours=costs[bid]*factor,
            illustrative_gpu_hours_with_recorded_native_wrappers=mmlong_with_wrappers*factor if bid=='mmlongbench_doc' else None,
            qualification='Mechanical linear extrapolation from one/two captured failure families; not a prevalence estimate, yield prediction or demonstrated feasible cohort. Annotation and some overhead remain unknown.'))
    decision = dict(status='REVIEWED_REDUCED_SWEEP_DECISION',recorded_at=now,
        outcome='O6_NO_SCALABLE_NATURAL_PRIMARY_DEMONSTRATED',primary_natural_benchmark=None,
        empirical_reference_family='mmlongbench_doc',
        exactly_one_recommendation='Controlled Confusable-Source Construction',
        recommendation_executed=False,primary_gate_demonstrated=False,
        rationale='The sweep identifies three strong wrong-source events across three families, but does not establish a feasible route to24 strong failures within one natural benchmark. Preserve MMLong as the strongest observed reference; prioritize guaranteed source/readout/control identifiability in a separately approved controlled construction.',
        strongest_objection='Two of the three MMLong failure events with alternative semantic controls certify WRONG_SOURCE_READ. Limited control preparation could be the main yield bottleneck; a larger natural cohort could outperform this small sample. These data cannot establish intrinsic benchmark poverty.',
        reconciliation='Keep the two positive cases and the uncertainty. Do not infer a reliable yield or expand based on effects. A controlled construction directly addresses source/control availability; its relevance to natural failures must remain anchored to the verified natural cases.',
        original_primary_gate=read(O/'config/ranking_rules.json')['primary_gate'],
        gate_interpretation='At least24 strong failures at feasible scale is not demonstrated. Each image pilot retains27–32 claim-level faithful-control candidates, but candidate, Tier2 and Tier1 controls remain distinct. No new hard budget or observed-24-only gate was introduced.',
        scale_checks=extrapolations,sources=sources)
    write(O/'analysis/selected_benchmark.json',decision)
    write(O/'analysis/paper_value_assessment.json',dict(status='REVIEWED',sources=sources,
        mechanistic_value='Direct natural examples of wrong-field and wrong-dataset source binding, plus certified faithful controls under the same unchanged state definitions.',
        paper_claim='This fixed model and bounded preparation protocol produced few captured strong source-faithfulness failures. It does not establish their natural prevalence or rule out prior-filled/extraction states.',
        intervention_relevance='Known T/X identities and oriented local readouts make controlled source-confusion an interpretable future monitor/intervention target. No monitor readiness or intervention benefit is demonstrated.',
        decision=decision))
    efficiency=[]
    for bid in ORDER:
        r=rows[bid]; n=r['certified_source_faithfulness_failures']; f=r['event_readout_source_feasibility']
        efficiency.append(dict(benchmark=bid,accounted_gpu_hours=costs[bid],
            recorded_native_wrapper_adjusted_gpu_hours=mmlong_with_wrappers if bid=='mmlongbench_doc' else None,
            certified_source_failures=n,strong_failures_per_pilot_event=r['strong_unfaithful_events_per_pilot_event'],
            strong_failures_per_100_reviewed_native_conditions=r['strong_unfaithful_events_per_100_reviewed_native_conditions'],
            strong_failures_per_100_frozen_native_bases=r['strong_unfaithful_events_per_100_frozen_native_bases'],
            strong_failures_per_32_selected_failure_candidates=32*n/f['selected_counts']['failure'] if f else None,
            annotation_burden=r['annotation_burden'],annotation_minutes_per_strong_failure=None))
    write(O/'analysis/efficiency.json',dict(status='COMPLETED_ACCOUNTING_WITH_LIMITS',rows=efficiency,
        accounted_gpu_hours_total=sum(costs.values()),total_with_recorded_mmlong_native_wrapper_overhead=sum(costs.values())+mmlong_overhead,
        scope='Measured native generation plus pilot/mechanics. MMLong also reports known native wrapper/startup/OOM overhead separately. Allocation reservation, full annotation and some diagnostics/overhead are not complete-pipeline costs.',
        sources={**sources,'mmlong_native_cost':ref(native_path)}))
    write(O/'analysis/failure_state_yield.json',dict(totals=a['totals'],rows=[{k:r[k] for k in
        ['benchmark','causal_pilot','state_counts','strong_faithful','certified_source_faithfulness_failures','candidate_anomaly_flags_nested_within_unresolved','frozen_state_assay_coverage','frozen_semantic_control_coverage']} for r in a['rows']],sources=sources))
    write(O/'analysis/source_identifiability_comparison.json',dict(rows=[{k:r[k] for k in
        ['benchmark','source_identifiability','structural_readout_feasibility','event_readout_source_feasibility','counterfactual_editability']} for r in a['rows']],sources=sources,
        scope='Output-blind structural scores and bounded prepared-event yields are separate. Unprepared native errors are unassessed, not ineligible.'))
    write(O/'analysis/bclean_comparison.json',dict(sources=sources,
        behavioral_partitions=dict(some_absent_correct=17,both_absent_wrong=25,unknown=22,image_correct_both_absent_wrong=19),
        paired_mmmu_bases=64,paired_phantom_bases=200,causal_bclean_established=False,
        absent_image_prior_fill_certificate_tested=False,
        scope='Local single-model semantic partitions, not published multi-model B-Clean labels. No-image correctness and unsupported visual claims are behavior, not causal PRIOR_FILL.'))
    write(O/'analysis/benchmark_comparison.json',dict(status='REVIEWED_COMPLETED_REDUCED_COMPARISON',
        sources=sources,track_a=ref(O/'analysis/track_a_ranking.json'),track_b=ref(O/'analysis/track_b_ranking.json'),
        decision=ref(O/'analysis/selected_benchmark.json'),efficiency=ref(O/'analysis/efficiency.json'),
        note='The linked immutable raw snapshot intentionally assigns no ranking. This review index records the completed interpretation.'))
    recommendation='''# Next-stage recommendation

**Controlled Confusable-Source Construction — proposal only; STOP.**

Use the verified MMLong table-field error as the natural reference for a separately approved construction with explicit demanded source T, confusable alternative X, faithful controls, valid error-oriented local readouts and matched semantic/sham controls. Keep the4B model and strict state definitions as the comparison reference. Do not begin construction, a new cohort, another benchmark/model, monitor training, rollback or decoding intervention under this completed stage.

MMLong leads observed wrong-source yield (two events/two document families), followed by CharXiv(one). This is useful positive mechanistic evidence, but no natural benchmark has demonstrated the planned scalable strong-failure gate. Limited semantic-control coverage is a competing explanation for low captured yield; the sweep does not prove that natural benchmarks intrinsically lack failures. The construction is recommended to make source/control identifiability explicit, with natural relevance checked against the preserved cases.

The full ranking, illustrative scale/cost checks and strongest objection are recorded in `analysis/selected_benchmark.json` and `analysis/paper_value_assessment.json`. Exactly one research action is recommended; none is executed.
'''
    write(O/'summaries/next_stage_recommendation.md',recommendation)
    lines=['# Stage7A-Bench v2 — reduced sweep','',
        '**Status: reporting complete; final figure/acceptance verification pending.**','',
        'The reduced sweep contains1,382 reviewed native conditions from1,392 frozen conditions/1,000 base IDs (990 bases with responses). Four fixed pilots contain187 events:17 strong faithful,66 weaker faithful,3 strong WRONG_SOURCE_READ and101 unresolved. The three strong failures belong to three different native bases/source families. No additional benchmark or downstream intervention was started.','',
        'Phantom and CharXiv are preserved. MathWild passed the unchanged96-review semantic gate A with19 localizable candidates/12 bases and completed only its original264-condition sample. MMMU and MMLong are complete. MathSight, MicroVQA and MedXpertQA-MM remain deferred; their historical artifacts and original broader plan remain preserved.','',
        '## Native screening','',
        'Accuracy is source-reviewed final correctness among adjudicated responses, not official full-test accuracy. Unknowns remain explicit. Local errors and whole-response F0 controls are separate from causal certification.','',
        '| Benchmark / condition | Reviewed / frozen | Final accuracy | Local visual/source errors | Binding errors | F0 candidates |',
        '|---|---:|---|---|---|---:|']
    for bid in ORDER:
        for cond,v in rows[bid]['conditions'].items():
            m=v['metrics']; f=m.get('f0_candidate')
            lines.append(f"| {NAMES[bid]} / {cond} | {v['reviewed']}/{v['frozen']} | {metric(m['final'])} | {metric(m['local_error'])} | {metric(m.get('binding_error'))} | {f['numerator'] if f else 'N/A'} |")
    lines += ['', 'MMLong exclusions: five runtime OOMs, two missing PDFs and three context-limit exclusions. All190 generated responses, including seven capped traces, were fully reviewed. Complete pre-cap local claims may remain eligible under the frozen rules. Final-accuracy identification bounds and all condition-specific unsupported-claim counts are retained in the linked accounting.','',
        '## Causal yield and source/readout feasibility','',
        '| Benchmark | Pilot events / bases / families | Strong faithful | Weaker faithful | Strong wrong-source | Unresolved | Strong failures /100 reviewed conditions | Strong failures /pilot event | Accounted GPUh |',
        '|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for bid in ORDER:
        r=rows[bid]; p=r['causal_pilot']; st=r['state_counts']
        if not p:
            lines.append(f'| {NAMES[bid]} | N/A | N/A | N/A | N/A | N/A | N/A | N/A | {costs[bid]:.2f} |');continue
        strong=st['FAITHFUL_READ']['certified_events']; weak=st['FAITHFUL_READ']['events']-strong
        lines.append(f"| {NAMES[bid]} | {p['events']}/{p['native_bases']}/{p['source_families']} | {strong} | {weak} | {st['WRONG_SOURCE_READ']['certified_events']} | {st['UNRESOLVED']['events']} | {r['strong_unfaithful_events_per_100_reviewed_native_conditions']:.3f} | {r['strong_unfaithful_events_per_pilot_event']:.4f} | {costs[bid]:.2f} |")
    lines += ['', 'All four pilots have zero assigned PRIOR_FILL, STALE_SOURCE_READ, SOURCE_COUPLED_EXTRACTION_ERROR, DOWNSTREAM_INTEGRATION_ERROR and SOURCE_ANOMALY states. These zeros describe captured labels, not fully tested state absence. Candidate anomaly flags(3 CharXiv,8 MathWild,2 MMMU,5 MMLong) remain nested within unresolved outcomes. Full raw/certified state counts and base/family nesting are in `analysis/failure_state_yield.json`.','',
        'Strong-failure yield per100 frozen native bases is0.5 for CharXiv and1.0 for MMLong; MathWild/MMMU are0 and Phantom is N/A. MMLong’s per-reviewed-condition yield uses190 responses; its frozen-base denominator remains200. Repeated event, base and source-family counts are not interchangeable.','',
        '| Benchmark | Prepared / eligible / selected events | Selected failure / faithful candidates | Localized T / X / valid value readouts | Failure events with T / X semantic-sham pairs |',
        '|---|---:|---:|---:|---:|']
    for bid in ['charxiv','mathvision_wild','mmmu_pro','mmlongbench_doc']:
        r=rows[bid]; f=r['event_readout_source_feasibility']; sc=r['frozen_semantic_control_coverage']['strata']['failure']
        lines.append(f"| {NAMES[bid]} | {f['prepared_events']}/{sum(f['eligible_counts'].values())}/{f['pilot']['events']} | {f['selected_counts']['failure']}/{f['selected_counts']['faithful']} | {f['demanded_source_localized']['events']}/{f['alternative_source_localized']['events']}/{f['valid_value_readouts']['events']} | {sc['with_target_semantic_sham']['events']}/{sc['with_alternative_semantic_sham']['events']} |")
    lines += ['', 'The source-reviewed prepared pools are bounded; unprepared errors are unassessed. Eligible failure readouts are correctly oriented before scoring. Semantic/sham availability does not itself establish followability or certify a state. MMLong’s15 failure events span11 bases/10 families; its three alternative-control failures span two bases/families. All42 selected MMLong events have localizable sources and valid value readouts; most native document errors were not exhaustively prepared.','',
        '## What the retained axes establish','',
        '- **Prior/no-valid-source:** Phantom has four unsupported silent-no-image claims/200 bases and none in explicit guess mode; all four switch to abstention. MMMU preserves200 image-present responses plus64 silent and64 explicit conditions; specific absent-image F3 claims occur4/64 silent versus1/64 explicit. Its local17/25/22 behavioral partition and19 image-correct/both-absent-wrong pairs are not causal B-Clean. All187 selected pilot events have intact targets, and no absent-image PRIOR_FILL certificate was tested. This axis remains behavioral/selection-feasibility evidence.','',
        '- **Source confusion:** CharXiv retains exactly1 strong wrong-source,6 strong faithful,25 weaker faithful and32 unresolved. MMLong adds2 strong wrong-source cases: a3M table fair-value total of132 is replaced by the gross-notional field2,277; HOVER4/ProgramFC recall49.93% is replaced by the FEVEROUS-S bar85.65%. Alternative suppression reduces wrong-value preference, and alternative semantic edits move the readout beyond matched sham. One is a document table-field error; the other is a chart binding error inside a document. Their source sheets and signed W2/W8/control effects were reviewed in `audit/mmlong_certified_case_validity_review_v25.json`.','',
        '- **Degraded extraction:** MathWild passed its semantic gate but its48-event pilot captured no strong unfaithful state. Complete64-base pairing shows9 response-level clean-correct→photo-local-error changes and6 reverse changes; these may involve different claims/sources and are not matched-demand causal transitions. The gate and48-event selection were not expanded after effects.','',
        '## Cost, ranking and decision','',
        f'Accounted native generation plus causal science/mechanics totals{sum(costs.values()):.2f} GPUh. Including separately recorded MMLong native wrapper/startup/OOM overhead raises that to{sum(costs.values())+mmlong_overhead:.2f} GPUh (MMLong{mmlong_with_wrappers:.2f} versus{costs["mmlongbench_doc"]:.2f} in the comparable accounted column). MMLong causal science sums two one-GPU worker runtimes; it is not two-worker wall time. Full-pipeline overhead and annotation minutes are incomplete. Review burden is1,382 responses,187 selected events and110 unique local-control images; MMLong alone has2,122,005 reviewed response characters and about135 documented agent review minutes, excluding some source/control preparation. This is not measured human labor.','',
        'Track A evidence order: MMLong, CharXiv, MathWild. Track B behavioral-bridge order: MMMU, Phantom; no causal PRIOR_FILL winner is established. MMLong leads captured failures, while CharXiv is cheaper per captured failure. Accuracy does not determine either ordering. Two MMLong failures would require a12-fold linear scaling to reach24 if yield stayed unchanged; that illustrative calculation costs about442 accounted GPUh, or499 with recorded native wrapper overhead, before unknown annotation/other costs. The extrapolation from two failure families is not an established feasible cohort. No natural primary benchmark is frozen for expansion.','',
        '**Exactly one recommendation: Controlled Confusable-Source Construction**, anchored to the verified MMLong table-field case. Limited control preparation could be a major yield bottleneck, so this is not a claim that natural failures are intrinsically rare. The proposal makes T/X/readout/control identifiability explicit while preserving a natural reference. See `next_stage_recommendation.md`; no recommended work has begun.','',
        '## Verification and limits','',
        'The replacement allocation114451 used two node02 A6000 GPUs in tmux10. The unchanged42-event MMLong seal completed, including both199k-token cases. Exact KV/logit/RoPE and original source/candidate/no-op/repeat mechanics passed on both devices against the immutable native document backend. The earlier dense-versus-document full-tensor comparison failed and remains preserved; dense-document tensor equivalence is not claimed. BF16 input conversion/cache residency repairs retain full pages, readouts and inherited causal definitions.','',
        'Historical embedded annotation status strings such as “bank pending” or “pilot_selected:false” are preparation snapshots; the outer frozen pilot and hash-bound control-review receipts govern executed membership/control availability. They were not rewritten. Early CPU reporting commands omitted explicit cache/temp environment binding; external effects were not inspected or verified. Later commands bind allowed project paths. Dataset lookup/download provenance is preserved separately.','',
        'Detailed limits: `reduced_sweep_interpretation_limits_v20.md`. Raw A–J dimensions, nested accounting, rankings, coverage and costs are indexed in `analysis/benchmark_comparison.json`. Final figure coverage and the23 technical criteria are recorded in `stage7a_bench_v2_acceptance.json`.','']
    write(O/'summaries/stage7a_bench_v2_summary.md','\n'.join(lines))
    dest=O/'analysis/figures/decision_batches/reduced_decision_v25';dest.mkdir(parents=True,exist_ok=False)
    plt.rcParams.update({'font.family':'DejaVu Sans','svg.fonttype':'none','pdf.fonttype':42})
    fig,ax=plt.subplots(figsize=(17,7));ax.axis('off')
    table=[]
    for bid in ORDER:
        r=rows[bid];p=r['causal_pilot'];s=r['event_readout_source_feasibility'];sc=r['frozen_semantic_control_coverage']
        table.append([NAMES[bid],ROLES[bid],str(r['native_conditions_reviewed']),
            str(p['events']) if p else 'N/A',str(r['certified_source_faithfulness_failures']) if p else 'N/A',
            str(r['strong_faithful']['events']) if p else 'N/A',
            f"{sc['strata']['failure']['with_alternative_semantic_sham']['events']}/{s['selected_counts']['failure']}" if s else 'N/A',
            'Gate not demonstrated'])
    t=ax.table(cellText=table,colLabels=['Benchmark','Intended regime','Reviewed\nconditions','Pilot\nevents','Strong\nsource failures','Strong\nfaithful','Failure X\ncontrols','Natural primary'],
        colWidths=[.13,.21,.09,.08,.11,.09,.10,.19],cellLoc='left',loc='center')
    t.auto_set_font_size(False);t.set_fontsize(10);t.scale(1,2.8)
    for (row,col),cell in t.get_celld().items():
        cell.set_edgecolor('#d3dee5')
        if row==0:cell.set_facecolor('#dceaf1');cell.set_text_props(weight='bold')
        elif row%2==0:cell.set_facecolor('#f3f6f8')
    fig.suptitle('Reduced sweep: captured mechanistic yield and decision',x=.03,ha='left',fontweight='bold',fontsize=17)
    fig.text(.03,.83,'3 strong wrong-source events across3 families;17 strong faithful controls. No scalable natural primary established.',fontsize=12)
    fig.text(.03,.13,'Recommendation: Controlled Confusable-Source Construction, with a verified MMLong table-field reference. Proposal only; STOP.',fontsize=11,weight='bold')
    fig.text(.03,.055,'X controls = selected failure events with reviewed alternative semantic/sham pairs; availability is not certification.\nPrior-axis absence was not causally tested. Unknowns, unprepared errors and missing controls are not null effects. See the full nested accounting.',fontsize=10,color='#516473')
    fig.subplots_adjust(left=.025,right=.975,bottom=.20,top=.78)
    files={}
    for ext in ('png','pdf','svg'):
        p=dest/f'22_reduced_decision.{ext}';fig.savefig(p,dpi=160,bbox_inches='tight');files[ext]=ref(p)
    plt.close(fig)
    write(dest/'manifest.json',dict(status='RENDERED_PENDING_VISUAL_REVIEW',figure_number=22,files=files,
        source_sha256={v['path']:v['sha256'] for v in [ref(ap),ref(O/'analysis/selected_benchmark.json')]},
        renderer_sha256=ref(Path(__file__))['sha256'],rows=table,recommendation_executed=False))
    print('Decision, accounting views, summary and Figure22 written; visual/technical acceptance still required.')

if __name__ == '__main__':
    main()
