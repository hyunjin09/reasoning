# Stage13C — stopped at forced-reasoning contract validation

Decision: **FORCED_TRACE_CONTRACT_BLOCKED**. The scientific mechanism study was not run.

The source-only24-family cohort, disjointtechnical4 and initial8 were sealed. All28 source traces use the first technically resolved Stage13A replicate, without correctness selection. Original Q+E*, 4B checkpoints, recipes and caps were preserved.

Technical execution:8 attempted short/long dummy calls; 7 normal-stop responses saved and 1 interrupted after the gate. All8 exact forced-token receipts pass:16-token short traces or source-length long traces, one token per autoregressive step with KV continuation, native closing token at the prescribed position, no forced-prefix prefill, no images.

However, 5/7 completed outputs emit a second native </think> after thousands of free tokens. One further long2472 output shows explicit reconsideration without a second marker. Long1269 has no second marker and extended final-solution prose; no semantic no-reasoning pass is inferred from marker absence. These are technical-case observations, not a population-rate estimate.

| Item / condition | Forced close position | Second close position | Free tokens before second close |
|---|---:|---:|---:|
| 2360 / T_SHORT | 16 | 6032 | 6015 |
| 2360 / T_LONG | 5088 | 7105 | 2016 |
| 2640 / T_SHORT | 16 | 7168 | 7151 |
| 2640 / T_LONG | 8675 | 15631 | 6955 |
| 1269 / T_SHORT | 16 | 7768 | 7751 |

For example, short2360 continues with “Wait, no. Let’s think more carefully” and repeated variable redefinitions after its forced close. Short1269 starts a fresh step-by-step derivation. The literal first-close and no-reopening-token constraints therefore do not enforce the required absence of additional free reasoning. The resulting short/long comparison would not isolate the intended amount of reasoning computation.

The plan requires stopping at this contract boundary. No scientific call, initial-eight missingness gate, native/semantic/Instruct technical extension, correctness scoring, paired inference or bootstrap was run. No prompt, answer grammar, sampling, penalty or cap search was attempted. The underlying cause of ignoring the semantic boundary is unresolved; the emitted behavior is directly observed.

Source-derived annotations for28families remain clearly marked drafts, not final leakage/QC certificates and never used as interventions. Required downstream artifacts explicitly record NOT_RUN/NOT_ESTIMATED; scientific result tables are empty, family effects are null. The five scientific figures are not estimable and were not fabricated. A standalone technical diagnostic figure is provided instead.

The first two Slurm jobs failed before any call because of a custom-processor loader delimiter error. The actual vLLM loader regression reproduced it; a one-character correction, versioned config and original source snapshots were preserved. The repeated run passed the mechanical token-step checks. This wiring issue is separate from the observed scientific-contract failure.

Resources: 0.307778 allocated GPU-hours across4jobs; all released. 20,520 prior Stage12/13 files verified unchanged. Completed raw responses, interrupted input/forced receipt, logs, source traces, drafts and both code/config versions are preserved.

Exactly one recommendation: Retain Stage 13A's confirmed post-evidence advantage as the strongest claim and do not expand the mechanism story.

STOP. No follow-on launched.

[Saved answers/reasoning](responses.md) · [Technical validation](../../../outputs/stage13c/v1/stage13c_forced_trace_technical_validation.json) · [Resources](../../../outputs/stage13c/v1/stage13c_resource_accounting.json)

[Technical token diagnostic](../../../outputs/stage13c/v1/figures/stage13c_technical_forced_contract.png). This is a technical display, not one of the unexecuted scientific-effect figures.
