# Stage11C — completed with prescribed technical STOP

Stage11C could not localize the Thinking-versus-Instruct advantage. The common 8,192-token primary completion gate failed before the oracle. This is a completion-limited result, not evidence for a zero native gap or an upstream/downstream mechanism. Noncompletion cause remains unknown.

## Frozen design and source evidence

The development rule used levels 2–4 across all subjects: 47 eligible earlier families (Thinking 19/47; Direct 11/47), with no fallback. The original 300-source manifest, original reviews, and source-only alias exclusions 1887/814 are preserved. No heldout outcomes selected sources or repaired E*.

We reviewed 250 source entries twice and retained 120 eligible families. Frozen split: 80 primary and 40 reserve, plus subset IDs for 24 neutral, 48 CoT, and 32 native-state families. E* and all subsets were frozen before primary inference. No reserve opened.

Two AI agents reviewed the evidence independently; these agreement measurements are not human inter-rater reliability. Each reviewer constructed a disjoint portion before reviewing the common proposals. In the final single-source batches, only reviewer A constructed proposals; reviewer B reviewed them without construction exposure. Raw all-proposal sufficiency agreement 98.0%,kappa 0.960; nonempty-proposal agreement 96.2%,kappa 0.278. Nonempty quality-conjunction agreement 93.1%,kappa 0.161. Low conditional kappa under strongly positive prevalence and all disputes remain disclosed; strict dual-pass eligibility excludes disagreements. No post-outcome evidence repair.

## Execution and stop

Calibration: 12 non-primary cases × 2 modes × 2 caps = 48 exact valid calls. Thinking hit the cap on 12/12 and Direct on 11/12 cases at both 4,096 and 8,192 tokens. The plan therefore selected 8,192 and marked the stage completion-limited. Batch size 1, BF16, TF32 off, greedy decoding, repetition penalty 1, native image preprocessing, and pinned model revisions were preserved.

The fixed first 16 matched primary families produced 32 valid calls. The prespecified criterion stops further native/oracle work if either mode has more than 4 cap hits.

| Arm | Completed calls | Cap hits | No committed final | Literal-scored correct |
|---|---:|---:|---:|---:|
| thinking | 16 | 16 | 16 | 0 |
| instruct_direct | 16 | 15 | 10 | 3 |

These are technical diagnostics for the fixed 16-family gate only. They are not primary-cohort accuracy estimates. The remaining 128 native calls are explicitly NOT_RUN, not incorrect. No full native performance gate was evaluated.

Oracle, neutral text, CoT, secondary native-state annotation and reserve execution: NOT_RUN. P1/P2/P3 and closure fraction: NOT_ESTIMATED; no confidence interval or upstream/downstream/mixed claim. Figures 2–4 explicitly display the stop and missing estimates; no fictitious zeros or CoT figure.

A fixed calibration-case check found valid image inputs and native templates, unfinished Thinking and repeated Direct text. It did not establish the cause or justify a decoding/cap rescue. No extra benchmark or mechanism search was launched.

## Resources and evidence

All 8 Stage11C Slurm jobs terminal and GPUs released. Total allocated **3.583889 GPU-hours**, including startup and the safe partial calibration shard; hard limit 8. Calibration reused 39 completed calls when its remaining 9 were repartitioned. No duplicate valid generations. Source annotation burden: 250 construction records and 500 semantic reviews by AI agents, separate from GPU accounting.

Artifacts: [native gate](stage11c_native_gate.json), [cap calibration](stage11c_cap_validation.json), [sufficiency review](stage11c_e_star_sufficiency_review.json), [primary split](stage11c_primary_split.json), [inference status](stage11c_primary_inference.json), [resources](stage11c_resource_accounting.json). Raw logs/receipts, output-only literal-answer reviews and source construction records are retained.

## Recommendation

Keep Thinking-vs-Instruct as an unresolved performance observation and finalize the paper around the established causal retrieval and visual-to-text lifecycle claims.

STOP. The recommendation is not executed as a new research action.
