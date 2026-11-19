# Stage8C v2 execution protocol

User approval:2026-09-20 KST, supplied Stage8C v2 plan; exactly two node02 GPUs,
project scheduler/Slurm, no tmux. The original plan remains authoritative.

## Ordered gates

Freeze input-only visual families, dev128/test512, timing256 and audit128 first.
Technical validation V1–V6 must all pass before dev inference. Freeze one of
1.25/1.50/2.00 after dev; apply the dev no-go before any test inference. No new
dose, detector, model, source annotation or policy may be chosen from test data.
Conditional extension follows plan §36 only. A stopped branch is a report and
recommendation; it does not authorize launching Block3B.

## Operational definitions fixed before outcomes

- BF16 pinned2B; unchanged Stage8B v2 prompt/pixels/scorer, temperature1,
  top_p.95/top_k20, max40960, normal EOS, zero presence penalty.
- Frozen Stage8A joint detector, layers19–22, threshold0.5478025980771918.
  Gap4 means at most four inactive intervening tokens; missing R splits an
  episode. Probe token index follows the existing passive recorder: output
  index t is measured from the prefix predicting token t. Prefill R is
  unavailable. The primary online policy evaluates every generated position;
  reasoning-only summaries also retain the explicit think boundary.
- Probe consumes no sampling RNG. At an onset, discard only its appended
  current-token K/V, rerun the same current input and positions with gain,
  commit that cache, and let the unchanged HF generation loop sample once.
- Add `(g-1)*W_O(concat_h(a_visual @ V_visual))` to the attention projection
  output of each selected layer at the current query. Use that rerun layer's
  current native attention weights/values; no renormalization, target ROI,
  desired value or benchmark answer. Gain1 returns the original tensor.
- V1/V2 require exact generated IDs and committed raw logits. V3 tolerance is
  relative L2<=0.02 and max absolute error<=0.125 for BF16 decomposition;
  also compare FP32 accumulation reference. V4 checks cropped prefix identity,
  cache length and independent intervention replay plus next-token equality.
  V5 compares online onset indices with the frozen offline gap4 implementation.
  V6 checks inference interfaces and denylisted oracle fields. Failure stops
  scientific execution and is recorded without changing tolerances.
- Cohort sampling seed820260920. Item sampling seed is the first31 bits of
  SHA256(`stage8c_v2:item_id`), shared across arms. Native output is never used
  to select cohort membership.
- Family construction combines exact/rescaled perceptual images, known alias
  1707/1245, and sufficiently specific repeated question templates. Ambiguous
  near-image candidates are grouped conservatively. Prior MathVision cohort
  items and known clean/wildphoto pairs are excluded with their full families.
  One representative per selected family. Report deduplication limits.
- Stratify by available source subject, level and choice/free-response format;
  absent fine problem type, density and entity-count metadata stay missing.
  Preserve proportional composition rather than enforce artificial balance.
- Primary accuracy is correct/all frozen items; unresolved extraction remains
  explicit and receives no correct credit. Preserve unresolved transitions and
  provide resolved-only sensitivity; use existing blind extraction procedures
  before dose decisions if unresolved cases could change selection/gates.
- Major subtype is the original subject label; dev severe harm uses >=15 items
  and strictly more than10pp loss. The qualitative 'meaningful' dev gain is
  fixed here as >=2pp; 'clearly substantial' held-out gain as >=5pp. These only
  qualify length guards, never relax accuracy/CI or cap gates. A dose must pass
  its applicable no-go guards before highest-accuracy/tie-break selection.
- Inference: deterministic20000 paired bootstrap samples (item and family),
  exact two-sided McNemar; no tokens/events treated as independent items.
  Extension 'small positive' means >0 and <=5pp, plus every other §36 condition.
- Timing positions are fixed from C0 only, outside episode±16; choose without
  replacement within trajectory quartiles when feasible. Preserve inability
  to place K events or early termination as mismatch, not resample with C2.

## Resource estimate before technical timing

Maximum initial scientific runs:512 dev +1024 held-out +256 random=1792;
optional extension adds1024. Prior native traces averaged about11800 tokens,
but the new decoder's runtime is unmeasured. Provisional dev40–100 GPU-hours
(20–50 hours on2 GPUs); full initial stage150–350 GPU-hours conditional on gates.
Replace with measured throughput after validation and first complete examples.
No idle keepalive; release each allocation when its queued work ends.
