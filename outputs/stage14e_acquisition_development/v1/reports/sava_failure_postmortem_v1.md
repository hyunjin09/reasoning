# SAVA failure postmortem: source-linked development evidence

All72 original families were joined to exact original images/prefixes, query and address receipts, helper records, existing source reviews and all432 final scores. The initial preservation audit verifies5,357 sealed files unchanged. Six source-image sheets were inspected against all72 question/query/address records; ambiguous small details retain the earlier original-image review or uncertainty. The frozen24 acquisition panel remains the primary representative acquisition panel. All9 any-arm regressions and3 primaryQI rescues are preserved in `analysis/all_regressions_and_primary_rescues_v1.json` with exact sources and solver receipt paths.

## What prevented useful evidence acquisition

**Target selection lost the relationship the solver needed.** Only22/62 accepted queries were fully relevant (35.5%; descriptive family bootstrap95%CI24.2–46.8%). Examples:107 asks the label ofB instead of street occupancy;937 asks the central island's position instead of bridge adjacency;847 asks an unnamed bottom square's position instead of row offsets;2702 verifies a text-given white corner while leaving the false checkerboard assumption intact. These are observed input/target mismatches, not proof of an inaccessible latent representation.

**Some requests were not image-resolvable.** NumericD in895, final water level1811, arcDA length2317, AB length2390, PQlength2501 and angleR2895 require inference; the requested values are not printed.333asks for nonexistent point labels. The host provenance checker certifies reference transport, not that a target exists or is useful. Seven rejection fallbacks must remain separate from semantic method failures.

**Source addressing independently failed.** Of49 generated local views,14 enclosed the requested target correctly (28.6%; descriptiveCI16.3–40.8%),20only partly,13wrongtarget,1wrongsource,1underspecified.633's crop targets lower-left kangaroo/steps instead of upper-right rabbit;1477crops the ring finger instead of middle finger. A correct crop can still isolate the wrong property:32's kangaroo icon lacks whole-circle containment;1380's rectangle crop excludes nail/string. This does not identify the effect of ideal crops, which was not tested.

**Reading and transport are separate.** Full-imageQI can give wrong bindings even when target is useful (633:99instead of100), merely repeat question facts (1067:PQ6;423:six beds), repeat a hypothetical frame (436), output literal template placeholders (407), or claim an image is unavailable despite verified image transport (2919). The frequency of these literal claims is a heuristic flag, saved with exact records; it is not evidence that image pixels were absent. Prefix anchoring and constrained compact reading are competing explanations requiring controlled tests.

## Checkpoint timing and observable state

The new retrospective source/text taxonomy assigns26tentative visual premises,16unresolved visual premises,12explicit visual/source errors,16already correctly stated task-critical premises, and2chiefly textual/mathematical uncertainties. See all72 rationales in `annotations/prefix_review_v1.tsv`. This is a single-reviewer development annotation, not independent adjudication or a causal timing test. It does not claim that absence of a statement proves failed acquisition. Case111contains a noncritical total-cell error despite having the two task-critical positions correctly available; that distinction is preserved.

Thus fixed512tokens is sometimes after useful evidence has already been expressed (563,2748,407,337), but frequently occurs while geometry is unresolved (999,2919,107). The evidence does not support a universal move to earlier/later checkpoints. A demand/abstention interface is a smaller first intervention than an online timing controller. Tentative correct hypotheses (487:19hexagons;633:100) remain legitimate reinspection opportunities, not automatically redundant reads.

## Frozen24 acquisition panel

Existing source judgments give new correct visual informationG2,Q2,QI3,QIA3,QGL4 of24; whole-record correctG13,Q7,QI10,QIA11,QGL11. QIwrong2/unknown12; unknown includes absent/abstaining, never treated as incorrect acquisition. Record correctness includes bindings and support. These sparse yields do not establish that context-preserving crops improve acquisition or that final changes are mediated by fresh facts. The previous72are now development data.

## All regressions and primary rescues

| Family | Source-linked observation | Interpretation boundary |
|---|---|---|
|33|Ladybird query answers supplied iconimage3, not grid position; targeted arms wrong|Missing global binding; final harm not causally attributed to one fact|
|633|All targeted helpers bind rabbit to99, source100;QI/QIAregress, QGLdoes not|Wrong evidence observed; deterministic mediation not established|
|847|Count3returned instead of inter-row offsets;Qregresses|No explicit false helper value required for damage|
|1067|PQ6correct but already available; vertical overlap confusion persists|Regressions are not proof of a bad numeric read|
|1207|Gassumes equal sectors;QI/QIAabstain;Q/QI/QGLregress|Different mechanisms/controls; abstention not wrong acquisition|
|2317|Unknown arc length queried, no value printed|Inappropriate task delegated to reader|
|2390|UnknownABlength queried; reader abstains|No observed erroneous acquired value explainsQregression|
|2898|DA/DClabels correct but complementary shading not supplied|Unhelpful evidence may perturb reasoning; cause unresolved|
|2919|Useful whole-face query, reader says image unavailable;Gclaims4gray instead of12|A readout failure remains even with relevant query|
|471(QIrescue)|Targetedreadouts uncertain;Gincorrect symmetry claim|Rescue supplies no clearly new task-critical readout|
|423(QIrescue)|Six rectangles repeated; their orientations/arrangement not supplied|Rescue cannot certify visual acquisition mediation|
|1380(QIrescue)|Rectangle shape repeated; string interpretation not resolved|Same limitation|

## Ranked next actions

1. Diagnose **target specificity versus independent source reading**, using exact matched target conditions with/without the solver prefix. Use source-validated target identities only as a labeled diagnostic upper-support condition, never a deployable result.
2. Compare two bounded candidate interfaces: demand-resolved independent reading and source-structured independent reading. Both retain global image context and can abstain. Structured reading requires entity/relation bindings, not unrestricted answer correction.
3. Retain a small predicted-local-view control; do not assume cropping fixes an incorrect query.
4. Defer learned triggering/training/logit interventions unless these cheaper acquisition tests justify complexity. No timing causal claim from the retrospective census.

No original SAVA annotation, score, headline estimate or runtime artifact was changed. Exact causal responsibility for each rescue/regression is **unknown**; the actionable observation is a low rate of useful source-bound facts entering the solver.
