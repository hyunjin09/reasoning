# Stage 8C-R — Visual-Contribution Decomposition Repair and Full Technical Revalidation

## 0. Purpose

Stage 8C v2 stopped correctly at technical validation because **V3 visual-contribution decomposition failed**. No scientific intervention experiment has started.

This repair stage has one purpose:

**diagnose and repair the visual-contribution decomposition, then rerun V1–V6 from scratch.**

If and only if all technical gates pass, resume the already frozen Stage 8C v2 experiment at:

**Stage 8C.1 — Diverse 128-item dose calibration.**

The existing Stage 8C v2 cohorts, dose grid, detector, trigger rule, and statistical plan remain frozen.

---

## 1. Why this repair is necessary

The Stage 8C intervention is defined as:

`h_post <- h_post + (g - 1) C_visual`

where `C_visual` is the model's native visual attention contribution.

This is scientifically interpretable only if:

`C_visual + C_nonvisual ≈ C_native`

on the actual cached BF16 execution path.

If this identity is wrong, then a nominal 1.25x/1.5x/2.0 gain has no clean mechanistic meaning, and any downstream accuracy result would be uninterpretable.

Therefore V3 is a validity gate, not a cosmetic engineering test.

---

## 2. What success supports

A successful repair does not create a new scientific claim. It only establishes:

> The visual contribution used by Stage 8C is a valid decomposition of the model's native attention computation on the canonical Qwen3-VL-2B-Thinking path.

Only after that may the efficacy experiment resume.

---

## 3. What repair failure does NOT rule out

Failure to repair does not invalidate:
- reasoning-conditioned visual retrieval;
- online retrieval-state observability;
- Value-rich visual semantic transport;
- Block 2's descriptive routing pattern.

It only closes the current intervention implementation.

---

## 4. Frozen scientific configuration

Do not change during repair:

### Model / benchmark
- Qwen3-VL-2B-Thinking
- MathVision
- BF16

### Generation
- temperature = 1.0
- top_p = 0.95
- top_k = 20
- repetition penalty = 1.0
- presence penalty = 0.0
- max_new_tokens = 40960
- frozen preprocessing

### Retrieval detector
- Stage 8A detector unchanged
- `tau_R = 0.5478025980771918`
- gap-4 retrieval episodes
- trigger = first active token of each episode

### Intervention
- layers 19–22
- frozen current head set / decomposition scope
- dose grid = {1.0, 1.25, 1.5, 2.0}

### Cohorts
Preserve already frozen:
- dev128
- test512
- timing-control256
- local-read-audit128

No cohort replacement is allowed because of the technical failure.

---

## 5. Frozen V3 tolerances

Do **not** relax the original bounds:

- relative L2 <= 0.02
- max absolute error <= 0.125

Repair must explain/remove the discrepancy rather than widen tolerance.

---

## 6. Main debugging hierarchy

Localize the failure in this order:

**source partition -> head-space decomposition -> W_O projection -> residual integration**

Do not debug multiple stages at once.

---

## 7. Diagnostic prefixes

Reuse the known failing prefixes first:
- item 2579
- item 2433

Also include:
- at least one triggered prefix
- at least one non-trigger prefix
- short, medium, and long cached prefixes

Preferred total: 4–8 prefixes.

Do not cherry-pick only passing prefixes.

---

## 8. Forensic logging before assertions

For every prefix, layer 19–22, and tested token, save before any assertion:

- native pre-W_O norm
- visual pre-W_O norm
- nonvisual pre-W_O norm
- pre-W_O reconstruction relative L2
- pre-W_O max abs error
- native post-W_O norm
- reconstructed post-W_O norm
- post-W_O relative L2
- post-W_O max abs error
- native residual-stream post-attention norm
- reconstructed residual norm
- residual relative L2
- residual max abs error
- largest-error tensor index
- largest-error native/reconstructed values
- total valid attended KV positions
- visual-token count
- nonvisual-token count
- partition overlap count
- partition uncovered count
- dtype at each stage

Assertions may run only after these records are written.

---

## 9. Diagnostic A — Source partition audit

Let:
- V = visual KV positions
- N = nonvisual valid KV positions
- K = all valid attended KV positions

Require:

`V ∩ N = empty`

and:

`V ∪ N = K`

Audit explicitly:
- image patch tokens
- multimodal boundary/special tokens
- system/user prompt tokens
- prior reasoning tokens
- cached prefix positions
- masked/padding positions

Produce token-index manifests per prefix.

If partition fails, repair indexing/masks before numerical reconstruction.

---

## 10. Diagnostic B — Native attention-path reuse

Verify that decomposition uses the same native tensors/semantics as the forward path:

- Q
- K
- V
- RoPE-applied states
- attention mask
- scaling
- GQA semantics
- cached positions
- attention probabilities where capture is available

Record whether attention weights are:
- exact native captured values, or
- recomputed values.

Do not silently compare a separately recomputed attention path to a different native kernel output.

---

## 11. Diagnostic C — Pre-W_O identity

Per head:

`c_native = sum_all a_j V_j`

`c_visual = sum_visual a_j V_j`

`c_nonvisual = sum_nonvisual a_j V_j`

Test:

`c_native ≈ c_visual + c_nonvisual`

before concatenation and again after head concatenation, before projection.

### If pre-W_O fails, prioritize:
1. source partition
2. cache indexing
3. GQA replication
4. head reshape/order
5. attention capture/reuse
6. mask mismatch
7. position/RoPE handling
8. dtype/cast order

Do not move on to W_O debugging until this identity passes.

---

## 12. Diagnostic D — GQA audit

Record:
- number of query heads
- number of KV heads
- grouping/replication factor
- exact Q-head to KV-head mapping used by native execution
- decomposition mapping

Verify visual/nonvisual accumulation under exact native GQA semantics.

Do not assume one-to-one Q/KV head mapping.

---

## 13. Diagnostic E — W_O projection identity

Only after pre-W_O passes, test:

`W_O(c_native) ≈ W_O(c_visual + c_nonvisual)`

and:

`W_O(c_visual) + W_O(c_nonvisual) ≈ W_O(c_native)`

Audit:
- concatenation order
- tensor layout
- projection dtype
- projection bias
- separate vs joint projection calls

If projection bias exists, it must be counted exactly once.

---

## 14. Diagnostic F — Projection-bias audit

Inspect the actual model module and record:
- whether `o_proj.bias` exists
- bias norm
- how current decomposition treats it

No assumption about Qwen's bias behavior is allowed without module/source verification.

---

## 15. Diagnostic G — Residual integration identity

After projection passes, verify the exact native residual update.

If native update is:

`h_post = h_pre + A_native`

reconstruct:

`h_recon = h_pre + A_visual + A_nonvisual`

with any native scaling/gating applied identically.

Test:

`h_post ≈ h_recon`

Record residual-stage errors separately.

---

## 16. Diagnostic H — Dtype and accumulation order

Record for each stage:
- input dtype
- accumulation dtype
- output dtype
- reduction dtype
- cast order before/after W_O

FP32 is allowed for diagnostic error measurement.

Do not silently change the scientific intervention computation to FP32.

---

## 17. Diagnostic I — Triggered and non-triggered prefixes

V3 must pass on both:
- retrieval-onset prefixes
- non-trigger prefixes

A pass only on triggered prefixes is insufficient.

---

## 18. Diagnostic J — Cache-length robustness

Test short, medium, and long cached prefixes.

All comparisons must remain within the same canonical cached BF16 path.

Do not require full-forward vs cached exact equality.

---

## 19. Root-cause decision tree

### Case 1 — Partition fails
Repair source indexing/masks, then rerun all diagnostics.

### Case 2 — Partition passes, pre-W_O fails
Repair attention capture, GQA, cache indexing, reshape, masking, or positional handling.

### Case 3 — Pre-W_O passes, post-W_O fails
Repair concatenation, projection, bias, dtype/layout.

### Case 4 — Projection passes, residual fails
Repair residual bookkeeping/scaling/state update.

### Case 5 — All decomposition identities pass but gain path fails
Repair gain wrapper/cache control flow, then rerun V1–V6.

---

## 20. Allowed repair changes

Allowed:
- diagnostic logging
- source partition code
- decomposition code
- GQA/head mapping
- W_O/bias handling
- residual reconstruction
- validation caller code
- cache bookkeeping required to realize the same intervention mathematically

Not allowed without a new scientific plan:
- detector change
- threshold change
- layer-window change
- dose change
- cohort change
- trigger change

---

## 21. Repair success criterion

Every diagnostic prefix must satisfy the frozen final reconstruction bounds:

- relative L2 <= 0.02
- max abs <= 0.125

No individual prefix may be hidden by averaging.

Preferred stronger result:
- pre-W_O passes comfortably
- post-W_O passes comfortably
- residual reconstruction passes comfortably

---

## 22. Full V1–V6 revalidation

After repair, rerun the entire technical gate from scratch.

### V1 — Gain-1 exactness
g=1.0 reproduces native inference.

### V2 — Non-trigger exactness
No onset -> wrapper is transparent.

### V3 — Visual decomposition
Repaired decomposition passes frozen bounds.

### V4 — Cache validity
Continuation uses intervention-state cache.

### V5 — Trigger validity
Online detector reproduces frozen Stage 8A behavior.

### V6 — No oracle leakage
No access to:
- benchmark answer
- ROI labels
- T/M/U
- L+/L−
- future tokens

All six must pass in one final validation bundle.

---

## 23. Revalidation coverage

Use at least:
- 2 triggered prefixes
- 2 non-trigger prefixes
- multiple cached lengths
- multiple layers 19–22
- at least two independent MathVision families

Preferred: 8 total prefixes if technical cost remains small.

---

## 24. Scientific resume rule

If V1–V6 all pass:

**resume Stage 8C v2 exactly at Stage 8C.1 — dev128 dose calibration.**

Use:
- already frozen dev128
- gain grid {1.0, 1.25, 1.5, 2.0}
- retrieval-onset trigger
- existing selection/no-go rules

Do not redraw cohorts or retune detector.

---

## 25. If repair changes the scientific intervention

If the mathematically correct implementation requires a material scientific change, stop before dev128.

Examples:
- different layer window
- scaling pre-W_O instead of the planned post-W_O contribution
- different source definition
- new trigger
- switch from contribution gain to re-attention

Then write a new user-approved intervention plan.

Pure implementation fixes preserving the same mathematical intervention do not require a new efficacy plan.

---

## 26. Stop rule

Stop Stage 8C intervention branch if:
- V3 cannot pass frozen tolerances after bounded diagnosis;
- pass requires tolerance relaxation;
- `C_visual` cannot be defined consistently on the native path;
- V1/V2/V4/V5 cannot jointly pass;
- repair requires an unapproved scientific intervention change.

Do not run dev128 under technical uncertainty.

---

## 27. Required artifacts

Produce:

1. `stage8c_repair_prefix_manifest.json`
2. `stage8c_v3_forensic_metrics.parquet`
3. `stage8c_source_partition_audit.json`
4. `stage8c_prewo_reconstruction.json`
5. `stage8c_gqa_audit.json`
6. `stage8c_postwo_reconstruction.json`
7. `stage8c_projection_bias_audit.json`
8. `stage8c_residual_reconstruction.json`
9. `stage8c_dtype_accumulation_audit.json`
10. `stage8c_repair_root_cause.md`
11. `stage8c_repaired_implementation_diff.txt`
12. `stage8c_v1_v6_revalidation.json`
13. `stage8c_repair_summary.md`
14. exactly one recommendation:
   - resume Stage 8C.1
   - revise scientific intervention
   - stop intervention branch

---

## 28. Diagnostic figures

### Figure 1 — Reconstruction error by layer
For layers 19–22:
- pre-W_O relative L2
- post-W_O relative L2
- residual relative L2

### Figure 2 — Max-absolute error by stage
Partition / pre-W_O / post-W_O / residual.

### Figure 3 — Source-partition coverage
Visual + nonvisual coverage per prefix.

These are technical figures, not necessarily paper figures.

---

## 29. Final decision criterion

This repair stage succeeds only if:

**the proposed visual contribution is a valid decomposition of the native attention computation on the canonical cached BF16 path**

and:

**V1–V6 all pass together.**

If successful:
- resume Stage 8C v2 at dev128.

If unsuccessful:
- do not run the intervention efficacy experiment;
- return to the non-intervention path, especially Block 3B recovery/wandering analysis.
