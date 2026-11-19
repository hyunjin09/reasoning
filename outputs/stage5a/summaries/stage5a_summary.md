# Stage5A: failure and attention-state taxonomy

**Technical PASS:20/20. The matched high-attention alignment/mirage hypothesis is
not confirmed.** Stage5A completes the200-base natural census,128-base causal
atlas and all feasible frozen assays. It establishes a broad source-dependence
record and13 reviewed integration-error events on7 bases. Strict alignment-only
and mirage confirmation cohorts have zero yield; their inferential comparisons
remain unrun. The sole next recommendation is a **Stage5B failure-rescue
feasibility review**, with no rescue experiment started.

The research question is whether similar visual attention can reflect semantic
alignment, causal retrieval, verification/refresh, or distinct visual failures.
The hypothesis predicts different causal and internal states at matched
attention magnitude. Semantic and causal labels were frozen before passive
features; wrong final answers never served as visual-hallucination labels.

## Cohorts and execution

| Cohort / subset | Bases | Selected events |
|---|---:|---:|
| Natural census |200|550|
| Causal atlas |128|347|
| Discovery |32|80|
| Fresh confirmation |96|267|
| Semantic/sham subset |48|85|
| Fixed R16 subset |96|256|

The natural cohort is the first200 eligible bases in the frozen screen, without
correctness balancing. It ends at screen208.210 screen positions were manually
reviewed, nine duplicate stimuli were excluded, and one further eligible reserve
was retained outside the natural cohort. All200 retained variants are Vision
Dominant; this is a selected-event MathVerse census, not exhaustive trace-error
or general multimodal population prevalence. The atlas contains63 bases with a
selected local error and65 others under the frozen fill rule. Historical anchors
remain separate:48 compatible Stage4A bases contribute144 discovery-reference
events, not fresh prevalence observations.

The fixed initial budget was800 and the maximum1400.551 exact-protocol existing
native trajectories were indexed for possible reuse. Fresh acquisition preserved
213 completed outcomes and stopped after the genuine cohort
freeze: one rank finished its planned shard; three stopped between trajectories.
Unused reserves are preserved. No post-effect population expansion occurred.

All new GPU work used the existing tmux9 / Slurm108548 allocation on node07:
exactly four RTX A6000 GPUs. No new Slurm allocation, package installation or
CUDA_VISIBLE_DEVICES assignment was made. The user's replacement-allocation
authority was not needed. Model loading uses the existing project `.venv` and
Qwen3-VL-4B-Thinking checkpoint; native generation settings and dataset assets are
unchanged.

The source assay uses BF16, canonical2048-token streaming prefixes, eight fixed
single-query barriers, W2 primary and W8 target sensitivity, all36 layers/all32
heads. Removing selected source-value terms leaves Q/K/V and native attention
unchanged; no attention renormalization occurs. R16 removal is restricted to
layers16–23, the current query and up to16 strictly preceding reasoning tokens.
Passive telemetry uses both late layers28–29/all32 heads and an independently
replayed t−8 prior. Historical selected heads are descriptive coordinates only.

## Natural census and source evidence

The550 selected events include386 locally correct,94 incorrect,20 undecidable
and50 without an explicit visual claim.64/200 bases contain at least one selected
incorrect local claim;121/200 final answers are correct and79 wrong. Base-level
semantic categories can overlap. The atlas scores92 of the94 selected incorrect
events, covering63 of the64 affected bases. The remaining base and unresolved
mechanisms are explicitly unascertained.

The347 atlas events have216 demanded-source-dominant profiles,17 alternative
dominant,65 mixed-support,38 weak under both W2 and W8,17 broader-window-dependent,
and66 unresolved profiles. These labels overlap. Large negative effects are not
nulls. Median within-base mean VSD_T is1.2655 nats/candidate-token; median W8_T is
1.4821. There are237 X arms,267 validated I arms, and five raw M arms on four
bases. Only two M events have an independent T/M contrast; the other three
overlap. They do not yield a strict alignment-only cohort.
I controls match ROI cardinality and use reviewed background regions; they are
not ink-matched to printed labels. Their selection and exclusions are preserved.

The48 semantic bases meet the minimum48, below target64. The conservative numeric
construction was exhausted over92 eligible atlas bases:164 source proposals,
85 constructed assets,79 construction failures, and six manual rejections.
The79 accepted source assets yield85 validated event readouts. Semantic and sham
images preserve the frozen token layout; factorial edits use disjoint reviewed
source regions where available.82/85 event effects exceed absolute sham by0.05;
the median base-mean CE-minus-absolute-sham is12.8013. All48 base means are positive.
The subset chiefly covers numeric labels and cannot validate arbitrary wrong
entity bindings. Effects from editing another source on the target readout are
cross-source controls, not alternative-fact semantic readouts.

The96-base R16 subset has134/256 target trigger effects above0.05 and a median
base-mean effect of0.1979. These are secondary source-dependence changes; trigger
generalization is not required for retrieval labels. Temporal review resolves
121 first-use,19 reuse and four refresh events;203 remain unresolved. Selected
event order was never substituted for full native history. Fixed-history image
counterfactuals do not localize when visual information was first acquired.

## Failure diagnoses and readout limits

| Operational label | Events | Bases | Confidence tiers |
|---|---:|---:|---|
| H-NR | 0 | 0 | {} |
| H-MR | 10 | 9 | {'Tier2': 10} |
| H-SC | 1 | 1 | {'Tier1': 1} |
| H-ST | 0 | 0 | {} |
| H-INT | 13 | 7 | {'Tier1': 5, 'Tier2': 8} |

H-INT is separate from visual hallucination. Its13 events have correct local
claims, demanded-source dependence, a wrong final answer and an explicitly
reviewed later error. An error already present before the selected event does
not qualify as its downstream error. The single H-SC example108_E1 claims CD=5
although the image says8: VSD_T=5.0000, semantic CE=6.6250 and sham shift=0.
It is a convergent extraction-error example, not a population-level class.

The10 H-MR labels are **frozen margin-based source profiles**, all Tier2. D is
the ground-truth candidate's mean log probability minus the foil's; the actual
native candidate direction is separately stored. Alternative-source dominance
on this margin does not establish that the alternative source caused the wrong
token. One saved-score validity diagnostic found only1/10 wrong-token
contributions above0.05. Alternative-source removal increases wrong-token
probability in7/10 and worsens the correct-versus-wrong margin in all10.
Two remaining positive wrong-token contributions are below0.001. Frozen labels
are preserved, but a wrong-source rescue mechanism is not inferred from them.
See the [orientation audit](../audit/hmr_readout_orientation_diagnostic.json).

Zero H-NR/H-ST diagnoses do not establish their absence. H-NR needs measured
semantic null evidence; missing counterfactuals are not nulls. H-ST additionally
needs an actual prior-source history, and only four refresh opportunities were
resolved. Subtype counts inside the natural200 are ascertained lower bounds;
atlas counts are not presented as an unbiased mechanism prevalence estimate.

## Attention confirmation and separability

Discovery-only normalization preserves source class and ROI-size buckets and
merges only adjacent progress/length buckets until eight reference ROIs are
available. The high criterion is a matched density percentile of at least0.90.
Both mass and density retain raw values, matched z scores and percentiles. The
ROI source class was prospectively normalized from the reviewed source kind;
the original base evidence type remains available. Sparse matching stays
unresolved rather than borrowing a different source class or ROI size.

211/347 atlas events have a matched target reference, including139/267 held-out
events.19 confirmation events cross the high-attention criterion. There are
zero strict mirages, zero high-attention missing-CE candidates and zero strict
alignment-only events. Alignment–retrieval and mirage–retrieval matched families
therefore have no pairs. Their six slots each remain unrun with p=1. The broad
semantic-mention/retrieval2×2 is reported separately; a mention without demanded
retrieval is not automatically a strict alignment-only mechanism.

Only grounded-correct versus locally wrong visual claims has sufficient
classifier yield. Models use fixed regularization, whole-template folds, no
base/event leakage and train-fold imputation/scaling. The confirmation data
contain76 grounded-correct and51 hallucination base/class observations, with
overlap because one base can exhibit both states. Predictions are averaged
within base/class, and bootstrap intervals resample unique bases together.

| Features | Balanced accuracy | Macro F1 | AUROC | ECE10 |
|---|---:|---:|---:|---:|
| F1 | 0.843 | 0.838 | 0.908 | 0.051 |
| F2 | 0.892 | 0.887 | 0.929 | 0.070 |
| F3 | 0.882 | 0.872 | 0.933 | 0.058 |
| F4 | 0.862 | 0.849 | 0.953 | 0.110 |
| F5 | 0.928 | 0.927 | 0.954 | 0.025 |

F1 attention-only balanced accuracy has a base-bootstrap95% interval
[0.771, 0.908];
F5's interval is[0.879, 0.970].
These are descriptive held-out prediction results. F4/F5 contain causal features
that partly define grounded labels, so their performance is circular as
independent mechanism evidence. Feature/ROI availability and event selection can
also carry contextual information. The other three classifier tasks are
insufficient. PCA is fitted on discovery F3 and projected descriptively; clusters
do not define the taxonomy.

The two independent M candidates retain their already-scored W2 local NLL and
demanded-margin effects as descriptive evidence. Zero meet strict alignment-only
qualification, below the32-event minimum. The dedicated utility experiment,
including its distinct final-candidate margin, is unrun. Local D is not
substituted for final-answer utility.

Sink mass, t−8 release and source-group gains/losses are retained for all347
events. Matched sink confirmation has only two pairs. The sink gate is not met;
generic attention magnitude, replication and behavioral relevance are not
established. No sink manipulation occurred. Major comparisons include local and
global correctness strata and leave-one-template-out sensitivity; low yield is
reported rather than ignored.

## Claim assessment and next action

- **O1: not_confirmed** — No strict alignment-only or mirage confirmation cohort; no primary matched pairs.
- **O2: limited_support** — 216 demanded-source-dominant events and82/85 positive semantic readouts; no new matched internal-signature comparison established.
- **O3: not_confirmed** — Zero strict cases under the frozen criterion;139/267 confirmation events matched and128 unresolved.
- **O4: illustrative_only** — 10 Tier2 margin-based H-MR profiles and one Tier1 H-SC case; error-specific readout audit prevents treating all H-MR profiles as causal error sources.
- **O5: case_level_supported** — 13 reviewed later-error events on7 bases have correct local claims and demanded-source dependence.
- **O6: unrun_insufficient** — Only2 independent M candidates and0 strict alignment-only events; minimum32 not met.
- **O7: gate_not_met** — Two matched confirmation pairs; no robust held-out or behavior-linked sink evidence.

The single recommendation is **HOLD — Stage5B failure-rescue feasibility review**
of error-specific readouts and source identity on the nine H-MR candidate bases.
The10 events fall below24 and do not yet form a coherent error-promoting source
class. This review-only recommendation is detailed in
[next_stage_recommendation.md](next_stage_recommendation.md). No new stage,
rescue, sink intervention or representation substitution was started. The
project-local research-control skill was unavailable; this stage followed the
user's fully specified plan and fixed gates, and the proposed review is not
executed as an autonomous follow-on action.

## Verification and reproducibility

- 15/15 mechanical checks on8 historical bases,24 events and312 arms.
- 23/23 final artifact checks;2736 frozen/raw hashes verified.
- 764 causal/semantic event-image files,3182 scored arms and243776 source calls.
- 347 fresh passive event files, each with a current and t−8 state; all347 native
  candidate/logit replays exactly match the causal run. All85 semantic native
  readouts also replay exactly.
- 31 CPU tests pass, covering taxonomy guards, native spans, source masks,
  controlled edits, grouped-KV telemetry, matching, Holm and grouped classifiers.
- 20 standalone PNG/PDF figure pairs. Raw vectors, per-head metrics, source token
  identities, exact preceding text-entity matches where available, text-control
  QK summaries and late residual norms remain available. Pooled key summaries
  are descriptive; no representation-equivalence or substitution claim is made.

All new implementation is under `scripts/stage5a` and
`code/visual_reasoning/stage5a`; historical causal runtimes are unchanged.
Original prospective config files are preserved with explicit pre-score
amendments. The first semantic completion audit ran before the last rank
finished and correctly rejected incomplete coverage; the completed audit passes.
The first final resource audit incorrectly required every generation rank to
stop at the freeze; one had completed its entire shard earlier. Its preserved
failure log and the corrected complete-or-frozen-stop check document the repair.
Neither required a GPU rerun or a changed scientific label.

Reproduction entry points: `audit_scores.py`, `freeze_causal_labels.py`
(create-once), `run_passive.py`, `analyze_passive.py`, `analyze_taxonomy.py`,
`make_figures.py`, `audit_results.py`, and `make_report.py`, all in
`scripts/stage5a`. GPU entry points require the recorded allocation and gates;
they must not be launched on a login node. The complete evidence is in
[mechanics](../audit/mechanical_validation.json),
[final audit](../audit/final_artifact_validation.json),
[resources](../audit/resource_summary.json),
[acceptance](stage5a_acceptance.json), and
[source summary](../analysis/source_summary.json).

## Figures

1. [An attention-independent taxonomy](../analysis/figures/01_taxonomy_overview.png) ([PDF](../analysis/figures/01_taxonomy_overview.pdf)). A–D labels were frozen before fresh passive extraction. Attention is a phenotype, not the causal label.
2. [Natural cohort: 200 bases, 550 selected events](../analysis/figures/02_natural_prevalence.png) ([PDF](../analysis/figures/02_natural_prevalence.pdf)). Semantic/local categories overlap at the base level; the census covers up to3 selected events per trajectory.
3. [Demanded, alternative and irrelevant source dependence](../analysis/figures/03_source_profiles.png) ([PDF](../analysis/figures/03_source_profiles.pdf)). Signed unnormalized effects are primary. A large negative effect is not a null; overlapping profiles are not independent counts.
4. [Alignment versus retrieval: confirmation feasibility](../analysis/figures/04_alignment_matched.png) ([PDF](../analysis/figures/04_alignment_matched.pdf)). The strict independently mentioned M definition was retained; generic visual claims were not relabeled as alignment-only.
5. [Grounded-correct versus locally wrong visual claims](../analysis/figures/05_attention_causal_separation.png) ([PDF](../analysis/figures/05_attention_causal_separation.pdf)). Descriptive classification, aggregated within base/class. F4/F5 include causal features that partly define grounded labels; scores do not validate a mechanism.
6. [QK, value transport and causal dependence by state](../analysis/figures/06_state_signatures.png) ([PDF](../analysis/figures/06_state_signatures.pdf)). Base means within each descriptive display state. The underlying labels can overlap; the display uses an explicit priority order.
7. [First retrieval, verification and refresh](../analysis/figures/07_temporal_states.png) ([PDF](../analysis/figures/07_temporal_states.pdf)). Only full-native reviewed histories receive temporal roles. Four refresh opportunities do not support population inference about stale-source failures.
8. [Mirage confirmation under the frozen rule](../analysis/figures/08_mirage_confirmation.png) ([PDF](../analysis/figures/08_mirage_confirmation.pdf)). Zero confirmed cases does not establish absence: matching coverage and clean semantic-edit feasibility limit ascertainment.
9. [Causal failure decision tree](../analysis/figures/09_failure_decision_tree.png) ([PDF](../analysis/figures/09_failure_decision_tree.pdf)). Wrong final answers do not enter the hallucination branch automatically. Missing semantic controls cannot establish a semantic null.
10. [Natural-cohort failure subtype ascertainment](../analysis/figures/10_natural_subtype_ascertainment.png) ([PDF](../analysis/figures/10_natural_subtype_ascertainment.pdf)). Counts are ascertained lower bounds from the nested causal atlas, not a correctness-balanced atlas prevalence estimate. Categories can overlap; unclassified errors remain unresolved.
11. [Causal profiles of failure subtypes](../analysis/figures/11_failure_causal_profiles.png) ([PDF](../analysis/figures/11_failure_causal_profiles.pdf)). H-NR and H-ST have no diagnosed cases. H-MR is Tier2; its alternative-fact semantic readout is unavailable. H-SC108_E1 is Tier1.
12. [13 locally grounded integration-error events on7 bases](../analysis/figures/12_integration_failures.png) ([PDF](../analysis/figures/12_integration_failures.pdf)). A reviewed error must occur after the selected event. These events are not visual hallucinations solely because the final answer is wrong.
13. [Sink behavior is descriptive](../analysis/figures/13_sink_states.png) ([PDF](../analysis/figures/13_sink_states.pdf)). Only2 attention-matched confirmation pairs; all sink gate conditions are unestablished. No sink intervention was performed.
14. [Fixed recent-reasoning trigger by state](../analysis/figures/14_trigger_states.png) ([PDF](../analysis/figures/14_trigger_states.pdf)). 256 events from the frozen96-base subset. Trigger dependence is secondary and is not required for retrieval labels.
15. [Existing mentioned-source arms: descriptive utility only](../analysis/figures/15_alignment_utility.png) ([PDF](../analysis/figures/15_alignment_utility.pdf)). The 2 independent M candidates were scored in the frozen causal run; they are not silently promoted to an alignment-only cohort. Other overlapping M maps are excluded from this contrast.
16. [Helpful, benign or interfering: qualification remains necessary](../analysis/figures/16_alignment_candidate_examples.png) ([PDF](../analysis/figures/16_alignment_candidate_examples.pdf)). Labels describe the sign of the existing M-removal effect. None of these examples meets the strict alignment-only criterion.
17. [Template concentration limits generality](../analysis/figures/17_template_robustness.png) ([PDF](../analysis/figures/17_template_robustness.pdf)). All leave-one-template-out primary matched comparisons remain insufficient; concentration is descriptive, not a substitute for replication.
18. [Held-out feature ablation: one adequately sized task](../analysis/figures/18_heldout_ablation.png) ([PDF](../analysis/figures/18_heldout_ablation.pdf)). Alignment/retrieval, retrieval/mirage, and failure-subtype tasks are insufficient. Only grounded-correct versus wrong visual claims is scored, with whole-template folds.
19. [Representative high-attention confirmation states](../analysis/figures/19_high_attention_examples.png) ([PDF](../analysis/figures/19_high_attention_examples.pdf)). First event ID within each observed state; illustrative cases are not matched causal contrasts. No alignment/mirage exemplar is manufactured.
20. [Attention requires semantic and causal qualification](../analysis/figures/20_conceptual_conclusion.png) ([PDF](../analysis/figures/20_conceptual_conclusion.pdf)). Conceptual possibilities are distinguished from observed diagnoses. Stage5A does not confirm the stronger matched alignment/mirage headline.
