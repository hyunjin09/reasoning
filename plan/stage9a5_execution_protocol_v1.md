# Stage9A.5 prospective execution definitions

Authority: stage9a5_qwen3vl4b_thinking_vs_cot_finite_access_plan.md.
Freeze before new inference; the original plan remains unchanged.

1. Reuse the 32 primary images/64 queries and 16-image reserve from Stage9A.3.
   Verify all image, task, prompt, option and Stage9A.4 reference hashes. Reuse
   completed CoT FULL/ZERO/64/128 and null-sink results without regeneration.
2. Pin Qwen3-VL-4B-Thinking revision1de27d8c51f12e819435303b9e84c4e25ba8401e.
   Native template ends in assistant <think> newline. Remove only the exact
   Stage9A.3 line "Think step by step. You must write intermediate steps."
   from the task body. Keep question, options and final {A} format instruction.
3. Native DeepStack unchanged. BF16, TF32 off, eager language/SDPA vision,
   greedy, native EOS, max_new_tokens=512. No interface requirement for a larger
   cap is evident in the local template/config. No automatic cap amendment.
4. First perform eight FULL-only exact no-op checks, then all64 FULL baselines.
   Seal native reasoning and literal final-option review before joining gold.
   Nontrivial native scratchpad content counts as reasoning even when capped;
   intention-only text does not. An option proposed within the scratchpad is
   not a final answer. Apply the unchanged Stage9A.3 literal adapter to the
   response after native </think>; preserve raw whole-trajectory extraction as
   a clearly labeled sensitivity, never as a fabricated final answer.
5. Gates: accuracy>=.60, native reasoning>=.90, valid final option>=.90,
   cap rate<=.10 OR all capped traces have valid final options, exact FULL no-op.
   Missing final options receive no credit. Any failed gate closes the stage
   before masked science. Report all-example and completion metrics separately.
6. If FULL passes, run eight actual-model V1-V6 checks as in Stage9A.4, then
   exactly ZERO/64/128. All36 decoder layers; generated query t=absolute-prompt+1,
   image keys blocked when t>cutoff. Prefill/image-derived cache remain native.
   Native-ended trajectories with N-1<=cutoff are exact FULL reuses; capped
   trajectories are not normal-ending aliases.
7. ZERO damage<=5pp stops necessity interpretation. Otherwise token128<=5pp
   stops the absolute search (select64 if both64 and128 preserve, else128).
   Token128>5pp triggers256 only; no other absolute grid. Record any nonmonotonic
   behavior rather than bypassing the specified128 gate. If no cutoff preserves,
   256 is the bounded control's last-tested budget, not a sufficient cutoff.
8. Independent unit=image, both queries equally weighted. 4,000 paired image
   bootstrap draws, seed920260927,95% percentile intervals. Main cross-arm
   endpoint=Thinking128 damage minus frozen CoT128 damage. Meaningful paired
   support for the positive claim requires a95% lower bound>0; point-based5pp
   preservation is reported separately from uncertainty. Use1e-12 only for
   floating comparisons. No outcome-dependent tolerances.
9. Relative-time descriptions use each FULL's observed total generated length N
   as the common horizon proxy (including final/EOS); report native Thinking
   scratchpad tokens separately. Give64/median(N), median(64/N), analogous128/256,
   clipped fractions, and actual exposure N-1>cutoff. Capped N is right-censored,
   not a known complete reasoning horizon. Keep all examples and label censoring.
10. Normalized50%/75% is conditional on damaging ZERO, Thinking128 damage>5pp,
    positive cross-arm128 difference, and longer Thinking median FULL length or
    lower median128/N exposure. Use floor(fraction*N), both arms/same32 images,
    same cap/backend. No other normalized points; reuse exact existing policies.
    Report paired damage differences at both fractions with image uncertainty;
    a prolonged relative-phase claim requires positive support at a tested
    matched fraction, not just longer traces. No absolute256 if128 preserves.
11. Primary reserve eligibility is evaluated after bounded controls: positive
    cross-arm128 difference>5pp and Thinking128 damage>5pp (not clearly null),
    interval includes0 OR Thinking128 preservation interval spans5pp, and no
    technical/control qualitative failure. If triggered, freeze128 as the
    decision-relevant primary contrast and run FULL/ZERO/128 on the16 reserve
    images in both arms for a genuinely paired48-image comparison. No new
    cutoff, extra reserve or new grid. Preserve the primary32 result separately.
12. Null-sink: primary32 only FULL/ZERO/selected finite budget after the absolute
    decision. If no finite budget preserves, use last-tested256 as an explicitly
    insufficient control budget. Native non-image probabilities are not
    renormalized. Reuse exact FULL/no-exposure rows. Compare existing CoT control
    only where conditions match; qualitative effects and confidence are distinct.
13. Up to4 available A6000 GPUs on authorized node02/03/06/07 through scheduler/
    Slurm only,4CPU/30G each, one process/GPU, no tmux or keepalive. Finite queues
    release allocations promptly. Heavy hashing/bootstrap/figures use CPU jobs.
    Conservative .06s/token*512 estimates: FULL .55GPUh, T1 1.64, T256 .55,
    null-sink1.09 plus1h overhead; optional normalized2.18 and paired reserve1.64.
    Primary/control target<10GPUh; projected>15 before optional expansion stops.
14. Produce required artifacts and figures; gated not-run results carry explicit
    status/null fields or empty schemas, never invented effects. If baseline
    fails, relative lengths are descriptive/censored and masked comparison is
    unmeasured. Exactly one plan-appropriate recommendation, then STOP.

Implementation checkpoints: input/protocol freeze and channel tests; FULL no-op
and T0 gates; conditional V1-V6/T1/T256; conditional controls/normalization/reserve;
final paired inference, figures, independent audit and release accounting.
No Git metadata exists; immutable artifacts and source hashes are save points.
