"""Publish the completed Stage 9A report; never launches another experiment."""
import json
from pathlib import Path

from scripts.stage8c.prepare import save,sha

ROOT=Path('outputs/stage9a/v1')


def fmt(value,digits=3):
    return 'undefined' if value is None else f'{value:.{digits}f}'


def interval(ci,digits=3):
    return 'not estimable (<20 families)' if ci is None else f'[{ci[0]:.{digits}f}, {ci[1]:.{digits}f}]'


def main():
    effects=json.loads((ROOT/'stage9a_primary_effects.json').read_text())
    causal=json.loads((ROOT/'stage9a_causal_validation.json').read_text())
    accuracy=json.loads((ROOT/'stage9a_accuracy_secondary.json').read_text())
    rows=json.loads((ROOT/'audit/trajectory_metrics.json').read_text())['rows']
    matched=json.loads((ROOT/'stage9a_length_matched_pairs.json').read_text())
    annotation=json.loads((ROOT/'annotations/causal_selection_frozen.json').read_text())
    names={'instruct_direct':'Direct','instruct_cot':'Prompted CoT','thinking':'Thinking'}
    keys={'P1':'Demand alignment ±16','P2':'Late episode fraction','P3':'Episodes / 1,000 tokens','P4':'Long-gap re-engagement'}
    positives=[k for k,v in effects['primary'].items() if v['ci'] is not None and v['ci'][0]>0]
    assert not positives,'This report implements the observed negative Stage 9A decision; reassess if data change'
    lines=['# Stage 9A — completed; stop at the regime-validation gate','',
        'The proposed Thinking-specific recurrent visual-access regime is **not supported** in this 128-family native comparison. '
        'None of the four predeclared Thinking−CoT primary contrasts is positive at the required confidence. '
        'Thinking has fewer frozen-proxy episodes per 1,000 reasoning tokens; the other primary intervals include zero. '
        'Sparse matched-length and causal support prevents an equivalence conclusion. The secondary accuracy advantage does not establish the proposed mechanism.','',
        '**Exactly one recommendation:** Stop the Stage 9 bottleneck/bypass branch here and retain the existing reasoning-conditioned dynamic visual-retrieval framing. '
        'Execution stopped after the approved Stage 9A validation; no Stage 9B/C or other follow-on experiment was launched.','',
        '## Execution and measurement','',
        'All 384 native trajectories are preserved: 128 per arm, 128 distinct conservative families from the unused MathVision reserve, 15 subjects, difficulty 1–5, 60 multiple-choice and 68 free-response items. '
        'The 2B Instruct/Thinking checkpoints used BF16, temperature 1, top_p 0.95, top_k 20, unchanged image preprocessing, and the 40,960-token cap. '
        'Direct and CoT share the Instruct template; only CoT appends the frozen instruction. Thinking retains its native `<think>` template. '
        '“Direct” means no added CoT instruction; it did not force short answers or suppress spontaneous reasoning.','',
        'All native artifact hashes were reverified. The detector, threshold 0.5478025980771918, layers 19–22 and max-over-head/layer aggregation were unchanged. '
        'First-token undefined detector/QK values are excluded. Primary native reasoning spans and common non-special full-assistant sensitivity are both reported. '
        'Bootstrap units are whole families, 4000 resamples; four primary 98.75% intervals, secondary 95%, minimum 20 contributing families.','',
        '| Arm | Mean / median reasoning tokens | Capped | Uncertain span boundaries | Reviewed demands / covered trajectories |',
        '|---|---:|---:|---:|---:|']
    for arm,name in names.items():
        d=effects['descriptive'][arm]
        lines.append(f"| {name} | {d['mean_reasoning_length']:.0f} / {d['median_reasoning_length']:.0f} | {d['completion'].get('capped',0)}/128 | {d['uncertain_boundaries']}/128 | {d['reviewed_demand_events']} / {d['trajectories_with_reviewed_demands']} |")
    lines += ['', 'The frozen CoT instruction did not increase mean or median trace length relative to Direct in this cohort. '
        'This is a comparison of one approved prompting protocol with native Thinking, not evidence about every possible CoT elicitation method.',
        '', '## Primary paired contrasts','',
        'Effects below are Thinking minus prompted CoT. Each metric uses its actual paired overlap; missing demand annotations and no-episode denominators are not zero.','',
        '| Endpoint | Paired families | Thinking / CoT mean on paired support | Effect | 98.75% CI |',
        '|---|---:|---:|---:|---:|']
    for key,title in keys.items():
        d=effects['primary'][key]
        lines.append(f"| {title} | {d['n_families']} | {fmt(d['left_mean'])} / {fmt(d['right_mean'])} | {fmt(d['mean'])} | {interval(d['ci'])} |")
    lines += ['',
        'The exploratory raw episode-count contrast is positive, while episodes per 1,000 tokens is negative. '
        'A greater total count in a longer trace is therefore insufficient evidence for the proposed recurrent regime. '
        'The common-assistant and normal-completion sensitivities preserve the negative density result. '
        'CoT−Direct primary-endpoint 95% intervals all include zero.','',
        '## Length, demand specificity and raw routing controls','',
        f"Only **{matched['matched_families']}/128** same-item pairs satisfy the unchanged |Δlog length|≤.15 caliper. "
        'The matched endpoint supports are 4/7/9/7 families; no matched inferential interval is issued. '
        'No caliper widening or replacement pairing was used. Family-clustered OLS adjusts for arm, log length, completion, subject, difficulty, answer format and question length. '
        'These are adjusted associations: generated length/completion are post-checkpoint variables, not randomized controls.','',
        '| Adjusted Thinking−CoT coefficient | Effect | 98.75% CI | Families |',
        '|---|---:|---:|---:|']
    for key,title in keys.items():
        d=effects['adjusted'][key];lines.append(f"| {title} | {fmt(d['coefficient'])} | {interval(d['ci'])} | {d['n_families']} |")
    lines += ['',
        'All original regression designs have full column rank, and all 4000 bootstraps yield an identifiable Thinking−CoT coefficient; resampled category-rank losses are recorded. '
        'No adjusted primary interval is wholly positive.','',
        '539/700 explicit-demand nominations were accepted, 126 rejected and 35 unknown, after review of source images and local text. '
        'The 539 accepted events cover 102 distinct families and 228 trajectories; 114 trajectories had no nominated phrase. '
        'This is bounded explicit-phrase coverage, not an exhaustive demand census. All annotations were completed by the main Codex annotator, not independent human reviewers. '
        'Arm IDs, gold/correctness, routing and causal effects were masked; prose style can still reveal the arm.','',
        '| Arm | Demand ±16 | Circular-shift control | Demand minus shift, 95% CI |',
        '|---|---:|---:|---:|']
    for arm,name in names.items():
        d=effects['demand_specificity'][arm];delta=d['demand_minus_shift']
        lines.append(f"| {name} | {fmt(d['P1']['mean'])} | {fmt(d['shift_control_alignment16']['mean'])} | {fmt(delta['mean'])} {interval(delta['ci'])} |")
    diff=effects['sensitivities']['demand_minus_shift']
    lines += ['',
        f"Demand-associated retrieval exceeds circular-shift controls in all three arms, but its paired Thinking−CoT difference is {fmt(diff['mean'])}, 95% CI {interval(diff['ci'])}. "
        'It does not establish Thinking-specific demand alignment. Unpaired arm means above and paired P1 means differ because annotation overlap differs. '
        'Reviewed non-demand controls, onset-only alignment, ±32 windows and full-window edge sensitivities are retained. '
        'Non-demand paired support is particularly sparse; unknowns are never used as negative controls.','',
        'Raw visual attention/QK channels and continuous detector score are also lower for Thinking on the unadjusted family comparison. '
        'For example, the mean of the frozen max-aggregated visual-mass channel is 0.0787 versus 0.1134, '
        'and mean R is 0.2188 versus 0.2537 (Thinking/CoT). These are aggregation-specific observations, not calibrated probabilities of visual causality. '
        'Per-token spatial focus/entropy and reviewed target/donor/residual source-partition diagnostics accompany the detector. '
        'Spatial entropy is not labeled semantic-source entropy.','',
        'The negative density contrast persists in both answer formats and in every leave-one-subject-out mean (range −3.076 to −2.210 episodes/1,000). '
        'Fine problem-type, visual-density and entity-count metadata are unknown for all 128 items; those fields cannot establish robustness. '
        'Subject/category is the available problem-subtype proxy. Most individual subjects lack 20-family support.','',
        '## Frozen causal validation','',
        f"All **{len(causal['rows'])}/50** eligible events were replayed: Direct 16, CoT 16, Thinking 18, at most one event per family/arm. "
        'Selection used only reviewed demand, local source/readout eligibility and stable hashes before any measurements. '
        'All 610 source/readout nominations were reviewed; the final bounded inventory yielded '
        f"{annotation['eligible_events']} eligible demands before the one-family/arm selection. "
        'Numeric-boundary and ROI-coordinate repairs, and the rejection of an article mistaken for a vertex label, were preserved before the freeze.','',
        'Tests use the exact native token prefix and next local evidence string, with same-image different-content Values copied into either the demanded or irrelevant region at layers 19–22 under native selected-layer routing. '
        'Original versus donor-counterfactual strings are scored by mean token log probability. Positive effect means a donor-semantic preference shift. '
        'Self/sham must reproduce native logits exactly. This is source-local Value validation, not a pixel counterfactual or an all-path visual-causality test.','',
        '| Arm | Events | Target effect | Irrelevant effect | Target−irrelevant | Positive target−irrelevant events |',
        '|---|---:|---:|---:|---:|---:|']
    for arm,name in names.items():
        d=causal['arms'][arm]
        lines.append(f"| {name} | {d['events']} | {fmt(d['target']['mean'],5)} | {fmt(d['irrelevant']['mean'],5)} | {fmt(d['target_minus_irrelevant']['mean'],5)} | {d['positive_target_minus_irrelevant_count']} |")
    d=causal['thinking_minus_cot_paired']['target_minus_irrelevant'];pool=causal['pooled_equal_family_target_minus_irrelevant']
    lines += ['',
        f"The paired Thinking−CoT target-minus-irrelevant effect is {fmt(d['mean'],5)} across {d['n_families']} overlapping families; CI: {interval(d['ci'])}. "
        'All arm-specific samples fall below both the 24-event feasibility aim and 20-family inference threshold. '
        'These results cannot establish a robust causal arm difference. Eligibility is limited to the implemented clear discrete-content assay, not all possible visual events.','',
        f"Pooling arms with equal family weight gives target-minus-irrelevant {fmt(pool['mean'],5)}, 95% CI {interval(pool['ci'],5)}, across {pool['n_families']} families. "
        'This pooled validation does not test Thinking specificity. '
        f"Native-prefix passive features are exact in {causal['exact_native_prefix_events']}/50 events; maximum absolute difference {causal['max_native_prefix_passive_abs']}. "
        'Capture and self/sham logits are exact at every scored query; sham semantic effects are exactly zero. '
        f"The raw FP64 JS expression leaves at most {causal['max_abs_sham_js']:.2e} signed roundoff; raw values are preserved, "
        'with a 64-machine-epsilon aggregation tolerance and unchanged mandatory exact-logit/score checks. '
        'Optional alphaV/post-WO and source-selectivity measurements are saved on these 50 first queries only.','',
        'Donors retain their native positional/contextual information. Irrelevant controls match token shape/cardinality and minimize ink; they are not Value-norm or visual-content matched. '
        'Original and counterfactual strings are teacher-forced from the same original prefix. At each query, every intervention uses the same unperturbed history for that candidate; intervention-altered caches do not propagate. '
        'Final-answer accuracy never substitutes for the local readout.','',
        '## Secondary accuracy','',
        'All 384 extractions received masked review. The unchanged local Qwen/MathVision adapter uses bounded numeric equivalence at 1e−6 and no external judge. '
        'Formatting/units and superseded intermediate answers were corrected by literal text review before gold comparison. '
        'Raw-adapter scores remain available. Unscorable cases receive no credit in the all 128 denominator and remain distinct from known wrong answers.','',
        '| Arm | Reviewed correct / wrong / unscorable | All-example accuracy | Scorable-only accuracy | Raw-adapter all-example accuracy |',
        '|---|---:|---:|---:|---:|']
    for arm,name in names.items():
        d=accuracy['arms'][arm]['reviewed'];raw=accuracy['arms'][arm]['raw_adapter']
        lines.append(f"| {name} | {d['correct']} / {d['wrong']} / {d['unscorable']} | {100*d['accuracy_all_examples_no_credit']:.2f}% | {100*d['accuracy_among_scorable']:.2f}% | {100*raw['accuracy_all_examples_no_credit']:.2f}% |")
    lines += ['',
        'Thinking−CoT reviewed no-credit accuracy is +15.63 percentage points (secondary 95% paired CI +7.03 to +23.44). '
        'Accuracy is a separate outcome and does not override the failed primary regime gate.','',
        '## Decision gates and stopping boundary','',
        '| Required criterion | Result |',
        '|---|---|',
        '| At least two positive primary Thinking−CoT effects | Not met: 0/4 |',
        '| At least one survives length control | Not established; 9 matched pairs, all adjusted primary CIs include zero |',
        '| Demand-specific re-engagement | Supported within arms; Thinking-specific advantage not established |',
        '| Causal support for part of the arm difference | Insufficient eligible independent support |',
        '| Not driven by one subtype | No positive primary phenotype to certify; negative density broad across available categories |',
        '',
        'This is a negative result for advancing the proposed native-regime story, with unresolved matching/causal precision and incomplete fine-subtype coverage. '
        'It does not show computational equivalence, absence of visual retrieval, absence of all Thinking advantages, or the cause of the accuracy difference. '
        'No additional benchmark, prompt, threshold or model was tried to rescue the hypothesis.','',
        '## Resources and evidence','',
        f"Native trajectories contain {sum(r['generated_tokens'] for r in rows):,} generated tokens and {sum(r['runtime_seconds'] for r in rows)/3600:.2f} measured inference GPU-hours. "
        f"Causal event execution adds {causal['runtime_gpu_hours']:.2f} GPU-hours, excluding model startup, with peak allocated VRAM {causal['max_peak_gpu_gib']:.2f} GiB. "
        'GPU workers 121562/121563/121564 used one A6000 each on node06. '
        'CPU-only 121568 ran on node03 for 9m 02s; pending CPU-only 121566 was cancelled before work and moved due host-memory capacity. '
        'Slurm accounting storage is disabled, so measured runtimes and captured job/worker receipts are retained instead of an invented billing total. '
        'Annotation burden: 700 semantic nominations, 610 local source/readout nominations, 128 source images, 50 sets of source/donor/control crops, and 384 answer extractions; no human annotation-hour estimate.','',
        'The native generation config is preserved. `stage9a_generation_config_node07.json` is the actual execution-config identity after the documented resource amendment; its scientific settings match the original. '
        'All workers release allocations when their bounded queues end; final release status is in `audit/final_validation.json`.','',
        'The 13 plan-required artifacts are in this directory. Supporting evidence includes:','',
        '- [All raw hashes verified](audit/all_native_hashes_verified.json)',
        '- [Frozen semantic review](annotations/semantic_review_complete.json)',
        '- [Frozen source/readout selection](annotations/causal_selection_frozen.json)',
        '- [Masked extraction review](annotations/answer_extraction_review_frozen.json)',
        '- [Time/source/support diagnostics](audit/sensitivity_diagnostics.json)',
        '- [Primary and controlled effects](stage9a_primary_effects.json)',
        '- [Causal validation](stage9a_causal_validation.json)',
        '- [Secondary accuracy](stage9a_accuracy_secondary.json)','',
        'Figures (PNG and PDF):','',
        '1. [All-family access trajectories](figures/figure1_visual_access_trajectories.png)',
        '2. [Recurrence and late access](figures/figure2_recurrence_and_late_access.png)',
        '3. [Demand alignment](figures/figure3_demand_alignment.png)',
        '4. [Length controls](figures/figure4_length_controls.png)',
        '5. [Causal source validation](figures/figure5_causal_source_validation.png)','',
        '**STOP.** The authorized Stage 9A action is complete; the recommendation is not a new experiment authorization.','']
    text='\n'.join(lines)
    old=ROOT/'stage9a_summary.md';backup=ROOT/'audit/stage9a_summary_before_final.md'
    if old.exists() and not backup.exists():backup.write_text(old.read_text())
    old.write_text(text)
    save(ROOT/'audit/decision.json',dict(primary_positive_endpoints=positives,advance=False,
        recommendation='Stop the Stage 9 bottleneck/bypass branch here and retain the existing reasoning-conditioned dynamic visual-retrieval framing.',
        next_experiment_launched=False,summary_sha256=sha(old)))
    print('Final Stage 9A report written')


if __name__=='__main__':main()
