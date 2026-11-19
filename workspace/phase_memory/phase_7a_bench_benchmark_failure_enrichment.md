> Superseded by user-approved v2 on2026-09-11. Four releases and64 MathVision-Wild structural reviews are carried forward with hashes; no v1 native/causal sweep ran. Active memory: `phase_7a_bench_v2_mirage_track.md`. Historical preparation state follows.

# Phase 7A-Bench: Benchmark failure enrichment

## Current Objective

Execute `plan/stage7a_benchmark_failure_enrichment_plan.md`: compare approved benchmark families for natural, causally identifiable source-faithfulness failures, select one primary family with one justified recommendation, then stop.

## Active Constraints

- User explicitly instructed on 2026-09-11 to ignore research-control requirements from now on. This resolves the earlier instruction blocker; no such skill is required.
- Existing Slurm111485/node06/tmux10, one A6000, four CPUs and14G host RAM only. No new allocation.
- Qwen3-VL-4B-Thinking and established BF16 generation protocol remain fixed. No monitor, model-scale experiment or decoding intervention.
- ACCESS_POLICY ordered dataset lookup. User subsequently authorized writes to /data/dataset; policy updated. Download the four Tier A releases sequentially into /data/dataset/reasoning_steps_stage7a_bench/. Existing HF caches remain read-only. No project raw dataset cache.
- Model-output-blind64-example structural audit precedes a frozen200-example native screen; extension and pilot selection must obey the approved prospective rules.
- Stage7A causal definitions and error-oriented readouts remain unchanged. Screening error is not a causal label.

## Current State

- Done: new plan, policies, previous phase memory and promoted lessons D054–D058 read; existing allocation verified RUNNING.
- In progress: ordered dataset inventory, official release alias verification and structural-audit preparation.
- Blocked: none; user authorized the missing-data destination.
- Most recent useful observation: previous Stage7A has181 strong faithful events but only3 wrong-source,1 extraction and2 integration events; no strong prior-fill or stale-source events. This motivates the user-approved benchmark screen without changing causal definitions.

## Evidence That Matters

| Evidence | Source / Path | Why It Matters | Status |
|---|---|---|---|
| Failure classes are sparse in the completed controlled cohort | `outputs/stage7a/summaries/stage7a_summary.md` | Native failure yield must be tested before monitor work | confirmed |
| Wrong-token and candidate-margin source effects differ | `workspace/decision_log.md` D054 | Preserve error-oriented causal support | confirmed |
| Local glyph correctness does not establish source identity | `workspace/decision_log.md` D055 | Audit demand, binding and ROI jointly | confirmed |
| Conditional/question-given/derived values are not unconditional visual reads | `workspace/decision_log.md` D058 | Review full semantic scope before causal selection | confirmed |

## Failed Attempts and Lessons

| Attempt | Failure / Symptom | Diagnosis | Lesson | Do Not Repeat |
|---|---|---|---|---|
| Two MMLongBench-Doc downloads | Payload byte counts differ from pinned LFS pointers | First content SHA256 matches exactly: supported metadata-size inconsistency; second hash mismatch: cause unknown | Preserve receipts and the invalid mi_phone.pdf payload; no blind retry | Do not admit hash-mismatched assets or silently replace sampled rows |

## Open Candidates

| Candidate | Why Plausible | How to Test | Status |
|---|---|---|---|
| MathVision-Wild photographic release | Natural presentation stress with possible clean pairing | Ordered availability lookup, paired-ID and64-example structure audit | open |
| MathSight | Paired image variants and text-only condition | Same audit, with explicit visual-demand distinction | open |
| MMLongBench-Doc | Similar pages/fields may cause source confusion | Verify official release and page/field identifiability | open |
| CharXiv reasoning | Confusable series, axes and legends | Verify reasoning split and local source editability | open |
| Tier B candidates | Approved fallback if Tier A insufficient | Inspect only after Tier A availability/eligibility decision | reserved |

## Next-Step Decision

- Current bottleneck: exact local benchmark availability and source identifiability are unknown.
- Relevant memory item used: sparse strong Stage7A failure classes and D054/D055/D058.
- Chosen next action: complete the four authorized sequential Tier A downloads, validate integrity, then Phase A model-output-blind structural audits. HallusionBench64 IDs were frozen during the access block; review is deferred until Tier A eligibility is known.
- Why this action: identifies whether a frozen native sweep can provide interpretable visual errors before spending GPU time.
- What not to repeat: infer grounding from final wrongness; use causal effects for sampling; download into a read-only root.
- Stop condition: complete structural eligibility decisions, or record an actual access/data blocker after checking every authorized candidate.

### Step Result

- Action taken: read the approved plan and verified the existing allocation; started ordered local lookup and official release naming checks.
- Result: inventory in progress; no new GPU workload or dataset download.
- Evidence saved: inventory and lookup audit will be written under `outputs/stage7a_bench/` before any download.
- Failure or issue: no writable external download root under current policy.
- Lesson learned: pending structural evidence.
- Next implication: continue available candidates; request only a concrete missing-data destination if required.

- Download diagnostic boundary: three datasets completely verified; MMLongBench-Doc has134 verified PDFs and one quarantined PDF. First size exception admitted only because SHA256 exactly matches the pinned pointer. Evidence: `outputs/stage7a_bench/audit/download_size_diagnostic.json`.
