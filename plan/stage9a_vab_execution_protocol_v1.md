# Stage9A VAB execution protocol v1

User-authorized on 2026-09-24 by the request to execute
`stage9a_vab_style_visual_access_necessity_thinking_vs_cot_plan.md`.
The completed `outputs/stage9a/v1` study remains immutable pilot evidence.
New outputs live in `outputs/stage9a_vab/v1`; no Stage9B execution.

## Ordered implementation and acceptance checks

1. Freeze synthetic scene/query manifests, this protocol, generator and model
   identities. Check150 distinct256px RGB scenes,6–7 nonoverlapping objects,
   two correctly counted queries per scene and common frozen A–E permutations.
2. Implement generated-query image-key masking and null-sink controls without
   changing prefill or prior cache. CPU tests check causal-row, layer/time and
   sink semantics; actual-model preflight tests V1–V6 on eight queries in all
   three arms. Require exact greedy tokens and logits for the no-op sentinel.
3. Run all900 full-access baselines. Review all300 CoT traces for intermediate
   reasoning with gold masked; evaluate the frozen elicitation and floor gates.
   No sweep is authorized before implementation validity and CoT validity pass.
4. Execute Direct29-layer sweep and identical CoT/Thinking29×15 grids, using
   only proved identical-condition aliases. Validate complete269700 grid rows.
5. Image-cluster inference4000 draws; epsilon sensitivity; frozen-rule boundary
   transfer and artifact controls. A positive controlled gate alone permits the
   optional64-item MathVision bridge. One recommendation then STOP.

## Paper and implementation boundary

Reference: Osaka et al., arXiv2607.12815v2, Sections4 and AppendicesA/B:
https://arxiv.org/html/2607.12815v2 . Retrieved2026-09-24.
The user plan fixes the intervention, tasks, prompts, grid and controls.
Exact original generator/source code is unavailable; placement, target sampling,
size convention, sink implementation and boundary tie rule below are explicit
reimplementation choices. No bitwise paper reproduction is claimed.

## Synthetic data

Seed920260924; independent seeded generators for scenes, prompts and options.
150 scientific scenes and four disjoint technical-validation scenes;256×256 RGB,
white background, matplotlib patches, no axes/text/borders. Each scene has6or7
objects equiprobably. Attributes independently sampled uniformly: red/green/
yellow/blue; five-point star/circle/equilateral triangle/square;18/24/30/36px
diameter of bounding circle;0/45/90/135-degree rotations. Star inner radius0.45
of outer. Centers sampled in pixel coordinates with full shape containment and
at least6px between bounding circles. Quadrants derive from centers.
Use literal matplotlib named colors. Geometry/angles are recorded even though
only color/shape are queried. Store raw generated images in a dataset-specific
directory under the allowed external dataset root, passed as an execution arg.

Each primary attribute target is sampled uniformly among classes whose actual
scene count is1–5. This keeps the paper-style five options1–5 valid; target/count
distribution is recorded, never adjusted after model outcomes. Each query gets
an independent uniform permutation of1–5 over A–E, shared across arms. Sample
only before inference; no image filtering by model performance.

## Models, prompts, runtime

Reuse the exact local2B Instruct and Thinking snapshots from the pilot manifest.
Use plan §10 Direct and CoT strings verbatim (ASCII colon and single quotes),
Thinking question/options plus `Respond in curly braces format: {A}` with its
native thinking template and no extra reasoning instruction. Same preprocessing
as pilot (min/max pixels602112/4014080) across all conditions/checkpoints.
BF16, TF32 disabled, visionSDPA/languageeager for masked and disabled conditions.
Greedy, max40960, no constrained decoding, normal EOS. No detector is used.

Layer cutoff0..28 is a count of allowed decoder layers: zero-based module index
is masked when `layer_idx >= cutoff`. Token indexing applies to **query tokens**:
with P prompt tokens, absolute query P is generated token1. Query P+t−1 is
masked when t exceeds the cutoff, or layer exceeds its cutoff. Prompt positions
0..P−1 remain intact; the first emitted token is predicted by the final prompt
query and is consequently shared by the main interventions. The first generated
query affects prediction of the second emitted token. Thinking opening template
tokens belong to prefill; subsequently generated thinking/special tokens count.
Report this autoregressive one-position distinction explicitly.

Main block adds negative infinity only at selected generated-row/image-key
entries before native FP32 softmax/BF16 probabilities. The image K/V and previous
text/residual/cache remain. The full sentinel calls the original eager function.
The query-text control additionally blocks actual user-question text positions
in prefill at layer_idx>=cutoff; early layers and all other prefill rows stay.
The null sink preserves native probabilities of real non-image keys and sends
removed image probability to a zero-Value dummy slot (an algebraic virtual sink,
never a new cached token). No renormalization of remaining real keys.

Actual-model preflight uses eight technical queries ×three arms; paired disabled/
sentinel greedy continuations up to128tokens, plus fixed teacher-forced sequences
to test crossing cutoffs and cache-vs-full-sequence agreement. Bounded validation
caps are not scientific caps. Exact-logit sentinel tolerance0; cache/full forward
BF16 tolerance0.25 absolute with identical top token required. Record actual
errors. Masked probabilities must be exactly0; sink real probabilities unchanged.

## Full-access gates and extraction

Final scoring: last standalone braced A–E key in final answer section; Thinking
requires a final section after `</think>`. Direct may additionally use a sole
unbraced A–E response. Missing/ambiguous output remains unscorable/no credit;
no option/value correction by ground truth. Report extraction and cap rates.

Review all300 CoT outputs without gold/correctness. Nontrivial intermediate
reasoning requires an explicit visual identification/enumeration/counting step
before the final option; question echo, generic intention, answer restatement or
option lookup alone does not qualify. Freeze individual decisions before gold.
The plan's90% gate uses all300 as denominator. Material length increase means
CoT median at least2×Direct median and at least16 additional generated tokens.
Require at least95% valid option extraction in CoT as the operational extraction
gate; report other arm rates. No prompt tuning. Elicitation failure triggers
the specified stop before a CoT-versus-Thinking boundary claim/sweep.
Per-arm/per-attribute full accuracy floor is50%; invalid cells cannot yield an
interpretable VAB. Do not tune images/targets to improve the floor.

## Sweep and inference

Every layer0..28. Tokens0,1,2,4,8,16,32,64,128,256,512,1024,2048,4096,FULL.
Main grid: Direct8700 +CoT130500 +Thinking130500 rows. Reuse only exact
equivalences: layer0 across token cutoffs; token0 across layer cutoffs; a token
cutoff at least the completed same-layer FULL trajectory length. Each alias
retains the executed source and proof; no interpolation or assumed monotonicity.
Cached prefix sharing, if used, must pass identical greedy continuation checks.

Analyze color and shape separately and equal-weight pooled, image as independent
unit with its two queries retained together.4000 paired image bootstraps, seed
920260925;95% percentile intervals, recomputing full accuracies, admissibility
and boundaries in every draw. Primary epsilon.05, sensitivities.03/.07/.10.
Report direct-anchored unreachable regions asN/A. No fitted monotonic smoothing.
Axis minima: smallest admissible layer at FULL and smallest admissible time at
full depth. FULL stays a sentinel, not an invented finite boundary. Rho is
undefined for FULL. Record bootstrap undefined fractions, not fabricated CIs.

Joint representative: among admissible Pareto points, smallest time then
smallest layer (FULL ordered last). The transfer uses this **joint admissible
point**, not the possibly inadmissible Cartesian combination of axis minima.
Select CoT's representative from full observed data; bootstrap the selection
along with paired damage to reflect boundary-selection uncertainty. Report
fixed-point contrasts separately. Finite temporal necessity requires cutoff
below median full-access horizon, avoiding trivial high-cutoff aliases.

Controls: freeze32 image IDs by seed920260926 before outcomes, both attributes,
CoT and Thinking. Same point-selection rule for all: full sentinel, (0,0),
CoT joint boundary and Thinking joint boundary, deduplicated; no-access is called
harmful only if observed damage supports that label. Run standard/query-text/
null-sink at these points, retain uninformative controls. No extra cutoff search.
Both attributes must support the main claim; pooled heatmaps alone cannot.
Gate criteria follow plan §29; tolerances cannot reverse temporal ordering.

## Resources and stopping

Up to4 available GPUs on node02/node03/node06/node07 via scheduler/Slurm only.
Prefer healthy node06 capacity while node07 startup reliability is unresolved.
Independent one-GPU workers; release on bounded queue exit, no tmux/keepalive.
There are269700 nominal grid rows before equivalence reuse; compute can greatly
exceed the pilot. Measure baseline lengths/throughput before a defensible ETA.
All prior pilot artifacts and its negative frequency result stay preserved.
Stop at failed mandated validity gates, or after all15 required artifacts and
six figures (plus the conditional bridge if positive), with exactly one
recommendation and no automatic execution of it.
