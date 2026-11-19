"""Render the Stage9A report; never label completion while controls are missing."""
import json
import shutil
from decimal import Decimal, ROUND_HALF_UP
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from scripts.stage9a_dynamics.prepare_answers import MAIN, BASE, sha
from scripts.stage9a_dynamics.analyze_main import load
from visual_reasoning.stage9a.protocol import ARMS

LABELS={'instruct_direct':'Direct','instruct_cot':'CoT','thinking':'Thinking'}
REQUIRED=['stage9a_visual_access_dynamics_spec.md','stage9a_mask_backend_validation.json',
          'stage9a_full_access_baselines.json','stage9a_cumulative_cutoff_results.parquet',
          'stage9a_local_window_results.parquet','stage9a_demand_aligned_knockout.parquet',
          'stage9a_temporal_necessity_profiles.json','stage9a_late_half_effects.json',
          'stage9a_demand_vs_control_effects.json','stage9a_attention_redistribution_control.json',
          'stage9a_primary_inference.json','stage9a_summary.md']


def write_json(path, value):
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')


def pp(value):
    if value is None:return 'NA'
    return f"{Decimal(str(100*value)).quantize(Decimal('.01'),rounding=ROUND_HALF_UP):+.2f}"


def interval(result):
    return 'withheld: <20 families' if result['ci'] is None else '['+', '.join(pp(v) for v in result['ci'])+']'


def main():
    infer=load(MAIN/'stage9a_primary_inference.json');profiles=load(MAIN/'stage9a_temporal_necessity_profiles.json')['arms']
    baseline=load(MAIN/'stage9a_full_access_baselines.json')['arms']
    local=load(MAIN/'audit/local_readouts_secondary.json')
    control_path=MAIN/'stage9a_attention_redistribution_control.json'
    control=load(control_path) if control_path.exists() else None
    complete=bool(control and control['complete'])
    now=datetime.now(timezone.utc).isoformat()
    # Main evidence already fails the positive-effect gates; controls cannot waive that.
    assert all(v['simultaneous']['ci'][0]<=0 for v in infer['primary'].values())
    assert infer['sensitivities']['P3']['leave_one_subject_out']['algebra']['mean']==0
    gates=dict(at=now,query_text_bypass=dict(triggered=False,reason='No supported Thinking-specific late necessity effect'),
        reserve_extension=dict(triggered=False,conditions={
            'P2_or_P3_hypothesized_point':True,'interval_includes_zero':True,
            'not_one_subject':False,'implementation_validation':True,
            'control_characterization_complete':complete,'precision_limited_rather_than_null':False},
            reason='P2 is negative; P3 falls to zero without algebra and to zero in the17-family scorable sensitivity. All five requirements are not met. No reserve execution.'),
        advance_stage9b=dict(triggered=False,reason='No primary late Thinking-over-CoT support; demand contrast uncertain and subject-dependent. Bounded controls cannot rescue these failed prerequisites.'),
        recommendation='Close the Thinking-specific visual-access scheduling branch; do not advance to Stage9B.',
        authorized_research_action_complete=complete)
    write_json(MAIN/'audit/gates.json',gates)
    main_status=load(MAIN/'audit/completion_status_20260926.json')
    prefix=sum(load(p)['shared_prefix_seconds'] for p in (MAIN/'rollouts/tasks').glob('*/complete.json'))/3600
    readout_hours=sum(load(p)['runtime_seconds'] for p in Path('outputs/stage9a_dynamics/v1/readouts/events').glob('*/result.json'))/3600
    control_hours=sum(load(p)['runtime_seconds'] for p in (MAIN/'controls_v1/rollouts/results').glob('*/result.json'))/3600
    control_prefix=sum(load(p)['shared_prefix_seconds'] for p in (MAIN/'controls_v1/rollouts/tasks').glob('*/complete.json'))/3600
    resources=dict(at=now,main_suffix_gpu_hours=main_status['completed_suffix_gpu_hours'],main_shared_prefix_gpu_hours=prefix,
        fixed_readout_gpu_hours=readout_hours,control_suffix_gpu_hours_so_far=control_hours,control_shared_prefix_gpu_hours_so_far=control_prefix,
        measured_model_compute_gpu_hours=main_status['completed_suffix_gpu_hours']+prefix+readout_hours+control_hours+control_prefix,
        control_matched_main_suffix_projection_gpu_hours=8.702915244114187,
        annotation=dict(main_unique_packets=1717,main_manual_packets=775,main_deterministic_terminal_checks=942,exact_native_reused_continuations=154),
        limitations='Operation timing, not billed allocation time: excludes model startup, I/O, scheduler wait, preflight, original native generation and superseded old outputs. Main suffix includes8 exact old reuse receipts. New task prefix receipts do not include historic prefix costs for those8.')
    write_json(MAIN/'audit/final_resource_accounting.json',resources)
    status='COMPLETE / STOP' if complete else 'MAIN ANALYSIS COMPLETE / CONTROLS PENDING'
    lines=[f'# Stage9A causal visual-access dynamics — {status}',f'Updated {now}.',
        'The completed64-family main study does **not support greater recurrent late direct visual-access necessity in Thinking than CoT**. This is a negative/uncertain result for the directional hypothesis, not evidence of equivalence, absence of visual processing, or a token-level visual-access boundary.',
        ('All1904 main continuations,87 frozen redistribution controls and50 teacher-forced local readouts are complete and reviewed. No reserve, query-text bypass or later-stage experiment ran.' if complete else
         'Main inference and the50 teacher-forced readouts are complete. The87 mandatory, preselected null-sink continuations remain pending/running in Slurm jobs124266–124273. The plan is **not yet finished**; their extraction review, comparison and final closure remain. Main conclusions below are sealed and will not be used to tune the control inventory.'),
        '## Frozen design and validity',
        'Three arms reuse the same frozen MathVision native inputs: Instruct Direct, one prompted CoT, and Native Thinking.64 conservative visual families were selected prospectively from128 by metadata-stratified hash allocation. All384 original native trajectories,539 semantic demands,50 readout events and12 actual-model V1–V6/cache/backend validations remain preserved. BF16, prompts, sampling, seeds and40960-token cap are unchanged.',
        'The assay masks image keys only for generated queries in decoder indices19–22. Prefill, prior KV and previously encoded image information persist; subsequent caches evolve. Cumulative cutoff, local-window knockout and demand-aligned knockout remain distinct. Local schedules use native coordinates even after divergence. Native FULL reuse is supported by backend validation and per-task native-prefix identity, not assumed cross-backend comparability.',
        'The amended panel contains2138 logical conditions:1904 unique continuations (1896 new+8 exact reused) and234 native identities (192FULL+42 unreached cutoffs). All78 completed old-manifest rows are preserved;70 superseded rows are outside primary inference. No early-stop proposal was executed. All64 reserve families remain unused.',
        '[Executed specification](stage9a_visual_access_dynamics_spec.md) · [Compute amendment](stage9a_compute_amendment_v1.md) · [Technical validation](stage9a_mask_backend_validation.json) · [Main integrity](audit/main_completion_validation_20260926.json)',
        '## Baselines, extraction and denominators',
        '| Arm | Native correct /64 | Accuracy | Wrong | Unscorable | At cap |',
        '|---|---:|---:|---:|---:|---:|']
    for arm in ARMS:
        b=baseline[arm];c=b['counts'];lines.append(f"| {LABELS[arm]} | {c.get('correct',0)}/64 | {100*b['accuracy_no_credit']:.2f}% | {c.get('wrong',0)} | {c.get('unscorable',0)} | {b['capped']} |")
    lines += ['',
        'Main extraction review was sealed before gold-based scoring:942 deterministic unambiguous-terminal packet checks,775 manual packets, and154 exact-native continuations inheriting prior review.1717 unique packets cover1750 other outputs. One Codex annotator reviewed ambiguous literal answers with candidate/context/tail and options; this is not independent human annotation. Arm/condition IDs and gold were withheld, though writing style may reveal arm. No reasoning correction or numerical answer solving was used. The unchanged Stage8B v2 adapter/tolerance scores both raw and reviewed outputs.',
        'Primary accuracy keeps all64 families per arm and treats unscorable as no credit **while retaining unscorable as a distinct label**. Scorable-only analysis is a potentially post-treatment-selected sensitivity. P3 uses28 families eligible in both Thinking and CoT; missing demand eligibility does not become zero.',
        '[Sealed review](annotations/answer_extraction_review_frozen.json) · [Raw/reviewed scores](audit/scored_answers.json) · [Completion, length and divergence](audit/continuation_secondary.json)',
        '## Primary family inference',
        'Damage=FULL accuracy−masked accuracy; positive damage means access removal harms performance. Contrasts below are Thinking−CoT, in percentage points.4,000 paired family bootstrap draws use seed920260924. The98.75% simultaneous intervals cover four scalar components in three primary groups. No condition/token/event is counted as another independent family.',
        '| Contrast | Paired families | T−C (pp) | Simultaneous CI (pp) | Positive / negative / tied families |',
        '|---|---:|---:|---|---|']
    for key,title in [('P1_512','P1: cutoff512'),('P1_2048','P1: cutoff2048'),('P2','P2: final two20% windows'),('P3','P3: demand−control')]:
        r=infer['primary'][key]['simultaneous'];d=r['family_directions']
        lines.append(f"| {title} | {r['n_families']} | {pp(r['mean'])} | {interval(r)} | {d['positive']} / {d['negative']} / {d['tie']} |")
    lines += ['',
        'None supports the hypothesized positive Thinking-specific contrast. P2 averages[.6,.8] and[.8,1.0], the final40% (called late-half in the amendment). Thinking late damage is+3.13pp versus CoT+5.47pp; the paired difference is−2.34pp. The stronger native Thinking accuracy is a baseline observation, not proof of greater visual necessity.',
        'P3 is+10.71pp on28 paired families but uncertain. Leaving out algebra reduces it to0 on21 families. Only5 paired families have a nonzero T−C demand contrast (4 positive,1 negative). This fails the no-single-subject requirement for the optional extension; it is not established as a precision-only limitation.',
        '[Primary inference and all sensitivities](stage9a_primary_inference.json) · [Family metrics](audit/family_metrics.json)',
        '## Temporal and demand profiles (descriptive)',
        '| Arm | cutoff0 | cutoff128 | cutoff512 | cutoff2048 | 0–20% | 20–40% | 40–60% | 60–80% | 80–100% |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for arm in ARMS:
        keys=[f'cutoff{c}_damage' for c in (0,128,512,2048)]+[f'local{k}_damage' for k in range(5)]
        lines.append('| '+LABELS[arm]+' | '+' | '.join(pp(profiles[arm][k]['mean']) for k in keys)+' |')
    lines += ['',
        'Values are percentage-point damage; negative values are improved correctness under the scheduled perturbation. These are descriptive and not monotone boundary estimates. Especially for Direct, sampled trajectories, looping/capping and low baseline accuracy complicate simple “less access is better” interpretations. No new prompt or assay was selected to repair these outcomes.',
        '| Arm | Eligible families | Demand damage | Shifted-control damage | Demand−control |',
        '|---|---:|---:|---:|---:|']
    for arm in ARMS:
        p=profiles[arm];lines.append(f"| {LABELS[arm]} | {p['demand_damage']['n_families']} | {pp(p['demand_damage']['mean'])} | {pp(p['control_damage']['mean'])} | {pp(p['demand_minus_control']['mean'])} |")
    lines += ['',
        'These within-arm demand profiles use34/37/38 eligible families; the primary cross-arm effect uses the28-family intersection. Shifted controls lack an accepted annotated demand and are not certified demand-free.',
        '## Sensitivity and local evidence',
        'Literal extraction matters: raw-adapter T−C at cutoff2048 is+9.38pp versus reviewed−3.13pp; raw P2 is+3.13pp versus reviewed−2.34pp. Both raw intervals include zero. No robust positive late phenotype emerges under either scoring path. The normal/certain native-boundary intersection has40 families and P2=0. Restricting native Thinking/CoT length ratio to≤2 leaves18 families, below the20-family interval threshold. Common cutoff exposure retains59 families at512 and48 at2048 and keeps negative point estimates.',
        'Scorable-complete P2 remains−1.25pp on40 families. Scorable-complete P3 is0 on17 families, with interval withheld. These restrictions do not estimate an unbiased alternative population effect. Capped native trajectories are retained in primary inference; altered stopping/extractability is part of the observed continuation behavior.',
        'All50 fixed teacher-forced events were retained:16 Direct,16 CoT,18 Thinking. Positive values below mean reduced original evidence mean log probability (nats per token). They are secondary, with no arm reaching20 families.',
        '| Arm | Events | r16 demand damage | r32 demand damage | Unexposed shifted controls | Both-exposed pairs |',
        '|---|---:|---:|---:|---:|---:|']
    for arm in ARMS:
        rr={r['radius']:r for r in local['summaries'] if r['scope']=='frozen50' and r['arm']==arm}
        r=rr[16];lines.append(f"| {LABELS[arm]} | {r['roles']['demand']['n_events']} | {r['roles']['demand']['original_mean_log_probability_damage']['mean']:.4f} | {rr[32]['roles']['demand']['original_mean_log_probability_damage']['mean']:.4f} | {r['roles']['control']['unexposed_events']} | {r['paired']['both_exposed']['n_events']} |")
    lines += ['',
        '40/50 shifted controls occur after the readout and are unexposed. Therefore the larger Thinking teacher-forced mean change is not a validated demand-specific cross-arm result. The explicit both-exposed sensitivity has only4/3/3 events. Donor-preference, sum-log-probability and main64-only summaries are retained separately; no reserve readout is added to the primary64-family denominator.',
        '[Local readouts](audit/local_readouts_secondary.json) · [Native usage comparison](audit/native_usage_secondary.json)',
        'The original128-family native-use study had0/4 supported positive primary contrasts. On the same64 families used here, usage frequency/timing and causal performance damage remain distinct summaries. Neither attention frequency nor an unperturbed correlation establishes functional necessity.',
        '## Redistribution controls']
    if complete:
        lines += ['All87 preselected null-sink continuations on8 families are complete. The same sealed extraction policy and fixed scorer were applied. Each comparison uses the exact same main family/arm/condition and baseline.',
                  '| Condition | Arm | Families | Standard damage (pp) | Null-sink damage (pp) | Null−standard (pp) |',
                  '|---|---|---:|---:|---:|---:|']
        for r in control['summaries']:
            lines.append(f"| {r['condition']} | {LABELS[r['arm']]} | {r['n_families']} | {pp(r['standard_damage']['mean'])} | {pp(r['null_sink_damage']['mean'])} | {pp(r['null_minus_standard_damage']['mean'])} |")
        lines += ['', 'The8-family bound is below the20-family threshold; all control inference is descriptive. Last20% control is not the full P2 final40% aggregate. Only selected demand, not a null-sink matched non-demand pair, was prescribed. The control set cannot establish population robustness or rescue the unsupported primary late effect.',
                  '[Redistribution comparison](stage9a_attention_redistribution_control.json)']
    else:
        lines += ['87 exact frozen rows on8 families were materialized after main inference; no effect-based representative selection. Slurm capacity is the current blocker. Matched main suffix timing projects8.70GPU-hours plus prefix/startup and uncertainty from changed continuation lengths. Queue delay is additional. All workers stop at their frozen queue boundary. No control outcome or robustness claim is available yet.']
    lines += ['', '## Gates and recommendation',
        'Query-text bypass: **not triggered** because there is no supported Thinking-specific late effect. Reserve extension: **not triggered** because P2 is negative and P3 fails subject robustness; no evidence establishes a precision-only problem. Stage9B advance: **fails** the primary late/semantic-support criteria, independently of unfinished or bounded redistribution characterization.',
        '**Exactly one recommendation: close the Thinking-specific visual-access scheduling branch; do not advance to Stage9B.**',
        'This does not reject visual grounding, recurrent visual use, or small effects the study cannot resolve. It closes the proposed distinctive late-necessity claim under these models, fixed prompt, layer window and MathVision cohort. No new experiment has been launched.',
        '## Figures and artifacts',
        '[1. Intervention schematic](figures/figure1_intervention_schematic.png) · [PDF](figures/figure1_intervention_schematic.pdf)  ',
        '[2. Cumulative necessity](figures/figure2_cumulative_necessity.png) · [PDF](figures/figure2_cumulative_necessity.pdf)  ',
        '[3. Temporal profiles](figures/figure3_temporal_necessity.png) · [PDF](figures/figure3_temporal_necessity.pdf)  ',
        '[4. Demand-aligned necessity](figures/figure4_demand_aligned_necessity.png) · [PDF](figures/figure4_demand_aligned_necessity.pdf)  ',
        '[5. Native usage vs necessity](figures/figure5_native_usage_vs_necessity.png) · [PDF](figures/figure5_native_usage_vs_necessity.pdf)',
        'All three condition tables are in the required parquet files; full baselines and primary/profile/demand/late summaries are in the required JSONs. [Artifact catalog](audit/artifact_catalog.json).',
        '## Resources and execution limits',
        f"Measured main suffix compute{main_status['completed_suffix_gpu_hours']:.2f}GPU-hours plus shared native prefixes{prefix:.2f}GPU-hours; fixed teacher-forced readouts{readout_hours:.2f}GPU-hours. Controls currently account for{control_hours+control_prefix:.2f}GPU-hours. These are operation timings, excluding startup/I/O, preflight, scheduler wait, original native generation and superseded old execution; they are not billed allocation time.",
        'Manual annotation burden was775 main packets, with942 deterministic checks and154 native-review reuses. Earlier semantic/source annotation is reused unchanged. [Accounting](audit/final_resource_accounting.json).',
        ('Research artifacts complete. Verify the final audit and absence of active/pending control jobs before recording resource closure.' if complete else
         'Remaining authorized work: finish87 controls; seal their extraction review; run analyze_controls.py; refresh this report; verify receipts, figures and resource release; update compact state; STOP. This report does not mark the stage complete before those steps.')]
    dest=MAIN/'stage9a_summary.md';archive=MAIN/'audit/summary_before_main_analysis.md'
    if not archive.exists(): shutil.copyfile(dest,archive)
    dest.write_text('\n\n'.join(lines)+'\n')
    # Markdown table rows must be consecutive, unlike prose paragraphs.
    text=dest.read_text();text=text.replace('|\n\n|','|\n|');dest.write_text(text)
    entries=[dict(path=name,exists=(MAIN/name).exists(),sha256=sha(MAIN/name) if (MAIN/name).exists() else None) for name in REQUIRED]
    entries += [dict(path=str(p.relative_to(MAIN)),exists=True,sha256=sha(p)) for p in sorted((MAIN/'figures').glob('figure*.*'))]
    write_json(MAIN/'audit/artifact_catalog.json',dict(at=now,stage_complete=complete,required_count=12,
        required_present=sum((MAIN/n).exists() for n in REQUIRED),figure_files=10,entries=entries))
    print(status)


if __name__=='__main__': main()
