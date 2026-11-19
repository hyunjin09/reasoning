# Stage 0 Plan: Instrumentation for Visual–Reasoning Dynamics in Thinking MLLMs

## 1. Objective

Stage 0 is an **instrumentation and smoke-validation phase**.

Goal:

> **Build a trustworthy pipeline that records internal visual–reasoning dynamics during MathVerse reasoning without changing baseline model behavior.**

Stage 0 does **not** establish scientific claims.

Do **not** start Stage 1 until all Stage 0 acceptance criteria pass.

## 2. Scope

### Model
- `Qwen3-VL-4B-Thinking`

Use the normal released inference path. Do not modify model weights.

### Dataset
- `MathVerse`

Prefer visually demanding variants such as Vision Intensive / Vision Dominant where available.

### Sample Count
- smoke test: **2–5 examples**
- full Stage 0: **30–50 examples**

Do not run hundreds/thousands of examples in Stage 0.

### Generation
Use deterministic generation first:
- greedy decoding,
- no sampling,
- save the complete reasoning trace and final answer,
- use a sufficiently large generation limit to avoid truncation.

## 3. Non-Goals

Do not do any of the following in Stage 0:
- no final causal claims,
- no re-grounding method,
- no attention-boosting method,
- no LOOK/THINK classifier,
- no RL,
- no training,
- no full failure taxonomy,
- no exhaustive layer/head intervention sweep,
- no cache patching,
- no evidence-lifecycle claim,
- no large-scale benchmark evaluation.

## 4. Required Per-Example Outputs

### Input Metadata
Save:
- example ID,
- MathVerse variant,
- question,
- ground-truth answer,
- image reference/path,
- available category/problem-family metadata.

### Baseline Generation
Save:
- full generated response,
- extracted reasoning portion,
- extracted final answer,
- correctness,
- number of generated tokens.

### Token-Level Metadata
For every generated token, save:
- token index,
- token ID,
- decoded token string,
- generation position,
- token log probability if available,
- next-token entropy,
- top-1/top-2 margin if available.

## 5. Internal Attention Metadata

Collect enough information to compute:
- generated token → visual token attention,
- generated token → question/prompt token attention,
- generated token → previous generated reasoning token attention.

Do not immediately average away all layer/head information.

Preserve enough data for later inspection:
- per layer,
- optionally per head,
- aggregated summaries.

If full attention tensors are too large, implement memory-safe online aggregation and document exactly what is retained.

## 6. Visual Token Mapping

The pipeline must reliably identify visual-token sequence positions.

Record:
- visual token indices,
- number of visual tokens,
- mapping from visual tokens to image grid/spatial regions if recoverable,
- image dimensions and preprocessing metadata needed for visualization.

Produce a few sanity-check visual-attention heatmaps.

These heatmaps are **not causal evidence**.

## 7. Reasoning-Time Representation

Support two resolutions.

### Token Level
Keep the raw token timeline.

### Reasoning Span Level
Create provisional semantic spans, for example:
- inspect a diagram quantity,
- perform arithmetic,
- introduce a geometric relation,
- verify a visual condition,
- select an answer.

For each span save:

```text
span_id
start_token
end_token
span_text
provisional_semantic_label
```

The Stage 0 segmentation method may be sentence-based, rule-based, or an offline annotation step. It does not need to be final.

## 8. Core Logged Signals

For each token and aggregated span, save/compute:

### A. Visual Attention Mass
\[
A^{vis}_s
\]

### B. Prompt / Question Attention Mass
\[
A^{prompt}_s
\]

### C. Previous-Reasoning Attention Mass
\[
A^{reason}_s
\]

### D. Predictive Uncertainty
At minimum:
- entropy,
- top-1 probability,
- top-1 vs top-2 margin.

### E. Visual Focus Distribution
A spatial distribution over visual tokens/patches that can later support:
- ROI analysis,
- visual focus shift analysis,
- evidence-specific analysis.

### F. Lexical / Semantic Context
Record:
- span text,
- visual-reference expressions (`look`, `diagram`, `figure`, `shown`, `labeled`, etc.),
- provisional semantic subgoal.

These are **descriptive signals**, not causal LOOK/THINK labels.

## 9. Diagnostic Visualizations

For several representative examples produce:

### Timeline 1 — Modality Attention
Across reasoning time:
- visual attention mass,
- prompt/question attention mass,
- previous reasoning-token attention mass.

### Timeline 2 — Uncertainty
Across reasoning time:
- entropy,
- confidence/margin.

### Timeline 3 — Reasoning Spans
Overlay:
- span boundaries,
- span labels/text.

### Visual Focus Snapshots
At a small number of reasoning positions:
- map visual attention back to the image.

Purpose:
- validate instrumentation,
- identify candidate patterns for later causal experiments.

Do not optimize figure aesthetics yet.

## 10. MathVerse Paired-Variant Readiness

Inspect and document how MathVerse modality variants are represented locally.

Before leaving Stage 0 determine:
- how to identify examples sharing the same underlying problem,
- which modality-information variants are available,
- how images/questions differ across variants,
- how pairs can be aligned reliably.

Do not run the full paired-variant experiment yet.

## 11. Correctness and Filtering Report

Do not discard wrong examples from raw Stage 0 logs.

Report:
- total examples,
- correct,
- wrong,
- invalid/truncated,
- average reasoning length,
- median reasoning length.

Stage 1 discovery will likely prioritize baseline-correct, multi-step, visually dependent examples.

## 12. Smoke Tests

Before the 30–50-example run, validate on 2–5 examples.

Check:

1. model loads,
2. normal deterministic generation works,
3. instrumented generation matches uninstrumented generation,
4. visual-token indices are correct,
5. attention tensors/summaries have expected shapes,
6. token timeline aligns with decoded text,
7. visual spatial mapping is plausible,
8. outputs save correctly,
9. GPU/RAM/storage use remains bounded.

Only after these pass should the full Stage 0 run start.

## 13. Baseline-Faithfulness Check

This is mandatory.

Run the same smoke examples:
- once with instrumentation disabled,
- once with instrumentation enabled.

Under deterministic decoding, generated tokens and final answers should match.

If they do not match, diagnose whether hooks, attention implementation, caching, or kernel changes altered model execution.

Do not continue until the instrumentation is sufficiently non-invasive.

## 14. Resource / Memory Safety

Attention logging can be expensive.

Requirements:
- detach logged tensors,
- move summaries to CPU,
- stream per-example outputs to disk,
- avoid retaining unnecessary GPU tensors,
- use online aggregation where possible,
- explicitly record aggregation dimensions.

If full attention cannot be stored, keep the minimal information needed for later analysis and document the approximation.

## 15. Suggested Output Structure

```text
outputs/
  stage0/
    config.json
    environment.md
    dataset_report.md
    model_report.md
    instrumentation.md

    examples/
      <example_id>/
        input.json
        generation.json
        tokens.jsonl
        spans.json
        attention_summary.npz
        visual_focus/
        plots/

    summaries/
      stage0_summary.json
      stage0_summary.md
```

Exact filenames may change, but each result must be traceable to one example and configuration.

## 16. Required Documentation

### `environment.md`
Record:
- model checkpoint,
- transformers/torch versions,
- CUDA/GPU information,
- generation configuration.

### `dataset_report.md`
Record:
- MathVerse data location,
- available variants,
- pairing keys,
- selected Stage 0 subset.

### `instrumentation.md`
Explain:
- hooks used,
- attention implementation,
- visual-token identification,
- aggregation rules,
- FlashAttention/SDPA changes if any,
- approximations if any.

### `stage0_summary.md`
Summarize:
- implemented instrumentation,
- validation results,
- examples processed,
- correctness statistics,
- qualitative observations,
- known limitations,
- explicit Stage 0 pass/fail status.

Do not write Stage 1 scientific conclusions into the Stage 0 summary.

## 17. Acceptance Criteria

Stage 0 passes only if:

1. **Deterministic faithfulness**  
   Instrumented and uninstrumented generation match on smoke examples.

2. **Correct visual-token mapping**  
   Visual positions and spatial mapping are verified.

3. **Token/span alignment works**  
   Reasoning maps reliably to token ranges and provisional spans.

4. **Required descriptive signals are recorded**  
   Visual/prompt/reasoning attention summaries and uncertainty metrics are available.

5. **Resource use is manageable**  
   30–50 examples run without uncontrolled RAM/VRAM/storage growth.

6. **Outputs are reproducible and traceable**  
   Each example has configuration and structured logs.

7. **MathVerse paired variants are accessible**  
   Corresponding variants can be identified for later experiments.

8. **Qualitative timelines are inspectable**  
   Several examples can be visually checked end-to-end.

## 18. Stop Conditions

Stop and fix Stage 0 if:
- hooks change deterministic outputs,
- visual token positions are uncertain,
- logged attention does not correspond to actual model computation,
- cache behavior invalidates the recorded quantities,
- spatial mapping is wrong,
- memory/storage use is impractical,
- reasoning token alignment is unreliable.

Do not compensate for broken instrumentation by proceeding to a larger run.

## 19. Allowed Stage 0 Observations

It is fine to note tentative patterns such as:
- visual attention seems concentrated early,
- repeated visual peaks appear,
- entropy and visual attention sometimes co-occur,
- some examples stay visually engaged,
- modality variants appear different.

Label all of these as:

> **qualitative observations / hypotheses for later causal analysis**

Do not call them established mechanisms.

## 20. Exit Deliverables

At the end of Stage 0, provide:

1. working instrumentation code,
2. reproducible configuration,
3. logs for 30–50 MathVerse examples,
4. dataset variant/pairing report,
5. diagnostic timeline plots,
6. `instrumentation.md`,
7. `stage0_summary.md`,
8. a short list of promising Stage 1 hypotheses,
9. pass/fail status for every Stage 0 acceptance criterion.

Then **stop**.

Do not begin Stage 1 automatically.
