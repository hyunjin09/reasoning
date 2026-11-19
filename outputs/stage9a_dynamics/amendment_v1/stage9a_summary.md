# Stage9A causal visual-access dynamics — MAIN ANALYSIS COMPLETE / CONTROLS PENDING

Updated 2026-09-26T14:18:54.500363+00:00.

The completed64-family main study does **not support greater recurrent late direct visual-access necessity in Thinking than CoT**. This is a negative/uncertain result for the directional hypothesis, not evidence of equivalence, absence of visual processing, or a token-level visual-access boundary.

Main inference and the50 teacher-forced readouts are complete. The87 mandatory, preselected null-sink continuations remain pending/running in Slurm jobs124266–124273. The plan is **not yet finished**; their extraction review, comparison and final closure remain. Main conclusions below are sealed and will not be used to tune the control inventory.

## Frozen design and validity

Three arms reuse the same frozen MathVision native inputs: Instruct Direct, one prompted CoT, and Native Thinking.64 conservative visual families were selected prospectively from128 by metadata-stratified hash allocation. All384 original native trajectories,539 semantic demands,50 readout events and12 actual-model V1–V6/cache/backend validations remain preserved. BF16, prompts, sampling, seeds and40960-token cap are unchanged.

The assay masks image keys only for generated queries in decoder indices19–22. Prefill, prior KV and previously encoded image information persist; subsequent caches evolve. Cumulative cutoff, local-window knockout and demand-aligned knockout remain distinct. Local schedules use native coordinates even after divergence. Native FULL reuse is supported by backend validation and per-task native-prefix identity, not assumed cross-backend comparability.

The amended panel contains2138 logical conditions:1904 unique continuations (1896 new+8 exact reused) and234 native identities (192FULL+42 unreached cutoffs). All78 completed old-manifest rows are preserved;70 superseded rows are outside primary inference. No early-stop proposal was executed. All64 reserve families remain unused.

[Executed specification](stage9a_visual_access_dynamics_spec.md) · [Compute amendment](stage9a_compute_amendment_v1.md) · [Technical validation](stage9a_mask_backend_validation.json) · [Main integrity](audit/main_completion_validation_20260926.json)

## Baselines, extraction and denominators

| Arm | Native correct /64 | Accuracy | Wrong | Unscorable | At cap |
|---|---:|---:|---:|---:|---:|
| Direct | 14/64 | 21.88% | 33 | 17 | 18 |
| CoT | 21/64 | 32.81% | 33 | 10 | 13 |
| Thinking | 31/64 | 48.44% | 27 | 6 | 6 |



Main extraction review was sealed before gold-based scoring:942 deterministic unambiguous-terminal packet checks,775 manual packets, and154 exact-native continuations inheriting prior review.1717 unique packets cover1750 other outputs. One Codex annotator reviewed ambiguous literal answers with candidate/context/tail and options; this is not independent human annotation. Arm/condition IDs and gold were withheld, though writing style may reveal arm. No reasoning correction or numerical answer solving was used. The unchanged Stage8B v2 adapter/tolerance scores both raw and reviewed outputs.

Primary accuracy keeps all64 families per arm and treats unscorable as no credit **while retaining unscorable as a distinct label**. Scorable-only analysis is a potentially post-treatment-selected sensitivity. P3 uses28 families eligible in both Thinking and CoT; missing demand eligibility does not become zero.

[Sealed review](annotations/answer_extraction_review_frozen.json) · [Raw/reviewed scores](audit/scored_answers.json) · [Completion, length and divergence](audit/continuation_secondary.json)

## Primary family inference

Damage=FULL accuracy−masked accuracy; positive damage means access removal harms performance. Contrasts below are Thinking−CoT, in percentage points.4,000 paired family bootstrap draws use seed920260924. The98.75% simultaneous intervals cover four scalar components in three primary groups. No condition/token/event is counted as another independent family.

| Contrast | Paired families | T−C (pp) | Simultaneous CI (pp) | Positive / negative / tied families |
|---|---:|---:|---|---|
| P1: cutoff512 | 64 | -4.69 | [-21.88, +14.06] | 6 / 9 / 49 |
| P1: cutoff2048 | 64 | -3.13 | [-17.20, +14.06] | 5 / 8 / 51 |
| P2: final two20% windows | 64 | -2.34 | [-10.16, +3.91] | 4 / 6 / 54 |
| P3: demand−control | 28 | +10.71 | [-7.14, +32.14] | 4 / 1 / 23 |



None supports the hypothesized positive Thinking-specific contrast. P2 averages[.6,.8] and[.8,1.0], the final40% (called late-half in the amendment). Thinking late damage is+3.13pp versus CoT+5.47pp; the paired difference is−2.34pp. The stronger native Thinking accuracy is a baseline observation, not proof of greater visual necessity.

P3 is+10.71pp on28 paired families but uncertain. Leaving out algebra reduces it to0 on21 families. Only5 paired families have a nonzero T−C demand contrast (4 positive,1 negative). This fails the no-single-subject requirement for the optional extension; it is not established as a precision-only limitation.

[Primary inference and all sensitivities](stage9a_primary_inference.json) · [Family metrics](audit/family_metrics.json)

## Temporal and demand profiles (descriptive)

| Arm | cutoff0 | cutoff128 | cutoff512 | cutoff2048 | 0–20% | 20–40% | 40–60% | 60–80% | 80–100% |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Direct | -4.69 | -7.81 | -3.13 | +3.13 | -10.94 | +1.56 | -1.56 | +4.69 | -3.13 |
| CoT | +9.38 | +1.56 | +7.81 | +7.81 | +4.69 | +4.69 | +9.38 | +4.69 | +6.25 |
| Thinking | -3.13 | +4.69 | +3.13 | +4.69 | +1.56 | +0.00 | +4.69 | +4.69 | +1.56 |



Values are percentage-point damage; negative values are improved correctness under the scheduled perturbation. These are descriptive and not monotone boundary estimates. Especially for Direct, sampled trajectories, looping/capping and low baseline accuracy complicate simple “less access is better” interpretations. No new prompt or assay was selected to repair these outcomes.

| Arm | Eligible families | Demand damage | Shifted-control damage | Demand−control |
|---|---:|---:|---:|---:|
| Direct | 34 | -5.88 | +0.00 | -5.88 |
| CoT | 37 | +2.70 | +2.70 | +0.00 |
| Thinking | 38 | +10.53 | +0.00 | +10.53 |



These within-arm demand profiles use34/37/38 eligible families; the primary cross-arm effect uses the28-family intersection. Shifted controls lack an accepted annotated demand and are not certified demand-free.

## Sensitivity and local evidence

Literal extraction matters: raw-adapter T−C at cutoff2048 is+9.38pp versus reviewed−3.13pp; raw P2 is+3.13pp versus reviewed−2.34pp. Both raw intervals include zero. No robust positive late phenotype emerges under either scoring path. The normal/certain native-boundary intersection has40 families and P2=0. Restricting native Thinking/CoT length ratio to≤2 leaves18 families, below the20-family interval threshold. Common cutoff exposure retains59 families at512 and48 at2048 and keeps negative point estimates.

Scorable-complete P2 remains−1.25pp on40 families. Scorable-complete P3 is0 on17 families, with interval withheld. These restrictions do not estimate an unbiased alternative population effect. Capped native trajectories are retained in primary inference; altered stopping/extractability is part of the observed continuation behavior.

All50 fixed teacher-forced events were retained:16 Direct,16 CoT,18 Thinking. Positive values below mean reduced original evidence mean log probability (nats per token). They are secondary, with no arm reaching20 families.

| Arm | Events | r16 demand damage | r32 demand damage | Unexposed shifted controls | Both-exposed pairs |
|---|---:|---:|---:|---:|---:|
| Direct | 16 | 0.0334 | 0.0434 | 12 | 4 |
| CoT | 16 | 0.0020 | 0.0029 | 13 | 3 |
| Thinking | 18 | 0.1467 | 0.2610 | 15 | 3 |



40/50 shifted controls occur after the readout and are unexposed. Therefore the larger Thinking teacher-forced mean change is not a validated demand-specific cross-arm result. The explicit both-exposed sensitivity has only4/3/3 events. Donor-preference, sum-log-probability and main64-only summaries are retained separately; no reserve readout is added to the primary64-family denominator.

[Local readouts](audit/local_readouts_secondary.json) · [Native usage comparison](audit/native_usage_secondary.json)

The original128-family native-use study had0/4 supported positive primary contrasts. On the same64 families used here, usage frequency/timing and causal performance damage remain distinct summaries. Neither attention frequency nor an unperturbed correlation establishes functional necessity.

## Redistribution controls

87 exact frozen rows on8 families were materialized after main inference; no effect-based representative selection. Slurm capacity is the current blocker. Matched main suffix timing projects8.70GPU-hours plus prefix/startup and uncertainty from changed continuation lengths. Queue delay is additional. All workers stop at their frozen queue boundary. No control outcome or robustness claim is available yet.



## Gates and recommendation

Query-text bypass: **not triggered** because there is no supported Thinking-specific late effect. Reserve extension: **not triggered** because P2 is negative and P3 fails subject robustness; no evidence establishes a precision-only problem. Stage9B advance: **fails** the primary late/semantic-support criteria, independently of unfinished or bounded redistribution characterization.

**Exactly one recommendation: close the Thinking-specific visual-access scheduling branch; do not advance to Stage9B.**

This does not reject visual grounding, recurrent visual use, or small effects the study cannot resolve. It closes the proposed distinctive late-necessity claim under these models, fixed prompt, layer window and MathVision cohort. No new experiment has been launched.

## Figures and artifacts

[1. Intervention schematic](figures/figure1_intervention_schematic.png) · [PDF](figures/figure1_intervention_schematic.pdf)  

[2. Cumulative necessity](figures/figure2_cumulative_necessity.png) · [PDF](figures/figure2_cumulative_necessity.pdf)  

[3. Temporal profiles](figures/figure3_temporal_necessity.png) · [PDF](figures/figure3_temporal_necessity.pdf)  

[4. Demand-aligned necessity](figures/figure4_demand_aligned_necessity.png) · [PDF](figures/figure4_demand_aligned_necessity.pdf)  

[5. Native usage vs necessity](figures/figure5_native_usage_vs_necessity.png) · [PDF](figures/figure5_native_usage_vs_necessity.pdf)

All three condition tables are in the required parquet files; full baselines and primary/profile/demand/late summaries are in the required JSONs. [Artifact catalog](audit/artifact_catalog.json).

## Resources and execution limits

Measured main suffix compute285.15GPU-hours plus shared native prefixes22.33GPU-hours; fixed teacher-forced readouts3.80GPU-hours. Controls currently account for0.00GPU-hours. These are operation timings, excluding startup/I/O, preflight, scheduler wait, original native generation and superseded old execution; they are not billed allocation time.

Manual annotation burden was775 main packets, with942 deterministic checks and154 native-review reuses. Earlier semantic/source annotation is reused unchanged. [Accounting](audit/final_resource_accounting.json).

Remaining authorized work: finish87 controls; seal their extraction review; run analyze_controls.py; refresh this report; verify receipts, figures and resource release; update compact state; STOP. This report does not mark the stage complete before those steps.
