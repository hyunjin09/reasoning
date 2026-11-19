#!/usr/bin/env python3
"""Regenerable reports retain numerical validity and censoring qualifications."""

import statistics
from collections import Counter
from scripts.stage3c9r.freeze_inputs import ROOT, OUT, read_json, write_json


def main():
    classification=read_json(OUT/'analysis/checkpoint_classification.json')
    source=read_json(OUT/'analysis/source_sensitivity.json')
    profile=read_json(OUT/'analysis/source_vs_rescue_2d.json')['rows']
    sensitivity=read_json(OUT/'analysis/threshold_sensitivity.json')['rows']
    lifetime=read_json(OUT/'analysis/lifetime_analysis.json')
    comparison=read_json(OUT/'analysis/stage3c9_phase_comparison.json')
    reference=read_json(OUT/'analysis/base38_reference.json')
    outcome=read_json(OUT/'analysis/scientific_outcome.json')
    acceptance=read_json(OUT/'summaries/stage3c9r_acceptance.json')
    mechanics=read_json(OUT/'audit/mechanical_validation.json')
    route=read_json(OUT/'route/route_status.json')
    necessity=read_json(OUT/'optional_necessity/gate.json')
    config=read_json(OUT/'config/stage3c9r_config.json')
    figure_index=read_json(OUT/'analysis/figures/index.json')
    runtime=[]
    condition_peaks=[]
    for directory in ['audit/raw','same_path_scores/raw','lifetime_raw','necessity_raw']:
        for p in (OUT/directory).glob('shard_*/run_summary.json'):
            runtime.append({'path':str(p.relative_to(ROOT)),**read_json(p)})
        for p in (OUT/directory).glob('shard_*/*/*/*.json'):
            row=read_json(p)
            condition_peaks.append({k:row[k] for k in ['peak_gpu_allocated_bytes','peak_gpu_reserved_bytes']})
    resource={'slurm_job_id':config['runtime']['slurm_allocation'],'node':'node07','gpus':4,
        'gpu_type':'A6000','new_allocation_requested':False,
        'peak_allocated_gib':max(r['peak_gpu_allocated_bytes'] for r in condition_peaks)/2**30,
        'peak_reserved_gib':max(r['peak_gpu_reserved_bytes'] for r in condition_peaks)/2**30,
        'memory_basis':'maximum of all saved condition-level peaks; inherited prefill resets CUDA peak statistics',
        'phase_max_rank_seconds':{role:max(r['runtime_seconds'] for r in runtime if r['role']==role) for role in {r['role'] for r in runtime}},
        'rank_runs':runtime}
    write_json(OUT/'audit/resource_summary.json',resource)
    lines=[
        '# Stage 3C.9R — Same-path validity repair', '',
        f"Technical **{'PASS' if acceptance['passed'] else 'FAIL'}**: {acceptance['passed_count']}/20 acceptance criteria; {mechanics['passed_count']}/15 mechanical gates. Scientific outcome **{outcome['outcome']}**.", '',
        outcome['claim'], '',
        f"On the unchanged 48-base, 144-event cohort, {classification['source_sensitive_events']} events were source-sensitive in at least one frozen window. There were **{classification['checkpoint_events']} distinct C2/C3 checkpoints** and **{classification['repeated_checkpoint_bases']}/48 repeated-checkpoint bases**. Classes: {classification['class_counts']}.", '',
        '## Frozen assay and repair', '',
        f"All {acceptance['event_window_rows']} mechanically valid W8/W16 event-window pairs received native, suppressed, event-span rescue and equal-width neighbor rescue in O/O_sham/C/C_sham before classification ({acceptance['primary_condition_files']} raw condition files). No cohort, span, ROI, candidate suffix or readout changed.", '',
        'Each arm used BF16 eager language attention / SDPA vision attention with 2048-token maximum chunks, allocator release and the same union of frozen event/neighbor token-end barriers. Event and neighbor rescues fork exact cache copies from the actual suppressed execution. One persisted suppressed score supplies every source-loss and rescue-gain denominator. All sham source effects were also recomputed on this path. Original Stage 3C.9 scores enter descriptive comparisons only.', '',
        'The original source directionality/sham criterion, reciprocal positive rescue, 0.05 mean effect floor, median unclipped RR >=0.25, matched-neighbor superiority, distinct-final C3 rule and >=24-token repeated-pair separation are unchanged.', '',
        '## Primary and threshold results', '',
        f"The continuous profile contains {source['source_sensitive_event_windows']} source-sensitive event-window pairs: {source['by_window']['W8']['source_sensitive']} W8 and {source['by_window']['W16']['source_sensitive']} W16. Of these, {sum(r['source_sensitive'] and not r['functional_span_rescue'] for r in profile)} do not pass the complete span-rescue rule. Descriptive high/low L/G quadrants are {dict(Counter(r['profile_type'] for r in profile))}; quadrant membership alone does not establish a checkpoint.", '',
        '| Effect floor | C2/C3 events | Repeated bases | Bases with 0 / 1 / 2 / 3 checkpoints |',
        '|---:|---:|---:|---|',
    ]
    for r in sensitivity:
        bins=r['checkpoint_count_per_base']
        lines.append(f"| {r['effect_floor']:.3f}{' (primary)' if r['effect_floor']==.05 else ''} | {r['checkpoint_events']} | {r['repeated_checkpoint_bases']}/48 | {' / '.join(str(bins[str(k)]) for k in range(4))} |")
    lines += ['', 'Sensitivity changes only the effect floor after the primary result freeze. Windows within an event never count as separate checkpoints. The combined C2/C3 counts are unaffected by final-readout upgrades. RR is descriptive and unclipped; a near-zero per-condition source loss can produce a very large ratio, so it is not a unique information fraction. Absolute source/rescue effects and their controls remain the primary evidence.', '',
        '| Per-base statistic | Mean | Median | Bootstrap 95% CI for mean | Positive fraction |',
        '|---|---:|---:|---|---:|']
    for name,r in classification['statistics'].items():
        lo,hi=r['bootstrap_mean_ci95']
        lines.append(f"| {name.replace('_',' ')} | {r['mean']:.5f} | {r['median']:.5f} | [{lo:.5f}, {hi:.5f}] | {r['positive_fraction']:.3f} |")
    lines += ['', 'The independent unit is base_problem_id. Each base contributes its event/window summary once; bootstrap sampling draws whole bases (10,000 draws, seed 12348). Event scatter plots are descriptive. A degenerate bootstrap CI for an all-zero count is an empirical resampling result and does not establish zero population prevalence.', '',
        '## Numerical comparison with the original experiment', '',
        '| Legacy path | Matched O/C cells | Median absolute source-loss difference | Gate agreement | Source-loss sign agreement |',
        '|---|---:|---:|---:|---:|']
    for phase in ['A','B']:
        r=comparison[f'vs_{phase}']
        lines.append(f"| Phase {phase} | {r['event_window_conditions']} | {r['median_absolute_source_loss_difference']:.6f} | {r['gate_agreement_count']}/{r['event_windows']} | {r['sign_agreement']:.3f} |")
    lines += ['', 'Original Phase B was pre-gated and retained Phase-A sham effects. Its gate comparison therefore includes that legacy mismatch. The repair uses its own quartet scores throughout. Mechanical validation found exact native/self-suppressed controls, deterministic replay and inherited-path comparisons; threshold sensitivity describes scientific cutoff dependence, not replay randomness.', '',
        '## Lifetime and frozen base-38 reference', '',
        f"Lifetime counts: {lifetime['phenotype_counts']}. A checkpoint with no distinct later/final readout is explicitly RIGHT-CENSORED. L-Short retains the original readout-based label; it does not establish a 16–32-token decay time when no probe exists there. L-Persistent uses the original mean-gain criterion at a distant or final probe; C3 additionally requires positive final rescue in both O and C, so those counts can differ.", '',
        '| Base / event | Window | Local G | Distinct downstream observations: distance → G | Lifetime |',
        '|---|---|---:|---|---|']
    for r in lifetime['rows']:
        for w,m in r['per_window'].items():
            probes='; '.join(f"{v['distance_from_span_end']} → {v['rescue_gain_mean']:.6f} ({v['name']})" for v in m['readouts']) or 'none'
            lines.append(f"| {r['base_problem_id']} / {r['event_id']} | {w} | {m['local_rescue_gain_mean']:.6f} | {probes} | {m['phenotype']} |")
    early=reference['repair']['events'][0]
    lines += ['',f"Base 38's frozen first event now classifies **{early['classification']}**. Its same-path W8/W16 source losses are {early['windows']['W8']['source_loss_mean']:.6f} / {early['windows']['W16']['source_loss_mean']:.6f}, and event gains are {early['windows']['W8']['rescue_gain_mean']:.6f} / {early['windows']['W16']['rescue_gain_mean']:.6f}. Its survival was never a technical PASS condition.", '',
        f"Original base-38 local G was {reference['original_local_G']:.6f}; its independently annotated readout 2342 tokens later had G={reference['original_downstream_G']:.6f}, and final G={reference['original_final_G']:.6f}. Full repair details are in [base38_reference.json](../analysis/base38_reference.json).", '',
        '## Gates and interpretation', '',
        f"Optional necessity: {'RUN' if necessity['run'] else 'NOT RUN'}; {necessity['robust_unique_checkpoints']} robust events versus 4 required. Robustness was prospectively operationalized as retaining C2/C3 at 0.15. Route decomposition: **{route['status']}**; {route['eligible_bases']} eligible repeated bases versus 16 required.", '',
        outcome['source_rescue_profile_interpretation'], '',
        'The assay tests frozen sparse semantic K/V spans under W8/W16. A negative result does not establish that visual processing or reasoning-side propagation is absent. Other acquisition windows, broader recent-token/residual state and semantic misalignment remain unresolved.', '',
        f"**Sole recommendation: {outcome['recommendation']}.** This is for review only. Stage 3C.9R stops here; no cohort expansion, Retrieval Trigger, sink intervention or Stage 4 experiment was started.", '',
        '## Execution and evidence', '',
        f"Used only the four user-provided A6000 GPUs in tmux 9 / Slurm {resource['slurm_job_id']} on node07. No additional allocation was requested. Peak per-rank allocated/reserved GPU memory was {resource['peak_allocated_gib']:.2f}/{resource['peak_reserved_gib']:.2f} GiB. Commands, versions, timing and rank assignment are saved in the raw directories and [resource_summary.json](../audit/resource_summary.json).", '',
        f"The independent audit rederived all scientific gates from raw scores and verified {acceptance['original_files_hashed']} immutable original artifact hashes. Focused regression evidence: `runs/stage3c9r_regression_tests.log`.", '',
        '- [Acceptance](stage3c9r_acceptance.json)',
        '- [Independent raw-score audit](../audit/independent_artifact_validation.json)',
        '- [Primary freeze](../analysis/primary_freeze.json)',
        '- [Continuous source/rescue profile](../analysis/source_vs_rescue_2d.json)',
        '- [All 15 figures (PNG/PDF)](../analysis/figures/index.json)', '',
    ]
    (OUT/'summaries/stage3c9r_summary.md').write_text('\n'.join(lines))
    (OUT/'summaries/next_stage_recommendation.md').write_text(
        f"# Stage 3C.9R recommendation\n\n**{outcome['recommendation']}**\n\n{outcome['claim']}\n\n"
        f"Repeated-checkpoint counts at 0.025 / 0.05 / 0.10 / 0.15: {outcome['repeated_counts_by_floor']}. "
        "This recommendation is for joint review only. No next-stage experiment is authorized or started by this report.\n")
    print('Summary and exactly one recommendation written from authoritative repair results.')


if __name__=='__main__':
    main()
