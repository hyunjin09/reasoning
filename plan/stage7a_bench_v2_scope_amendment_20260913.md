# Stage7A-Bench v2 — user-approved mechanistic scope amendment

Recorded:2026-09-13 00:32KST. Authority: the user's explicit amendment in this conversation; no additional approval is required. This supersedes the broader remaining queue in `stage7a_benchmark_failure_enrichment_plan_v2_mirage_track.md`. Preserve that original plan, frozen manifests and historical execution records.

## Objective and retained roles

Identify naturally occurring, causally diagnosable source-faithfulness failures for a possible later sequence: failure → causal diagnosis → online monitor → grounding-aware decoding/rollback. This stage authorizes benchmark evaluation and eligible causal pilots only. Low final accuracy alone is not the objective or selection criterion.

| Benchmark | Amended status | Mechanistic role |
|---|---|---|
| Phantom-0 | completed; preserve; never rerun | extreme no-valid-source/unsatisfied-demand reference |
| CharXiv | completed; preserve; never rerun | chart source-confusion reference |
| MathWild / MathVision-Wildphoto | continue only to96 full reviews initially | degraded-source/extraction regime |
| MMMU-Pro | continue after the MathWild gate | main image-present/no-image prior-fill bridge |
| MMLongBench-Doc | continue after MMMU-Pro | page/field/row source-confusion topology |
| MathSight | deferred | overlaps degradation and no-image axes |
| MicroVQA | deferred | medical domain replication |
| MedXpertQA-MM | deferred | medical domain replication |

For deferred benchmarks: no further generation, downloading, review or causal scoring without explicit user reauthorization. Preserve existing preparation and startup artifacts. No reserve/additional benchmark breadth is authorized.

## Preserve completed evidence

Keep all completed evidence, reviews, causal scores, logs, manifests, figures and accounting for Phantom and CharXiv. CharXiv's64-event pilot remains valid negative/low-yield evidence:1 strong WRONG_SOURCE_READ,6 strong faithful,25 weaker faithful and32 unresolved. Testing documents does not invalidate or reinterpret it. Phantom remains a behavioral extreme no-image reference; no true target ROI exists there.

## MathWild interim gate

Reach96 fully reviewed examples without interrupting an in-flight example solely to enforce the boundary. Use the nearest safe between-example/unit boundary. Operationalization at amendment time:39 primary photos are fully generated/reviewed; generate only the next57 primary photos in the existing frozen order, then pause for the full96-review gate. Four disjoint worker shards may process that fixed suffix; no later frozen row is released before the decision.

Freeze the interim feasibility report using semantic/source/readout eligibility only. Do not use attention, QK, alphaV, VSD, hidden states, PCA or causal effect sizes to decide continuation. Report separately:

- locally wrong visual-value candidates;
- wrong source/entity binding candidates;
- source-coupled extraction-error candidates, still semantic candidates;
- faithful controls;
- events with clean demanded-source ROI;
- events with plausible alternative source;
- events with valid value/binding/error-oriented causal readout;
- interpretable paired clean→wildphoto transitions, if both conditions exist.

Continue beyond96 only if at least one fixed condition passes:

1. **A:** at least12 local visual/source/extraction failure candidates with source-localizable evidence;
2. **B:** at least16 failure events eligible for a proper Stage7A-style causal pilot, including valid demand, source identity and correctly oriented local/error readout;
3. **C:** where exact pairing is available, at least10 paired items transition from a clean/correct local visual read to an interpretable wildphoto local visual/source error candidate.

If none passes, stop MathWild at the safe boundary and record low yield for the intended causal failure analysis. Never lower the gate after seeing its result. If it passes, the existing frozen200-photo+64-screenshot sample may continue as needed; no expansion beyond264 conditions. Exact source pairing without generated/reviewed clean responses does not itself establish criterionC. Unknown/unavailable is not zero evidence.

## Ordered remaining execution and causal rules

After the MathWild gate, run MMMU-Pro with separate frozen image-present, silent no-image/mirage and explicit no-image/guess conditions where supported. Preserve the existing Behavioral B-Clean protocol separately. Image-absent correctness is neither PRIOR_FILL nor causally nonvisual reasoning. Screen specific unsupported visual evidence, silent/explicit differences, certifiable faithful image-present controls and informative paired claims. Use existing pilot eligibility and unchanged PRIOR_FILL definitions.

Then run MMLongBench-Doc. Verify page, field, row, table-region or header-value identities and readout orientation before expensive causal scoring. Error-rich but causally unidentifiable documents are a valid negative result. Never force errors into WRONG_SOURCE_READ; retain the existing error-oriented support and source-semantic followability requirements. Preserve full physical-page input and existing missing/context/resource exclusions; no oracle page selection.

For a MathWild pass, operational ordering is gate decision → remaining frozen MathWild work, if needed → MMMU-Pro → MMLongBench-Doc. Complete eligible pilots within retained scope. Parallelism may occur within a released benchmark, not by bypassing these benchmark-level gates/order.

## Reduced final comparison

Compare Phantom/MMMU-Pro for prior/no-valid-source; CharXiv/MMLong for wrong-source/source-confusion; MathWild for degraded-source/extraction. Report reviewed native counts (distinguishing bases and condition rows), final accuracy, local visual/source candidate rates, faithful-control yield, source-identifiable event yield, error-oriented readout feasibility, causal-pilot size, all unchanged causal-state counts (FAITHFUL_READ, PRIOR_FILL, WRONG_SOURCE_READ, SOURCE_COUPLED_EXTRACTION_ERROR, DOWNSTREAM_INTEGRATION_ERROR, SOURCE_ANOMALY, unresolved; retain stale-source if present), strong unfaithful per100 native examples and per pilot event, approximate GPU-hours and annotation burden. Nest events by base/source family as appropriate.

Prefer source-faithfulness failure yield × causal identifiability × error-readout validity × intervention relevance, while retaining adequate faithful controls. Do not rank by accuracy alone. Preserve negative and unresolved results. Sparse strong failures across these retained benchmarks would support reporting limited suitability of existing natural benchmarks for this model, rather than automatically adding more benchmarks.

## Resources and stop

Use existing Slurm113280/node02/tmux10 only:4 A6000 GPUs,32 CPUs,120G RAM, scheduled expiry2026-09-20 00:10:55KST. No additional allocation to restore the original sweep. If unavailable, follow local GPU/access policy.

Before further execution, update workflow state, phase memory, decision log, checklist and resource estimate. Keep historical manifests unchanged. The old2376-condition freeze remains historical;984 MathSight/Micro/Med conditions are deferred. Retained scope is at most1392 conditions, or1224 if MathWild stops at96; five retained document conditions already have missing/context exclusions.

Finish: MathWild gate/completion decision → MMMU-Pro → MMLongBench-Doc → eligible retained pilots → reduced comparison → exactly one recommendation → STOP and return the reduced-sweep summary. Do not execute the recommendation. No automatic new benchmark,2B/8B study, monitor training, rollback, grounding-aware decoding or full new causal cohort. Those require a later user-selected research action.
