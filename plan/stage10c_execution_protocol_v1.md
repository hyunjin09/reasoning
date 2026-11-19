# Stage10C execution protocol — prospective

Authority: stage10c_causal_visual_reopening_plan.md. Preserve prior stages.
Independent unit: conservative problem/image trajectory. Use the exact24 event IDs
in Stage10B's >=24-token anchor-gap sensitivity, including its already-sealed later
MathVision475 event. Hash SHA256("stage10c-primary-920260927:"+trajectory_id) within
dataset; first8 per dataset primary, remaining8 reserve (5 MathVision,3 MathVerse).
Three technical cases are the first MathVision reserve, first MathVerse reserve,
and second MathVision reserve. Selection does not use correctness or effect magnitude.

## Frozen coordinates and runtime

Reuse A/B/evidence/target anchors verbatim. PRE=[B−24,B), POST=[B,B+24), outcome=
[B,B+64), native generated-token coordinates. The terminal24-token text suffix is
reviewed before outcomes for new B facts. Stage10B paragraph interval endpoints
are coarse and sometimes contain A/B clauses or end before intervening textual
restatements. Record that overlap/gap rather than moving B or selecting another
window. PRE contains calculations, conclusions, restated A/question facts or
unresolved textual hypotheses; it is a semantic control, not a causal certificate
that the interval is image-independent.

Use all28 decoder layers, all heads, the existing standard eager-attention
negative-infinity image-key mask. This extends the validated all-layer full-access
rectangle to a finite24-token interval; it is not the old19–22-layer passive assay.
Native prefill and earlier image-derived cache remain intact. A query at absolute
p+i−1 predicts generated token i. Apply the mask when computing that query,
restore at the right-open endpoint. Target and control use frozen absolute image
positions, equal patch counts, same image and disjoint support. No attention-based
control matching. Prefer the sealed irrelevant region, then compact geometric
extension. Exclude other presently required target content based on image semantics.

Qwen3-VL-2B-Thinking exact Stage9A checkpoint, BF16, TF32 off, native template,
language eager/vision SDPA and dataset-specific historical preprocessing.
Historical MathVision/MathVerse traces used sampling; Stage10C explicitly requires
greedy decoding. Therefore historical free suffixes are NOT exact greedy aliases.
Run one local unmasked greedy baseline plus four masked local continuations from
the same teacher-forced native prefix ending before PRE. No-op validation compares
unpatched greedy versus empty-hook greedy, not greedy versus sampled tokens.
Frozen native prefix IDs and evidence tokens remain unchanged. This is a local
assay (88 new tokens from B−24 through B+64), not benchmark-scale regeneration.
Do not shift B/window/scoring coordinates if free generation branches.

## Outcomes and review

Before interventions, ground the first atomic B fact represented by the sealed
native observation span in the original image. Keep the broader B subgoal and
complete native evidence span too. Broad inventory demands use their first
source-local assertion (e.g. first option), consistently across cases, not a
post-outcome easier target. Gold can disagree with native assertions. Seal accepted
semantic alternatives and required source binding for all24 cases. Score the
64-token local window, using prior prefix only to resolve references, never to
supply the new fact. Explicit correct resolution=>B_CORRECT; a material wrong
resolution=>B_WRONG; only questions/hypotheses/incomplete claims=>B_UNRESOLVED;
early termination with no local read=>NO_FINAL_LOCAL_READ. If retracted, use the
last completed resolution; unresolved contradictory resolutions are wrong.
Unrelated final-answer correctness is not scored. Main semantic scoring uses
condition-blinded, hash-ordered packets and frozen gold. No automatic substring
correctness scorer. Keep quotes/rationale and all unresolved cases.

Teacher force exactly the full sealed native B-observation token span under
NATIVE and the same four masks; report mean NLL/token and sums. NLL scores native
assertions, including wrong ones; it is convergent mechanistic evidence, not a
correctness metric. Long native evidence spans are retained even beyond64 tokens;
report this difference from the behavioral window. Historical-native correctness
in the same64-token window defines the preregistered source-faithful stratum;
also report fresh greedy baseline correctness as a distinct sensitivity.

## Statistics and gate

Equal trajectory weighting; paired4,000 bootstrap draws; fixed seed920260927.
Ordinary95% percentile intervals plus98.75% marginal intervals for four endpoints
(Bonferroni family-wise95%). P1=PRE accuracy−POST-all accuracy;
P2=POST-all NLL−PRE NLL; P3=irrelevant accuracy−target accuracy;
P4=target NLL−irrelevant NLL. Report dataset points, target types, completion,
historical-native faithful/wrong/unresolved and fresh-greedy faithful strata.
Prespecified robustness: delete each one and each pair; all relevant directions
must stay positive. Reopening must be positive for P1/P2 in both datasets;
specificity P3/P4 must remain positive in historical-native faithful stratum.
Main gate follows plan§16 positive point directions with these robustness and
technical checks. Intervals qualify strength/precision; do not silently replace
its direction gate with a different significance criterion. OutcomeA requires
both robust reopening and specificity; B/C require the respective robust component;
D neither. No causal impossibility claim from a null.

Open reserve only if all four primary points>0, at least one multiplicity-aware
interval includes0, both dataset reopening directions agree, no one/pair deletion
flips the corresponding effect and technical checks pass. Identical protocol,
combine16+8 once; no second expansion. This operationalizes precision-limited
rather than inconsistent. No reserve rescue after a failed direction.

Optional demand-swap constructions must be frozen before any intervention output;
only naturally phrased alternative source demands qualify, maximum8. Execute only
if the final full primary gate passes. Optional null-sink at most4 reserve cases
only if standard result is strong and a concrete reviewer-facing need is recorded.
Neither optional block changes the primary standard-mask claim.

## Resources, artifacts and stop

All GPU work through project scheduler/Slurm, finite single-GPU workers on authorized
A6000 nodes, up to8 available GPUs. Start with technical validation only; no primary
outcomes before all10 checks pass on exactly3 cases. Target<2GPUh primary,
<1additional reserve, <1optional; hard total<4GPUh including failures/validation.
All model/data local, no download expected. Preserve all failed attempts and receipts.
Produce11 mandatory artifacts plus optional artifacts only if executed, four figures
and fifth integrated figure only OutcomeA. Exactly one plan recommendation; STOP.
