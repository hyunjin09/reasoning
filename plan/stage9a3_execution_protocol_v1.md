# Stage9A.3 bounded calibration: execution protocol v1

Implements the explicitly approved Stage9A.3 plan. Separate namespace:
outputs/stage9a3/v1. Existing MathVision main evidence and completed controls
are immutable. Stop old controls using their between-rollout stop flag, verify
durable receipts, then release allocations. No new strategic approval is needed.

## Ordered work and acceptance

1. Freeze32 primary,16 reserve and4 disjoint technical images (8 technical
queries), common prompt/options, both checkpoint identities and this protocol.
Tests require reproducible nonoverlapping scenes, correct counts/permutations,
mask indexing and independent image weighting. No model-selected filtering.
2. Validate model-wide Qwen2.5 mask on all8 technical queries, including no-op,
zero image probabilities, unchanged prefill, cached continuation and depth/time
boundaries. Record greedy baseline lengths and throughput; freeze generation cap.
3. Run64 Qwen2.5 primary FULL trajectories. Seal literal extraction and manual
CoT validity without gold; enforce90% intermediate reasoning,95% valid extraction,
60% accuracy and normal termination. Freeze token grid from baseline lengths.
4. Freeze exact canonical manifest/compute estimate, then run16 logical conditions
per query with exact aliases only. Analyze paired4000 image bootstraps and the
predeclared calibration gate. A gate failure stops, with reserve only as below.
5. Only if Phase A passes: same assay on Qwen3, first8 technical validations and
64 FULL checks, then its grid if baseline gates pass. Run the bounded null-sink
controls, report artifacts/figures and exactly one recommendation. STOP.

## Synthetic inputs and model identity

Use source paper AppendixA as task/prompt reference:
https://arxiv.org/html/2607.12815v2 . This is a bounded reimplementation, not exact
published generator replication. Procedural256px RGB white-background scenes
contain6or7 nonoverlapping objects. Independently uniform red/green/yellow/blue,
star/circle/triangle/square, bounding-circle diameters18/24/30/36px, angles
0/45/90/135 degrees. Centers have6px bounding-circle clearance; record quadrants.
Fixed NumPy seed920260927 with separate scene/query option streams. Primary IDs
0–31, reserve32–47, technical48–51; no outcome-dependent ordering or replacement.
Each image has one color and one shape target, sampled uniformly among present
classes with count1–5, and an independently permuted A–E mapping to counts1–5.
Ground-truth attributes are metadata, never given to inference.

Use local frozen Qwen2.5-VL-3B-Instruct and Qwen3-VL-2B-Instruct snapshots, record
config/tokenizer/weight hashes. Images pass through each model's processor with
common min_pixels224²/max_pixels256²; architecture-required patch rounding and
normalization differ and are recorded. Native checkpoint chat templates only.
BF16, language eager, vision SDPA, TF32 off, eval, greedy, no forced output,
no sampling. No detector, prompt search or MathVision expansion.

Common prompt:
```
How many {target} objects are in the image?
options: {A: ..., B: ..., C: ..., D: ..., E: ...}
Think step by step. You must write intermediate steps.
Respond in curly braces format: {A}
```
The literal final `{A}` is format instruction, not the correct option.

## Mask semantics and technical validation

Layer counts round down: Qwen2.5[0,18,27,36], Qwen3[0,14,21,28]. Image-key
access is allowed only when layer_idx<count AND generated-query time<=cutoff.
FULL time has no temporal restriction. With prompt lengthP, query coordinate
t=absolute_query−P+1. Prefill predicts token0 and remains unchanged; generated
queryt predicts token t. All decoder layers participate; no late-layer-only mask.
Keep prior KV/prefill and image-derived state; future cache evolves naturally.
Null-sink zeroes image Value contribution without renormalizing other weights.

Eight technical examples are fixed before outcomes. Disabled vs FULL requires
bit-identical generated tokens and logits (tolerance0). Prefill logits exact
under every cutoff; masked image probabilities exactly0; null-sink nonvisual
probabilities exact. Check layer cutoffs0/half/three-quarters/full and times0/2/4
on a fixed eight-token cached sequence. Same mask: fresh generation and resumed
cached generation must match; no cache reset at activation. All tests must pass.

Technical baseline runs have a1024-token ceiling. Freeze scientific cap as the
smallest of256/512/1024/2048 at least1.5×the longest normally completed technical
baseline; choose2048 if technical baseline hits1024. This is a length-only rule,
not prompt/correctness tuning. If no technical trajectory terminates normally,
stop and report unsuitable bounded generation. Scientific capped outputs remain
unscorable if no final answer; no cap expansion after scientific masked outcomes.

After64 primary FULL outputs, default time grid[0,16,64,FULL]. If>90% terminate
before64, replace64 with max(17,min(63,floor(median completed length/2))) unless
that exceeds the observed95th percentile, in which case use17. This declared
length-only rule retains four distinct cutoffs and is frozen before masking.
If fewer than10% reach beyond16, stop as unsuitable for the temporal grid;
no alternate prompt or increasingly fine time search.

## Scoring and inference

Extract last standalone braced A–E from the terminal answer. Missing or genuinely
ambiguous output is unscorable/no credit. Literal gold-masked review may normalize
formatting/explicit option label, not solve or correct the answer. Preserve raw
and reviewed extraction. CoT requires explicit visual enumeration/identification
or a counting step before final option; generic intent, echo or answer repetition
does not count. Review64 full-access trajectories per model before masked science.
All64 form the accuracy denominator; image contributes the mean of its two queries.

Independent unit=image.4000 paired image bootstrap draws, seed920260927, same
draws for models/cells;95% percentile intervals, equal image weighting. FULL
is baseline. No tokens, queries or grid cells are independent samples.

Operationalize the plan's qualitative positive-control gate prospectively:
- Clear damaging restriction: (layer0,time0) damage>=10pp and95% lower bound>0.
- Material finite condition: layer<=.75L or finite time below median FULL length;
  non-FULL, observed damage<=5pp. FULL/unreached-time aliases do not qualify on time.
- Bootstrap stability: at least90% of paired image draws retain positive damage
  at(0,0) AND damage<=5pp at the selected finite condition. Also report selection
  frequency, intervals and bootstrap re-selection using the same deterministic tie.
- Technical/baseline gates must remain valid. No positive label from low FULL accuracy.

Tie rule: smallest time (FULL last), then shallowest normalized depth, then
lexicographic ID. Select on Qwen2.5 only before any Qwen3 masking results.
Reserve16 is permitted only if clear restricted damage exists, some material
finite condition has point damage<=10pp and the5pp threshold is crossed by its
95% interval, and calibration is otherwise valid. Run unchanged grid, evaluate
all48 images once. A final failure stops before Qwen3. Phase B always uses the
original32 primary images; if reserve was used report the32 matched Q2.5 support
separately from its48-image calibration selection.

Bounded null-sink logical controls: FULL,(0,0) if it meets the damaging criterion,
and selected finite calibration condition if present. If no damaging restriction
exists, retain(0,0) explicitly as an unconfirmed diagnostic. FULL is an exact
validated no-op reuse.64 queries on primary32 images only, at most128 extra
continuations/model. No full sink grid or query-text experiment.

## Resources and stop

Canonical4×4 grid has10 distinct policies before trajectory identity reuse:
layer0 and time0 all alias one no-access policy; nine positive-depth/time pairs
include FULL. Thus at most640 continuations/model (64 FULL+576 masked), plus
bounded controls. Reserve at most320 further standard continuations. Estimate
tokens and GPU-hours using technical/FULL observed throughput before main grid;
target<25GPUh Phase A; stop if estimate>40GPUh. All-cap projection reported too.
Scheduler/Slurm only, allowed node02/03/06/07. Use up to4 workers for this small
stage; combined old-draining/new allocations stay within existing8-GPU ceiling.
Exit on queue completion, no tmux/keepalive or autonomous next experiment.
