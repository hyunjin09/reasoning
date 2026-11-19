# Stage8B Block2 — retrieval-event local-read success/failure

Completed 2026-09-19. **No robust earliest computational divergence is established.**
The earliest coherent **descriptive candidate is source routing**, followed by
source ambiguity. The frozen census yields only17 L− events in16 families,
below the prespecified24-failure minimum. This result is not activation
equivalence, causal misrouting, or confirmation that routing causes errors.

## Frozen scope and yield

Block0/1 artifacts, all256 MathVision items, detector, threshold
0.5478025980771918, gap4 episodes, and exact456 review members were preserved.
No native generation, extra event selection, detector refit, image intervention,
or Block3 execution occurred. The original plan and the pre-annotation
[execution protocol](../../../plan/stage8b_block2_execution_protocol_v1.md)
remain unchanged.

| Review result | Events | Unique image families |
|---|---:|---:|
| All selected episodes |456|214|
| T: task-required immediate visual claim |148|127|
| M: mention/restatement/nonvisual |253|171|
| U: demand unresolved |55|52|
| L+: locally correct T |120|107|
| L−: locally incorrect T |17|16|
| L?: local outcome unresolved |11|11|
| Source-localizable L+ |101|90|
| Source-localizable L− |12|11|
| Source-localizable L? |4|4|

The42 items without selected episodes remain in the256-item cohort. Family
counts across local classes overlap and must not be added as independent units.
The456 evidence-backed records were sealed before feature contrasts and replay.
Geometric box corrections were recorded in a separate pre-seal amendment;
original review files were preserved. Shared visual-token cells were excluded
symmetrically, without attention-based geometry changes.

## Observational replay and comparisons

Replayed all12 source-localizable failures plus9 fixed correct-read controls:
21 events in18 items. The9 pairs span15 families and7 connected family
components;8 pairs also match completion exactly. Three failures were retained
unmatched. One control has no confuser: target–confuser paired contrasts have
8 complete pairs, while rank/share/ambiguity have9 pairs. The available-case
matched target–confuser summaries contain8 L+ and9 L− events; the paired
estimates below handle that missingness explicitly.

All21 captures had bit-identical logits versus untouched queries on the same
prefix, and **zero difference** from saved native global passive features.
Original images, input/pixel hashes, native token IDs and one-token cached
prefixes were verified. Model execution was BF16; source-vector diagnostic
reductions were FP32. These are passive measurements, with no altered forward
output, source suppression, switching or patching.

Analyses were written in the frozen order: activation → routing → ambiguity →
transport. Inference resamples complete image families4000 times, seed1234;
paired sensitivity resamples connected family components. Simultaneous
intervals cover metrics within each primary family. All intervals remain
descriptive because the failure-yield gate failed.

| Measure | L+ mean | L− mean | L− minus L+ |95% simultaneous interval|
|---|---:|---:|---:|---|
| Retrieval score at onset, all120/17 |0.5837|0.5794|−0.0043|[−0.0203,0.0118]|
| Target−confuser QK, available matched8/9 |1.8457|0.5561|−1.2895|[−1.9266,−0.6525]|
| Target−confuser attention share, matched8/9 |0.3188|0.0876|−0.2312|[−0.3749,−0.0875]|
| Target visual share, matched9/9 |0.4099|0.1869|−0.2230|[−0.3872,−0.0587]|
| Candidate-source entropy, matched9/9 |0.5827|0.7800|0.1973|[0.0530,0.3416]|
| Top-two source margin, matched9/9 |0.6928|0.3560|−0.3368|[−0.5389,−0.1347]|
| Cross-head target consensus, matched9/9 |0.8924|0.6771|−0.2153|[−0.4155,−0.0151]|

None of the four primary activation intervals excludes zero; this does not
establish equal activation. Complete-pair target–confuser effects agree in
direction: QK−1.2054, interval[−1.6815,−0.6077]; attention-share−0.2295,
interval[−0.3442,−0.1059]. Family/class-mean sensitivities also retain the
routing/ambiguity directions. Target rank is less decisive: matched mean
rank1.00 versus1.22, with an interval including zero for the contrast.
Most replayed failures still have the target as their top annotated region.
Weaker selectivity must not be renamed WRONG_SOURCE_READ or causal misrouting.

Descriptive target alphaV and post-W_O norms are smaller in the failure group;
total visual transport, visual/residual ratio, cancellation and Value-direction
cosine do not form a clear independent transport deficit. Source contribution
magnitudes depend on routing and ROI extent and are not grounding scores.

## Local versus final outcomes

| Local read | Final correct | Final wrong | Final unresolved |
|---|---:|---:|---:|
| L+ |58|62|0|
| L− |9|7|1|
| L? |3|8|0|

These are event counts clustered by family, not separate native examples.
The9 L−/final-correct and62 L+/final-wrong events are candidates for later
recovery/downstream-use analysis; those mechanisms were not diagnosed here.

## Identifiability and implementation limits

- This is a single-agent semantic review. Packets hid final labels and feature
  values, but the annotator had prior project context; no independent-blinding
  or inter-rater-reliability claim is made.
- The frozen earliest-claim rule often selects a coarse correct shape/layout
  before later detailed mistakes. This measures the selected immediate claims,
  not every visual error in a trajectory. No later error was substituted to
  increase failure yield. Twelve T readout anchors precede episode onset;
  onset/episode contrasts are concurrent descriptions, not validated predictors.
- Early records lack the optional matching-subtype field:21 L+,3 L−,2 L?.
  The three affected localizable failures (2299,1833,2450) therefore remained
  unmatched under exact recorded strata, and were still replayed. Missing
  subtype metadata were not imputed after results opened. ROI-type granularity
  also varies across records. This restricts the matching interpretation.
- Full adjustment is unavailable: activation has31 design columns but only16
  L− families; routing has20 columns and rank17 with11 L− families. Matching
  does not establish balance on all nuisance variables. One pair crosses
  completion classes, and duration/length residual differences remain.
- Source sets contain only2–3 annotated regions. QK uses log-mean-exp to account
  for token count; raw attention share and transport still depend on ROI area.
  Source identity/localizability does not establish causal identifiability.
- All148 reviewed T claims have active retrieval within±32 tokens, and253/456
  selected events are M. Both are conditional on retrieval-selected membership.
  Population missed-demand coverage and all-token unnecessary-retrieval rates
  are unidentifiable; the100% conditional coverage is not population recall.
- Only three trajectories have multiple replayed anchors. Their candidate
  inventories change, so continuous lag, stale-source persistence, oscillation
  and comparable source-transition accuracy remain unavailable. Sparse exact-ROI
  sequence agreement is only an operational descriptive observation.

## Deliverables and resources

All12 required outputs are in this directory. Five figures are available as
PNG and PDF under [figures](figures/): activation, routing, ambiguity,
head/layer agreement, and local×final outcomes. Complete semantic records,
geometry amendments, native-prefix receipts and analysis tables are retained.

Scheduler job `stage8b_block2_replay_node06_v1`, Slurm118076, used two distinct
RTX A6000 GPUs on node06. It completed with exit0 in4m49s
(approximately0.161 allocated GPU-hours). The initial60GB host-RAM request
was reduced to48GB while pending to fit available node memory; GPU count and
scientific configuration were unchanged. Peak observed GPU allocation was
6.26GiB per worker. Both GPUs were automatically released at completion.
The review-record interval was about41 minutes of main-agent annotation,
excluding preparation and analysis. Slurm accounting storage is disabled;
the final `scontrol` receipt and worker environments preserve runtime evidence.

## One handoff emphasis, then stop

For a separately authorized Block3, emphasize **post-read recovery and evidence
use after weak target–confuser separation**, retaining local/final-outcome
crossings and the existing source/annotation uncertainties. The source-routing
pattern is a hypothesis to follow, not a confirmed failure mechanism. Block3,
causal interventions, new examples, and further GPU jobs were not launched.
