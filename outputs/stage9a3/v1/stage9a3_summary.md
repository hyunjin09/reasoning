# Stage9A.3 — bounded VAB calibration and Qwen3 validity stop

**Completed at the plan's mandatory Qwen3 baseline-validity stop.** Qwen2.5-VL-3B CoT recovered a finite direct-access regime. Qwen3-VL-2B failed its FULL-access accuracy and CoT gates, so its masked grid was not run and the generation comparison is underidentified. No Thinking experiment, further reserve, prompt search, or next research action was launched. All GPUs are released.

The approved question was whether the finite direct-image-access regime in Qwen2.5 CoT transfers to Qwen3 CoT under the same bounded assay. The [approved plan](../../../plan/stage9a3_bounded_vab_calibration_qwen25_vs_qwen3_cot_plan.md) and [frozen execution protocol](../../../plan/stage9a3_execution_protocol_v1.md) govern this run. The controlled counting setup follows the [VAB paper's task description](https://arxiv.org/html/2607.12815v2); this is a bounded reimplementation, not an exact published-boundary reproduction.

The corpus contains32 primary images,16 prospectively frozen reserve images and4 disjoint technical images. Each image has one color and one shape query. Prompts/options, greedy decoding, BF16 weights, preprocessing limits, seeds and model revisions were frozen. Every decoder layer participates in the depth/time rectangle; prefill, image K/V and previously propagated image information remain intact. The grid is depth fractions0/.5/.75/1 × token cutoffs0/16/64/FULL. Both models passed all eight actual-model technical checks, including exact no-op logits/tokens, zero blocked probabilities, preserved prefill and cached continuation.

| FULL cohort | Correct | Intermediate reasoning | Valid option / normal EOS | Capped |
|---|---:|---:|---:|---:|
| Qwen2.5 primary,32 images |47/64 (73.44%)|62/64 (96.88%)|64/64|0|
| Qwen2.5 reserve,16 images |21/32 (65.63%)|32/32|31/32|1|
| Qwen2.5 combined,48 images |68/96 (70.83%)|94/96 (97.92%)|95/96|1|
| Qwen3 primary,32 images |20/64 (31.25%)|56/64 (87.50%)|46/64|18|

All160 FULL texts were reviewed without answer keys before review seals and grading. Literal format repairs preserve the emitted option even when the model's prose count disagrees. Capped/missing answers receive no credit; no item was discarded. The mandatory initial baseline gates were evaluated on the original64 primary trajectories. The reserve's one capped FULL trajectory remains in the48-image analysis.

The32-image Qwen2.5 grid gave clear zero-access damage, but the frozen tie rule selected(0.75L,64), whose4.69pp point damage had wide uncertainty and only56.13% joint bootstrap stability. The predeclared16-image precision extension therefore activated. Its unchanged grid resolved the selection to **all decoder layers through token64**. No cutoff, prompt, cap or image selection changed.

| Qwen2.5 condition,48 images | Accuracy | Damage vs FULL |95% image-bootstrap interval for damage |
|---|---:|---:|---:|
| FULL |70.83%|0|reference|
| Zero generated-query access |48.96%|21.88pp|11.46 to32.29pp|
| All layers through token16 |54.17%|16.67pp|8.33 to25.00pp|
|75% of layers through token64 |60.42%|10.42pp|1.04 to19.79pp|
| **All layers through token64** |**71.88%**|**−1.04pp**|**−5.21 to3.13pp**|

The selected condition passes the5pp preservation tolerance with **99.35% joint bootstrap stability**, together with positive zero-access damage. Raw strict-format extraction also passes, selects the same cutoff, and gives94.93% joint stability. This supports coarse finite access; it does not locate an exact token boundary or imply that visual information is erased after64. The selected mask is actually reached in92/96 native trajectories; the other four are exact identity reuses.

Inference uses equal image weighting and4,000 paired image-cluster bootstrap draws with seed920260927. Queries, cells and tokens are not independent samples. The full16-cell surface is preserved in the parquet files;32-image and48-image results remain separately accessible.

The bounded null-sink control used the primary32 images and only FULL, zero access and the selected all-layer/token64 condition.125 new continuations were needed;67 exact identities were reused. Without redistributing removed image probability onto other keys, zero-access damage remains **15.63pp [4.69,26.56]**, while token64 damage is **−1.56pp [−7.81,3.13]**. The qualitative calibration pattern survives this bounded alternative intervention.

Qwen3 fails the60% accuracy floor,90% CoT requirement and extraction/completion gates under the frozen assay. Eight outputs contain only an option;18 reach the256-token cap without a final answer. Even granting every unscorable output a correct answer yields only38/64=59.38%, below the floor. This bound holds the46 completed answers fixed and is not an imputed score. Visual/count errors, repetition and censoring are observed; their underlying cause is not established.

One consequential limitation is explicit: the frozen protocol made Qwen3 inherit Qwen2.5's256-token cap. Qwen3's technical maximum was235 tokens; applying its own1.5× length rule would have suggested512. That alternative was not run. The observed validity failure therefore belongs to this frozen prompt/task/decoding setup, and no Qwen model-generation, architecture or Thinking-specialization claim follows. No Qwen3 masked science or null-sink experiment was launched after the failed gate. Its coarse-grid parquet is an explicitly marked **empty schema artifact**, not a zero-effect result; comparison fields are null.

The initial Qwen2.5 technical validator incorrectly required eight naturally generated tokens. The repair extended only the teacher-forced cache probe and respected native EOS; all eight examples were revalidated in a new namespace. The failed receipt, six completed initial checks and original source remain preserved.26 focused CPU tests passed during implementation. Seven independent final audit groups passed, including a separate numerical reconstruction of the48-image bootstrap, all input/source/output hashes, and the mandatory stop. See [final validation](audit/final_validation.json).

Compute totaled approximately **1.88 GPU-hours**, including **1.81 GPU-hours for Phase A**, well below25. There were1,143 scientific generations: Qwen2.5 FULL96 + primary masked571 + reserve masked287 + null-sink125, and Qwen3 FULL64. Up to four GPUs ran concurrently through the project scheduler on authorized nodes; no tmux or keepalive was used. Accounting combines captured Slurm runtimes with documented submission-to-receipt estimates where completed jobs had purged. Scientific generation time itself was1.58 GPU-hours. Both checkpoints were local; no download or package installation was needed.

The previous MathVision main report and all74 completed controls remain byte-identical. Its13 unfinished controls were cancelled at safe boundaries under this plan's§27; no prior result was reinterpreted.

Figures are available as PNG/PDF: [intervention](figures/figure1_intervention_rectangle.pdf), [primary surface](figures/figure2_qwen25_surface.pdf), [48-image surface](figures/figure2b_qwen25_extended_surface.pdf), and [Qwen3 validity stop](figures/figure3_qwen3_validity_stop.pdf). A Qwen3 transfer surface and same-cutoff effect figure are not estimable. The [artifact index](stage9a3_artifact_index.json) distinguishes completed, conditional and unmeasured outputs.

**Exactly one recommendation:** obtain a separately approved bounded repair and validation of the Qwen3 FULL-access baseline before drawing a generation-level visual-access conclusion. **STOP; this recommendation has not been executed.**
