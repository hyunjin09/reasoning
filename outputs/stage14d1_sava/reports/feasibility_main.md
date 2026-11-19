# Stage14D1 SAVA feasibility — technical stop

**2026-10-19. Outcome: runtime validation unresolved; scientific pilot not run.** The subgoal-addressed acquisition interface is implemented and the 72-family cohort is frozen. The eight-family technical test failed the predeclared exact-replay gate after a bounded repair/diagnostic. This does not show that targeted visual retrieval is ineffective. H1(query benefit), H2(context benefit), H3(final-answer utility) and H4(target-selection bottleneck) remain untested.

## Goal and implemented method

The objective remains: tell the model exactly which visual evidence its current reasoning step requires and retrieve it in the correct global context. The implemented chain is **question/current prefix → value-free query or NONE → full-image LOCATE → context-preserving READ → resume the same solver**. Offline E*, source annotations, gold, historical correctness, manually selected source targets and human ROIs are absent from runtime inputs. They cannot repair the deployed query or locator.

The user delegated plan amendment and execution without further approval requests. [Execution amendmentv2](../../../plan/stage14d1_sava_execution_amendment_v2.md) records the bounded release and separate16 allocated GPU-hours ceiling, including a2 GPU-hours technical envelope. These numeric limits were chosen under that delegation, not quoted as user-specified values. The original design-only plan is preserved. Old Stage14D's1,674-continuation/375GPUh grid remainsHOLD. Stage14C-V remains unfinished; it was decoupled from this separately gated feasibility test, not marked complete.

## Frozen design and source protection

72 distinct R-panel families were selected by SHA256 ordering with seed `sava-dev-v2-20261019` and deterministic matching to36 global-required,18 local-sufficient and18 local-plus-global opportunities. Selection used source annotations, not answer correctness or intervention outcomes. Known same-construction alias1744 was excluded before generation; original records remain unchanged. Technical IDs are317,760,2577,107,2274,33,1477,737. There were no outcome-based replacements. All 72 had eligible pre-answer prefixes.

The checkpoint is the first 512 historical native Thinking tokens, trimmed before final-answer boundaries; prefixes shorter than 64 tokens would be retained as ineligible. Token decoding matches the historical vLLM raw convention. All arms restart from exactly the same original image/chat prompt/prefix. This is interrupted/restarted inference, not a continuously cloned KV state. Runtime is allowlisted and hashes bind inputs, source pixels and token prefixes.

The six planned arms are N(native continuation), G(generic relook), Q(query without a new helper image), QI(query/full image), QIA(query/predicted address/full image), and QGL(same query/address plus valid local views alongside the full image). Q retains an initially image-conditioned prefix and its final solver retains the original image; it is not globally vision-absent. QIA controls localization computation. GLOBAL/UNRESOLVABLE locations and invalid query/read outputs use recorded aliases/fallbacks. No crop is invented for global structure. A bounded repeated-full-image control was frozen but not run.

A model query about another legitimately needed fact would be judged on that actual target, separately from sampled-opportunity coverage. No such source-semantic success rate is estimable from the current technical results.

## Exact runtime

Pinned `Qwen/Qwen3-VL-4B-Thinking` revision `1de27d8c51f12e819435303b9e84c4e25ba8401e`; BF16; vLLM0.11.0, torch2.8.0, transformers4.57.1, qwen-vl-utils0.0.14, Pillow12.3.0. Sampling: temperature 1, top-p 0.95, top-k 20, repetition penalty 1, presence penalty 0, fixed family seed, nativeEOS. Tensor parallelism 1, max model length 128000, max batch 8, memory utilization 0.85. Original image preprocessing602112–4014080pixels; unchanged source pixels checked.

Main solver cap 81920 was frozen but never used. Technical continuation cap 256 and replay cap 64 intentionally test engineering behavior and cannot estimate final accuracy. V1 query helpers used4096 tokens and native Thinking output. V2 compact helpers explicitly closed their thinking block in the input and used structured final JSON with2048 tokens. This is a compact controller using Thinking weights, not native Thinking behavior for the helper. V3 corrected only grammar field ordering and disabled automatic prefix caching to test the runtime asymmetry. Prompts, cases, seeds, semantic fields and numerical gates remained fixed.

## Observations and bounded repairs

| Attempt | Physical completed calls | Query behavior | Exact native64-token replay | Interpretation |
|---|---:|---|---:|---|
| v1, job146489 |21|4/4 hit4096 tokens without committed JSON|4/4|Helper output-contract failure; pending second shard cancelled|
| v2, job146494 |48|8/8 valid JSON, all NONE|5/8|QUERY grammar branch-order defect; replay gate also fails|
| v3, job146499 |16|Eight query inputs admitted, interrupted before saved completion|6/8|Cache-disabled replay still fails; job cancelled under gate|

V1 unclosed helper thoughts were never parsed as committed queries. V2's JSON grammar listed QUERY properties starting with`subgoal`, whereas the prompt example starts with`status`; NONE starts with`status`. The installed CPU xgrammar test rejects the prompt-order QUERY object and accepts both schema-order QUERY and NONE. Thus a status-first opening excludes QUERY. This establishes an implementation defect/bias, not proof that all eight NONE responses would otherwise become QUERY. The correction has four passing regression tests and preserves both branches. V2 NONE counts are not evidence that these cases lack visual demand.

V2 replay mismatched cases107,317,737 despite identical prompt tokens, seed and sampling. Prefix caching was enabled. Disabling it did **not** restore all-family parity: v3 cases107 and33 first diverge at zero-based generated positions45 and30. All eight v3 pairs have identical prompt tokens, prepared image pixels, seeds and sampling. Remaining numerical/scheduling cause is **unknown**; cache reuse is not established as the sole explanation. See [v3 gate and exact raw paths](../audit/technical_gate_v3_stop.json).

The bounded technical action stops here. The strict gate was not relaxed after observing the failure. There is no forced-query retry, alternative-case search, accuracy-driven prompt tuning, model switch or main launch. The eight interrupted v3 query inputs/last heartbeat remain preserved; their unfinished decoded streams were not committed and are unavailable. Do not invent them.

## Scientific results and missingness

- Planned72families/432main arm slots; **0 main families/0 main slots run**.
-85 completed physical technical requests plus8 interrupted requests;93input receipts total. Replays are included in these counts.
-12 physical G read attempts across v1/v2; no LOCATE/Q/QI/QIA/QGL read requests were reached. Schema validity is not source correctness.
- 72 logical technical continuation slots across versioned attempts reflect fallbacks/aliases, not72independent families or main outcomes.
-Original eight source images inspected; no completed deployment-valid query/address/value semantic panel. No independent reviewer or reliability estimate.
-Accuracy, wrong→correct, correct→wrong, source-specific gains, readout correctness, harm rate, paired bootstrap and mediation are **not estimable**. They are null/not-run in the exported tables, not zeros or cap-as-wrong scores.

Representative source risks include coordinate correspondence across two number lines(2274), top/side-view binding and hidden layers(760), complete grid/panel identity(33), and the marked angle sector across two rectangles(317). These observations justify the proposed source review; they do not establish that SAVA handles them successfully. Full source notes are [offline-only](../analysis/technical_source_context_v1.json).

## Resources and decision

Slurm allocation charges:548s(v1)+580s(v2)+293s(v3)=**1421GPU-seconds =0.394722GPU-hours**, including startup/idle time. Jobs146487,146488,146490were cancelled while pending with0 allocated seconds. All SAVA jobs are terminal and GPUs released. No packages/models/datasets were downloaded. This is below both2 GPU-hours technical and16 GPU-hours stage limits. Request latencies overlap and are not summed as GPU cost.

There is no validated main throughput estimate: short replay/continuation timings and previous native lengths are insufficient after the runtime gate failure. Initial worst-case cap calculations remain preserved as planning bounds, not claimed measured estimates. No main resource reservation remains.

**One recommendation:** resolve and validate restart/replay behavior on the same frozen eight inputs before comparing acquisition methods. No primary SAVA variant can be selected from these results, and Stage14E is NO-GO on technical grounds. No follow-on was launched. [Decision](next_stage_14e_decision.md), [resource ledger](../audit/resource_accounting_final.json), [coverage](../analysis/coverage.json).
