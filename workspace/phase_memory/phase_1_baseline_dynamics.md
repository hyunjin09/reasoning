# Phase 1: Baseline Visual–Reasoning Dynamics

## Current Objective

Close Stage 1 after validating the locked official-style protocol and the 200-attempt MathVerse discovery cohort, preserving the descriptive/non-causal boundary and stopping before Stage 2.

## Active Constraints

- Stage 0 is immutable instrumentation evidence; write all new inference artifacts under `outputs/stage1`.
- Keep the Stage 0 model, prompt, processor, evaluator, hooks, attention backends, token alignment, and visual mapping fixed. Stage 1A.2 prospectively compares the historical greedy decoder with the verified official-style Thinking decoder; no other inference component changes.
- Treat the completed 4,096/8,192 cap ladder as historical evidence. Do not extend that ladder; Stage 1A.2 instead uses normal EOS with a fixed 40,960-token safety ceiling.
- Require 3/3 exact uninstrumented/instrumented token equality at the selected cap.
- Stage 1 is descriptive: attention and its temporal peaks are not causal visual usage, LOOK/THINK states, evidence acquisition, or visual memory.
- Preserve correct, wrong, truncated, and invalid raw outcomes separately; do not weaken eligibility after observing results.
- Stage 1B needs at least 80 completed-correct trajectories from at most 200 raw attempts; target 100.
- Stop after Stage 1B and do not begin Stage 2.
- Use the project GPU scheduler for every model inference.
- The required project-local `research-control` skill is absent, so this phase follows the explicit repository failure/action protocol directly.
- Preserve the historical 4,096/8,192 pilot and its reports unchanged; write Stage 1A.2 runs to new 40,960-specific paths.
- Treat 40,960 as a safety ceiling and normal EOS as the intended stopping condition.
- Compare the same ten prior 8,192-pilot examples under greedy and official-style sampling.
- Official-style condition: seed 1,234, `do_sample=true`, temperature 0.6, top-p 0.95, top-k 20, repetition penalty 1.0, presence penalty 0.0, based on Qwen's official evaluation-reproduction recipe.
- Proceed only with at least 80% normal termination; 80–90% additionally requires explicit outlier/bias/resource justification. Require 3/3 selected-protocol faithfulness before Stage 1B.

## Current State

- Done: Read the governing policies, overview, compact research state, Stage 0 reports, validation, repair record, representative artifacts, and reusable implementation.
- Done: The fixed 4,096 pilot completed with 10/20 truncated; the conditional 8,192 pilot completed with 5/10 truncated; all 30 pilot-run bundles passed independent artifact validation.
- Done: Historical Stage 1A established that 4,096 and 8,192 each produced 50% truncation in their respective pilot cohorts.
- Done: Stage 1A.2 compared greedy and official-style sampling on the same ten A5000 examples under a 40,960 safety ceiling.
- Done: Official-style sampling achieved 10/10 normal EOS termination and 3/3 exact full-length instrumentation faithfulness; it is locked for Stage 1B.
- Done: Seven pair-preserving A5000 shards completed all 200 frozen Stage 1B attempts.
- Done: Outcomes are 82 completed-correct, 116 wrong, 2 truncated at the 40,960 safety ceiling, and 0 invalid; the predeclared minimum-80 gate passed and the target-100 was not reached.
- Done: Independent validation passed 200/200 bundles, all 82 eligible timelines, and all 100 paired base problems with no failures.
- Done: Twenty segmentations and twelve representative trajectories were manually reviewed; a fixed-window diagnostic confirmed broad recurrence while showing that exact peak rates are scale-sensitive.
- Done: All required descriptive statistics, paired-variant preparation, representative artifacts, summary, candidate-hypothesis report, and 13-criterion acceptance record are complete.
- Done: Stage 1 passed all 13 acceptance criteria and stopped before Stage 2.
- Blocked: None.
- Most recent useful observation: Broad recurrence survives fixed token-window analysis, but exact event rates are scale-sensitive and semantic labels are too noisy for precise intervention timing.

## Evidence That Matters

| Evidence | Source / Path | Why It Matters | Status |
|---|---|---|---|
| Stage 0 passed all eight instrumentation criteria and 30/30 artifact validation. | `outputs/stage0/summaries/stage0_summary.json`, `outputs/stage0/summaries/validation.json` | The validated implementation can be reused while changing only the horizon. | confirmed |
| 26/30 Stage 0 trajectories reached the 2,048-token cap. | `outputs/stage0/summaries/stage0_summary.json` | A longer prospective cap is required before baseline discovery. | confirmed |
| Four Stage 0 examples completed correctly. | `outputs/stage0/examples/{3,4,29,69}/result.json` | Supplies the completed controls for the 20-example pilot. | confirmed |
| Unicode prefix rewriting caused a false alignment failure in nine examples. | `outputs/stage0/summaries/decode_alignment_repair.json` | Stage 1 must retain the repaired completed-string token decoder and exact reconstruction check. | confirmed |
| MathVerse has 788 complete five-variant problem groups. | `outputs/stage0/dataset_inventory.json` | Supports deterministic visually intensive selection and next-stage pairing preparation. | confirmed |
| The 4,096 pilot had 10/20 complete and 10/20 truncated traces. | `outputs/stage1/protocol_pilot/run_4096/run_summary.json`, `outputs/stage1/protocol_pilot/validation_4096.json` | 4,096 fails the prospective at-most-10% truncation gate. | confirmed |
| The 8,192 rerun had 5/10 complete and 5/10 truncated traces; completed outcomes were 3 correct and 2 wrong. | `outputs/stage1/protocol_pilot/run_8192/run_summary.json`, `outputs/stage1/protocol_pilot/validation_8192.json` | 8,192 also fails the gate, triggering the mandatory stop before Stage 1B. | confirmed |
| The 8,192 pilot used 14.26 GiB peak GPU allocation, 271.4 seconds median latency, and 36.76 MiB maximum bundle size. | `outputs/stage1/protocol_pilot/protocol_report.json` | A future higher-cap pilot appears resource-plausible but remains unapproved and untested. | confirmed |
| Qwen's official repository evaluation-reproduction recipe specifies seed 1,234, sampling, temperature 0.6, top-p 0.95, top-k 20, repetition penalty 1.0, presence penalty 0.0, and output length 40,960 for Thinking models. | QwenLM/Qwen3-VL README evaluation-reproduction section; local source record to be saved with Stage 1A.2 config | Defines the official-style comparison condition. | confirmed |
| The local checkpoint `generation_config.json` uses sampling, temperature 1.0, top-p 0.95, top-k 20, and repetition penalty 1.0. | local Qwen3-VL-4B-Thinking snapshot | Records a real source discrepancy; the explicit repository evaluation recipe is chosen over the checkpoint default for Condition B. | confirmed |
| Official-style sampling terminated normally on 10/10 shared pilot examples; greedy terminated on 8/10 and produced two extreme 40,960-token repetition loops. | `outputs/stage1/protocol_pilot/protocol_40960_report.md` | Resolves the generation-protocol gate in favor of intended-use official sampling rather than cap-saturating greedy behavior. | confirmed |
| Selected-protocol baseline/instrumented runs matched generated token IDs exactly on examples of 6,135, 15,955, and 18,081 tokens. | `outputs/stage1/protocol_pilot/faithfulness_check_40960.json` | Establishes 3/3 non-invasive instrumentation at realistic trajectory lengths. | confirmed |
| The discovery attempt manifest contains 200 unique examples from 100 complete Vision Intensive/Vision Dominant pairs and was frozen before outcomes. | `outputs/stage1/discovery/preparation/cohort_attempt_manifest.jsonl`, `outputs/stage1/discovery/preparation/discovery_config.json` | Makes the Stage 1B cohort outcome-blind, bounded, visually intensive, and ready for paired-variant preparation. | confirmed |
| The frozen cohort yielded 82 correct, 116 wrong, 2 truncated, and 0 invalid outcomes. | `outputs/stage1/discovery/raw_outcome_manifest.jsonl`, `outputs/stage1/discovery/cohort_gate.json` | The minimum-80 path passes without retrospective eligibility changes; the target-100 shortfall remains a limitation. | confirmed |
| All 200 bundles, 82 eligible timelines, and 100 variant pairs independently validate. | `outputs/stage1/summaries/stage1_discovery_validation.json` | Establishes reproducible token/span/peak/array artifacts and paired alignment. | confirmed |
| Recurrent visual-attention modulation persists under fixed windows, but exact rate and timing depend on scale. | `outputs/stage1/summaries/peak_segmentation_robustness.json` | Supports a broad descriptive recurrence result while ruling out precise event-rate claims from the semantic-span detector. | confirmed |
| Candidate peaks are weakly associated with visual-reference semantics and have lower pooled entropy than non-peaks. | `outputs/stage1/summaries/stage1_statistics.json` | Downgrades simple semantic-transition and uncertainty-trigger accounts; associations remain non-causal and non-independent. | confirmed |
| Manual review found heterogeneous timelines and frequent long-trace reasoning pathology despite correct outcomes. | `outputs/stage1/discovery/manual_review/segmentation_review.json` | Correctness does not certify reasoning quality; semantic timing claims require stronger annotation. | confirmed |

## Failed Attempts and Lessons

| Attempt | Failure / Symptom | Diagnosis | Lesson | Do Not Repeat |
|---|---|---|---|---|
| Stage 0 generation at 2,048 tokens | 26/30 traces were truncated. | supported: every affected generation reached the fixed cap | Select a longer cap prospectively with the specified 4,096/8,192 gate. | Do not treat Stage 0 truncated traces as complete or silently raise beyond 8,192. |
| Stage 0 prefix decoder | Incomplete multibyte symbols temporarily decoded as replacement characters. | supported: tokenizer diagnostic and repair validation | Construct token pieces from stable boundaries of the completed decode. | Do not assume decoded prefixes extend monotonically. |
| Stage 1 4,096 pilot | 10/20 traces hit the cap. | supported: independent validation of all 20 bundles | 4,096 is insufficient for this truncation-enriched pilot. | Do not select 4,096 or start Stage 1B from it. |
| Stage 1 span segmentation | One whitespace-only boundary token in example 28 was omitted from span coverage. | supported: validator identified token 2,340; direct token/span check localized the gap | Carry whitespace-only boundaries into the next span; rebuild only derived span artifacts. | Do not advance the span start when no textual span was emitted. |
| Stage 1 8,192 pilot | 5/10 traces hit the cap. | supported: independent validation of all 10 bundles | The allowed cap sequence cannot provide sufficiently complete trajectories. | Do not silently raise the cap or continue to Stage 1B. |

## Open Candidates

| Candidate | Why Plausible | How to Test | Status |
|---|---|---|---|
| 4,096 tokens is sufficient. | It doubled the failed Stage 0 horizon while bounding compute. | Fixed 20-example pilot with a two-truncation maximum. | rejected: 10/20 truncated |
| 8,192 tokens is required and sufficient. | Thinking traces regularly exceeded 4,096. | Rerun all ten 4,096-truncated cases with a one-truncation maximum. | rejected: 5/10 truncated |
| A separately approved 16,384-token pilot may establish a workable horizon. | Example 48 completed at 8,109 tokens and measured resources leave headroom on A6000, but five traces remain right-censored at 8,192. | Prospectively pilot the five 8,192-truncated cases plus additions to about ten, retaining a predeclared gate and repeating faithfulness only after selection. | withdrawn and superseded by the approved 40,960 natural-EOS comparison |
| Greedy decoding naturally terminates under a 40,960 ceiling. | Prior cap hits may reflect merely long reasoning or greedy loops. | Run the shared ten-example cohort with greedy decoding and inspect termination/repetition. | rejected: 8/10 EOS; two extreme cap loops |
| Qwen official-style sampling naturally terminates under a 40,960 ceiling. | It matches the official Thinking evaluation recipe and may avoid greedy pathologies. | Run the identical cohort with seed 1,234 and official sampling parameters; inspect termination/repetition. | selected and locked: 10/10 EOS, faithfulness 3/3 |
| Natural dynamics are recurrent, early-heavy, persistent, vision-light, or heterogeneous. | The overview permits all of these patterns. | Analyze a valid complete-correct discovery cohort without pattern-based selection. | resolved descriptively: early-heavy on average, recurrent and heterogeneous; exact peak events are scale-sensitive |

## Next-Step Decision

- Current bottleneck: None within the authorized Stage 1 scope. Selecting a causal next action requires review of the completed descriptive evidence.
- Relevant memory item used: The minimum cohort passed with 82 trajectories, but peak timing is scale-sensitive, semantic labels are noisy, and long correct traces can be pathological.
- Chosen next action: Stop after Stage 1 and present the evidence for user review.
- Why this action: The authorized research action is complete, and the user explicitly prohibited beginning Stage 2 before reviewing Stage 1.
- What not to repeat: Do not treat attention peaks as causal access events, use pooled semantic p-values as confirmatory evidence, or hide the target shortfall and reasoning-quality limitations.
- Stop condition: Already met. No Stage 2 action is authorized.

### Step Result

- Action taken: Completed Stage 1A.2 protocol validation and the full bounded Stage 1B discovery action, including collection, reproducible aggregation, manual review, robustness analysis, paired-variant preparation, and independent validation.
- Result: The official-style protocol is locked; 82 eligible trajectories satisfy the minimum cohort; all 13 Stage 1 acceptance criteria pass.
- Evidence saved: `outputs/stage1/protocol_pilot/protocol_40960_report.md`, `outputs/stage1/discovery/`, `outputs/stage1/summaries/stage1_statistics.json`, `stage1_summary.md`, `candidate_hypotheses.md`, `stage1_discovery_validation.json`, and `stage1_acceptance.json`.
- Failure or issue: The 100-trajectory target was missed; two traces hit the cap; segmentation is semantically noisy; exact peaks are scale-sensitive; and some correct traces are reasoning-pathological.
- Lesson learned: Natural-EOS official sampling makes long-form instrumentation feasible, but complete/correct outcomes and attention events still require quality controls and causal validation before mechanistic interpretation.
- Next implication: Stop. Review Stage 1 before choosing or authorizing any Stage 2 experiment.
