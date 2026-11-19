# Stage10B: recurrent visual-demand census

**STRONG GO: 26 clean candidate trajectories among 224 eligible.** 37 trajectories satisfy the semantic C1–C4 criteria. These are passive candidate associations; this stage does not establish causal reopening or repeated visual/textual phase alternation.

## Corpus and execution

All128 frozen Stage9A MathVision and96 Stage8A main MathVerse native Qwen3-VL-2B-Thinking trajectories were retained. No correctness, detector, length or intervention-outcome selection was applied. The corpus contains 3,803,022 reasoning tokens. No exact image duplicates were found; conservative problem/image trajectory is the independent unit. Capped/abnormal runs remain observed-prefix evidence. No original trace was modified or regenerated.

Two independent model-agent semantic passes reviewed the question/image/reasoning packets without routing, accuracy or causal outcomes. Main-agent adjudication sealed A, the text interval, B onset/identity, prior availability and ROIs before passive values were opened. The second passes then reviewed target-specific routing under the frozen32-token rule. Long negative traces were screened through demand/observation passages and context; this is not exhaustive human token-by-token annotation. Positive candidates received full prior-text verification. Reported yields are operational explicit-demand census estimates for these corpora.

## Trajectory-level endpoints

Percentages have Wilson95% intervals. Events/windows from one trajectory are never independent samples.

| Source | E1: C1–C5 / eligible | E2: C1–C4 / eligible | E3: C5 given C1–C4 |
|---|---|---|---|
| MathVision | 15/128 = 11.7% [7.2, 18.4] | 21/128 = 16.4% [11.0, 23.8] | 15/21 = 71.4% [50.0, 86.2] |
| MathVerse | 11/96 = 11.5% [6.5, 19.4] | 16/96 = 16.7% [10.5, 25.4] | 11/16 = 68.8% [44.4, 85.8] |
| Pooled | 26/224 = 11.6% [8.0, 16.5] | 37/224 = 16.5% [12.2, 21.9] | 26/37 = 70.3% [54.2, 82.5] |

Timing among clean primary events: n=26, median=0.0, IQR=[0.0, 6.0] generated tokens after B onset. Lag is the onset of the qualifying routing run; an explicit observation may occur elsewhere within the same32-token window. The complete0–31 distribution is saved in the inference JSON and Figure3.
Taxonomy (earliest clean event per trajectory): {'S1': 26, 'S2': 0, 'S3': 0}. Additional clean events (33 total events) are secondary.

Using the strongest annotated topology among all clean events in each trajectory (secondary): {'S1': 21, 'S3': 5}. No clean S2 return recurrence was identified; the plan permits Strong GO from S1 cases.

Unresolved target/routing coverage affects 4 semantic-positive trajectories. The observed-to-best-case missing-data yield bounds are [0.11607142857142858, 0.13392857142857142]; these bounds are not confidence intervals. Missing routing and unlocalizable targets are not evidence of absent re-access.

## Agreement and preserved negatives

Raw independent labels are preserved separately from adjudication. Agreement between model-agent passes is not independent human-rater reliability.

| Measure | n | Raw agreement | Cohen kappa |
|---|---:|---:|---:|
| semantic_trajectory | 224 | 0.9151785714285714 | 0.6497695852534561 |
| availability_matched | 45 | 0.9333333333333333 | 0.785031847133758 |
| availability_union | 157 | 0.267515923566879 | 0.1077341240425006 |
| C5_event | 157 | 1.0 | 1.0 |
| clean_trajectory | 224 | 0.9553571428571429 | 0.7378277153558056 |

Onset agreement within±8 tokens: 36/45 (0.800). Source identity: 43/43 (1.000). Acceptable for Strong GO: True. Detection/onset/availability/interval/source disagreements and resolutions are retained in the agreement/adjudication artifacts.

Event-union availability agreement is low because 112 of157 retained event groups were nominated by only one pass, including repeated already-textualized and partial negative cases. Matched-event availability passes the prospectively frozen gate, but broad event-inventory agreement remains a limitation. C5 agreement uses shared adjudicated targets and does not erase semantic detection disagreements.

| Primary negative category | Independent trajectories |
|---|---:|
| B_ALREADY_TEXTUALIZED | 111 |
| NO_RESOLVED_VISUAL_A | 49 |
| NEW_DEMAND_NO_REACCESS | 7 |
| NO_TEXT_INTERVAL | 9 |
| NO_NEW_REQUIRED_DEMAND | 5 |
| TARGET_AMBIGUOUS | 17 |
| ATTENTION_ONLY | 0 |
| TRACE_TOO_SHORT | 0 |
| ROUTING_DATA_MISSING | 0 |

## Measurement and interpretation limits

C1 means that a visual fact/subgoal is semantically resolved in the trace; it does not certify factual correctness or visual causation. C2 permits a distinct derived conclusion even when shorter than24 tokens. Requiring at least24 tokens from the end of the A quote to B onset descriptively leaves 24 clean trajectories and 34 semantic-positive trajectories. This raw anchor-gap sensitivity is not a pure text-interval duration estimate or replacement primary rule. Completion and length-quartile results, target types and dataset strata are included in the inference JSON.

C5 requires at least two consecutive target-selective measurements (target/control patch-mean ratio≥1.5 and within-image target mass≥.05), plus frozen detector positivity or an explicit B observation within32 tokens. These prospective screening thresholds are not a validated causal classifier. Detector positivity alone and raw global image attention do not qualify. Historical MathVision routing uses unchanged layers19–22 and the frozen Stage8A detector. MathVerse historical event summaries do not supply arbitrary new-B patch routing. Passive repair was used for 14 trajectories; it teacher-forced frozen prefixes with64-token eager chunks and checked observer/no-op feature/logit/cache behavior. Original native per-query routing for those traces was not saved, so reconstruction is explicitly distinguished from historical observation.

A low yield can reflect task distribution, already-textualized evidence, continuous inspection, model behavior, operational annotation limits or routing identifiability. It is not proof that recurrent perceptual demand is impossible. Stage10AR single-transition evidence and Stage4A source retargeting remain separate findings.

## Resources and deliverables

New GPU allocation: **0.0167 GPU-hours**; 14/32 maximum passive-repair trajectories. New generations:0. Causal interventions:0. All Stage10B GPU jobs are terminal. Annotation burden: 448 independent reviewer–trajectory judgments plus main adjudication; human labor hours were not measured.

All11 required artifacts are present in this directory; optional passive-repair data are included only when executed. Four standalone PNG/PDF figures are under `figures/`. Raw passes, semantic seals, routing evidence, provenance checks and resource receipts are under `audit/` and `annotations/`.

## Exactly one recommendation

Run a bounded causal reopening experiment on the frozen clean recurrent-demand cohort, testing whether visual necessity and source-specific causal dependence rise after the new B demand.

**STOP:** no causal follow-on, new model, benchmark or synthetic construction was launched.
