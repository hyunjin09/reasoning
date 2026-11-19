# Stage8B Block3B — post-read lifecycle analysis

Status: **completed at the prescribed sparse-coverage / inconclusive-result stop boundary**.
No robust post-read mechanism was established. This is not evidence that mutation,
refresh, or recovery has no effect: semantic coverage and symmetric exposure are
too limited for that conclusion. No new research action was launched.

## Scope and validity

The frozen 256 MathVision items, 456 Block2 reviews and 148 T anchors remain unchanged:
120 L+, 17 L−, 11 L?, spanning 127 items and 126 conservative analysis families.
The 1707/1245 image alias is clustered together. All 148 anchors received masked
lineage review and quote validation before outcomes/passive values were joined.
There was one annotator, not an independent blinded panel.

Only 16 anchors had complete remainder review; 132 used source-reference windows
and concluding text. Thus witnessed reuse is not a full persistence certificate,
and failure to find a mutation/correction is not coded 0. This is a limitation of
the performed annotation coverage, not proof that the remaining text is inherently
unannotatable. The two mutation witnesses are 2 different families; the three
correction witnesses are 3 different families. All original evidence is preserved.

## Main comparison: L+ / final wrong minus L+ / final correct

| Endpoint | Eligible events / families | Adjusted difference | Multiplicity-adjusted 98.75% CI |
|---|---:|---:|---|
| mutation | 16 / 13 | 0.08117 | unavailable |
| refresh_compliance128 | 1 / 1 | not identifiable | unavailable |
| reretrieval128 | 120 / 107 | -0.02149 | [-0.2413, 0.1931] |
| delta_tortuosity256 | 27 / 24 | -47.29 | unavailable |

New retrieval within 128 tokens was observed at family-weighted rates
78.0% in final-correct and 73.7% in final-wrong traces.
The adjusted difference was -2.15 percentage points
(98.75% CI -24.13 to 19.31). This does not distinguish the groups reliably.
The first-eligible-event and normal-completion sensitivities also include zero.

Mutation: 2 observed positives, 14 full-review negatives, 104 unknown among 120 L+.
One mutation occurred in a final-correct item 1833 (die top-face 1→2), one in
final-wrong item 1017 (notch bottom→top). Unequal ascertainment prevents treating
complete-case rates as population incidence. The adjusted mutation bootstrap had
only 871/4000 valid replicates, below the frozen 95% rule.

Refresh: three certified reuse gaps across two anchors were recorded, including
one semantically ambiguous refresh interval. Only one anchor had an identifiable
128-token compliance denominator with resolved refresh status; no outcome contrast
is possible. Explicit verbal reinspection without detector support is kept apart
from a stale-reuse certificate. 7/12 reviewed source-engagement spans have nearby
frozen detector episodes; these are sparse temporal alignments, not causal grounding.

## Pre/post wandering and vSTREAM bridge

Full symmetric 256-token exposure covers 27 L+ events /24 families (12 correct, 15 wrong)
and 7 L− events. The 128/512 sensitivities contain 42/19 L+ events.
The primary raw wrong-minus-correct delta was 19.46 tortuosity units, with a wide
interval crossing zero; adjustment reversed the point estimate and only
2477/4000 bootstrap draws supported a nonsaturated identifiable fit.
Its interval is therefore withheld. No controls, anchors or windows were loosened.

The exploratory L− minus L+ post-minus-pre contrast is negative in the raw data,
not the hypothesized increase after local error. Its fully adjusted interval
includes zero and is very wide. With only seven exposed L− events, it establishes
neither a precursor nor a consequence of local failure. Secondary paired changes,
alternate windows, claim-start anchors and low-displacement exclusion are saved.
The representation is the frozen four standardized retrieval features, not a
hidden-state vSTREAM replication.

## Recovery and downstream evidence

L−: 3 observed corrections, 2 full-review persistent errors, 12 unknown.
The corrections occur in final-correct items 243 (circle count 3→4), 1715
(bottom-edge endpoints), 1642 (box count 4→5). Positive witness times are upper
bounds on first correction, not necessarily exact first-adoption latency.
The complete-case exact recovery interval is conditional on review coverage and
cannot support a population rate or a targeted-refresh mechanism.

Item 2634 re-inspects the chart and retains E-bar 1 instead of the source value 5;
it finishes wrong. Item 1707 retains the wrong edge binding yet finishes correct.
Together with the final-correct mutation case, these show why final correctness
cannot substitute for recovery or evidence preservation.

Continuous source switching, target/confuser transitions and source entropy are
unidentified: existing source replay covers isolated prefixes. No new replay was
needed, since it would not repair the primary annotation/exposure limitations.
All 62 L+ / final-wrong events (57 families) retain DU for the **first** downstream failure;
observing a later mutation does not identify the first error. This is unresolved
coverage, not evidence that arithmetic/integration errors are absent.

## Inference, resources and completion

Four frozen primary endpoints; 4000 complete-family bootstrap draws, seed 820260922;
family-equal event weighting; controls for t0 position, log trajectory length,
subject group, completion, R at the original T episode, ROI group and question
length. Pointwise 95% and four-endpoint 98.75% intervals are included only when
≥95% of replicates are valid. Missingness bounds accompany semantic endpoints.
Seven focused tests passed (boundaries, censoring, frozen geometry parity,
family weighting, confound identifiability and unknown semantics).

Both analysis executions were CPU-only Slurm jobs on node02, 2 CPUs / 8 GB, 0 GPUs.
The original execution and its mechanical correction are retained separately.
Frozen final-answer extraction spans map to tokens for 147 of 148 anchors; these
need not be the first answer commitment. Semantic subgoal boundaries remain
unidentified; full remaining retrieval is measured through native reasoning end.
Repairs select the first metric-eligible family event, separate semantic refresh
from unsupported staleness, and retain frozen final-answer extraction spans.
Labels, controls and primary windows were unchanged. No model/dataset download,
generation, detector refit or causal intervention occurred. GPU-hours: 0.
Detailed job receipts, timing and provenance are in `audit/` and `runs/`.

The 11 required artifacts and six figures are saved here. Figures explicitly show
missing coverage; empty categories are not evidence of mechanism absence.

## Exactly one recommendation

Emphasize the dissociation between local evidence fate and final-answer correctness, using the observed correction, mutation and persistent-error cases as illustrations and reporting the controlled post-read comparisons as inconclusive.
