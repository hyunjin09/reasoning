You are continuing the **Visual–Reasoning Dynamics in Thinking MLLMs** project.

Read the existing project documentation and Stage 0 artifacts first. In particular, understand that Stage 0 was only an instrumentation-validation phase and that **Stage 2 causal experiments must not be started in this task**.

# Project Context

The broader research question is:

> **How does a Thinking MLLM allocate computation between fresh visual evidence and accumulated reasoning context during long-form multimodal reasoning? When and why does it directly access visual evidence, what supports reasoning when direct visual dependence is low, and how do these dynamics eventually differ between successful and failed reasoning trajectories?**

For now, we are **not developing a method**.

We first want to characterize current Thinking MLLMs.

Important methodological principle:

> **Raw attention is descriptive evidence, not causal evidence.**

Do not interpret high visual attention as proof that the model is causally using vision, and do not interpret low visual attention as proof that the model is reasoning from stored visual memory.

Causal tests will come in later stages.

---

# Stage 0 Status

Stage 0 is complete and passed all eight instrumentation acceptance criteria.

Verified results:

- Smoke faithfulness: `3/3` exact baseline/instrumented generation match.
- Full Stage 0 run: `30/30` artifact bundles independently validated.
- Outcomes:
  - `4` correct
  - `26` truncated
  - `0` wrong
  - `0` invalid
- The 26 truncated traces all reached the fixed `2048` generation-token cap.
- Peak GPU allocation: `10.76 GB`.
- Largest example bundle: `16.45 MB`.
- Five representative visual overlays passed spatial-alignment inspection.
- Descriptive attention trends were recorded but are **not causal evidence**.
- A Unicode tokenizer-prefix issue affecting nine examples was repaired without rerunning inference. Token IDs, generations, scores, attention arrays, and statuses were unchanged.

Primary Stage 0 evidence includes:

```text
outputs/stage0/summaries/stage0_summary.md
outputs/stage0/summaries/validation.json
outputs/stage0/summaries/decode_alignment_repair.json
outputs/stage0/summaries/visual_sanity_check.md
workspace/phase_memory/phase_0_visual_reasoning_instrumentation.md
```

Do not overwrite or retrospectively alter Stage 0 outputs.

The major constraint entering Stage 1 is:

> **2048 generated tokens is too short for most Qwen3-VL-4B-Thinking MathVerse trajectories.**

---

# Stage 1 Goal

Stage 1 is the first scientific discovery phase, but remains **descriptive**.

Main question:

> **What temporal visual–reasoning patterns naturally occur over complete successful reasoning trajectories in Qwen3-VL-4B-Thinking?**

We want to discover whether trajectories tend to show patterns such as:

```text
early-heavy visual engagement

repeated visual peaks

persistent visual engagement

mostly vision-light reasoning

strong sample-to-sample heterogeneity
```

Do not force these categories if the actual model behavior differs.

Stage 1 has two parts:

```text
Stage 1A — Generation Protocol Pilot

Stage 1B — Baseline Dynamics Discovery
```

Stage 1A must pass before Stage 1B begins.

After Stage 1B, stop.

Do **not** begin Stage 2.

---

# Stage 1A — Generation Protocol Pilot

## Objective

Determine a generation cap that produces sufficiently complete Thinking trajectories without blindly spending excessive compute/storage.

Start by changing only the generation cap.

Keep:

```text
model = Qwen3-VL-4B-Thinking
decoding = greedy / deterministic
do_sample = false
```

Keep the same:

- prompt template,
- image preprocessing,
- evaluator,
- instrumentation,
- attention extraction,
- token alignment,
- visual-token mapping

that passed Stage 0.

---

## Pilot Samples

Use approximately **20 Stage 0 examples**.

Prefer:

```text
16 previously truncated examples
4 previously completed examples
```

If this exact composition is inconvenient, use a documented representative 20-example subset with a strong majority of previously truncated examples.

Do not overwrite Stage 0 inference results.

---

## First Pilot

Run:

```text
max_new_tokens = 4096
```

for all pilot samples.

Measure and report:

```text
completion count/rate
truncation count/rate
correctness among completed traces
median generation length
p90 generation length
maximum generation length
per-example latency
peak GPU allocation
artifact size
```

### Completion definition

A trajectory is complete only if:

1. generation terminates before the token cap,
2. the evaluator can extract a final answer,
3. the trace is not invalid,
4. the reasoning is not visibly cut by the generation limit.

If a trace hits the cap, classify it as `truncated`, even if an answer-like string occurred earlier.

---

## Generation-Cap Decision

If the 4096 pilot has:

```text
truncation rate <= 10%
```

lock:

```text
max_new_tokens = 4096
```

for Stage 1B.

If:

```text
truncation rate > 10%
```

run the 4096-truncated samples again with:

```text
max_new_tokens = 8192
```

If fewer than 10 samples truncate at 4096, add previously truncated Stage 0 samples so the 8192 pilot contains at least ~10 examples when feasible.

If the 8192 pilot achieves:

```text
truncation rate <= 10%
```

lock:

```text
max_new_tokens = 8192
```

for Stage 1B.

If truncation remains above 10% even at 8192:

> **STOP before Stage 1B.**

Do not silently increase the cap further.

Instead produce a protocol-revision report with the observed length distribution and recommended next options.

---

# Faithfulness Check Under the New Cap

Because the generation horizon changed, repeat the instrumentation-faithfulness check.

For at least 3 pilot examples run:

```text
uninstrumented inference

vs.

instrumented inference
```

under the selected Stage 1 generation cap.

Requirement:

```text
3/3 exact generated-token match
```

If this fails, stop and debug before Stage 1B.

---

# Stage 1B — Discovery Cohort

Once the generation protocol is locked, construct the baseline dynamics discovery set.

Target:

```text
100 completed + correct trajectories
```

Use at most:

```text
200 raw MathVerse examples
```

to obtain them.

Prioritize:

```text
visually intensive examples
multi-step reasoning
non-trivial reasoning length
Vision Intensive / Vision Dominant variants when identifiable
```

Do **not** select examples based on whether they exhibit a preferred visual-attention pattern.

We do not want cherry-picked `LOOK → THINK → LOOK` examples.

---

## Minimum Cohort Rule

If fewer than 100 eligible examples are obtained after 200 raw attempts:

- report the actual count,
- do not weaken the criteria retrospectively.

If:

```text
eligible completed-correct trajectories >= 80
```

Stage 1B may continue with the smaller cohort.

If:

```text
eligible trajectories < 80
```

stop Stage 1 and report insufficient discovery cohort.

Do not start Stage 2.

---

# Preserve All Raw Outcomes

Even though the primary discovery set uses completed-correct trajectories, save all generated examples:

```text
correct
wrong
truncated
invalid
```

Do not discard wrong traces.

They may later become useful for failure analysis.

But do not mix them into the primary normal-mechanism analysis.

---

# Reasoning Span Representation

The primary scientific unit should be a **reasoning span**, while keeping token-level raw data.

For each generated reasoning trace create reproducible spans with:

```text
span_id
start_token
end_token
span_text
semantic_label
```

Use coarse labels such as:

```text
VISUAL_READ
COMPUTE
RELATION_INFERENCE
VERIFY
PLAN
ANSWER_SELECTION
OTHER
```

Important:

> `VISUAL_READ` is a semantic/textual label, not an attention-derived label.

Do not label a span `VISUAL_READ` simply because visual attention is large.

If the segmentation/labeling process is automatic, manually inspect at least 20 trajectories and report typical segmentation errors.

---

# Signals to Analyze

For each reasoning token and span, preserve/compute the following descriptive signals.

## 1. Visual Attention

For span `s` and layer `l`:

```text
A_vis[s,l]
```

Save both:

```text
total attention mass to visual tokens
```

and

```text
per-visual-token normalized density
```

because the visual source set contains many tokens.

---

## 2. Prompt / Question Attention

Save:

```text
total attention mass to prompt/question positions

normalized per-source-token density
```

---

## 3. Previous Reasoning Attention

Save:

```text
total attention mass to previous generated reasoning tokens

normalized per-source-token density
```

Normalization is particularly important here because the number of previous reasoning tokens increases continuously during generation.

---

## 4. Visual Focus Distribution

For every span obtain a distribution over visual tokens/patches.

Preserve enough information to compute:

```text
similarity to prefill visual focus
similarity to previous reasoning span
spatial entropy
top-k visual-token overlap
visual-focus turnover
```

These are descriptive statistics only.

---

## 5. Predictive Uncertainty

Record at token level:

```text
entropy
top-1 probability
top-1 vs top-2 margin
```

At span level report at least:

```text
mean
maximum
end-of-span value
```

Do not conclude that uncertainty triggers visual access in Stage 1.

---

# Per-Example Timeline

For each eligible sample produce a compact timeline similar to:

```text
Reasoning time ------------------------------------>

Semantic stage:
READ A | COMPUTE | VERIFY | READ B | COMPUTE

Visual attention:
██████ | ░░░░░░░ | ██░░░░ | ██████ | ░░░░░░

Previous reasoning attention:
░░░░░░ | ███████ | ██████ | ███░░░ | ███████

Entropy:
  ██   |   █     |  ███   | ████   |   █
```

Again:

> Do not call these regions causal LOOK/THINK states.

They are descriptive candidate patterns.

---

# Candidate Visual-Peak Detection

For exploratory analysis only, identify candidate visual-attention peaks.

Recommended:

```text
span-level signal
light smoothing
scipy.signal.find_peaks
prominence-based detection
```

Do not use one arbitrary absolute attention threshold across all examples.

For each example save:

```text
number of peaks
peak positions
peak prominence
inter-peak distances
normalized generation positions
```

The purpose is to identify candidate events that later stages may test causally.

---

# Dataset-Level Statistics

Compute at least:

```text
distribution of number of visual peaks

fraction of examples with:
  0 peaks
  1 peak
  >=2 separated peaks

temporal distribution of peaks

distribution of visual-focus shifts

total visual-attention mass over trajectory

fraction of spans with high descriptive visual engagement

relationship between trace length and peak count

relationship between MathVerse variant and visual dynamics
```

Use bootstrap confidence intervals where practical.

---

# Exploratory WHEN/WHY Alignment

Stage 1 should investigate whether candidate visual events appear aligned with:

```text
semantic subgoal boundaries

VISUAL_READ semantic spans

visual-reference language:
  figure
  diagram
  shown
  labeled
  look
  check
  etc.

entropy changes

large visual-focus shifts

elapsed reasoning time since the previous candidate peak
```

Possible analyses:

```text
event-aligned averages
lag analysis
simple regression
correlation
contingency tables
```

But maintain the following boundary:

> These analyses identify hypotheses only.

Do not write:

```text
uncertainty causes LOOK
subgoal transitions cause re-grounding
```

based on Stage 1 correlation.

Those claims belong to later controlled experiments.

---

# MathVerse Paired-Variant Preparation

One important goal of Stage 1 is to prepare the next-stage paired experiment.

Identify MathVerse examples corresponding to the same underlying problem under different modality-information variants.

Create a pairing manifest containing fields such as:

```text
base_problem_id
variant
example_id
image_id
question_id
completed
correct
reasoning_length
```

Report:

```text
number of base problems with >=2 aligned variants
available variant pairs
completion rate by variant
correctness by variant
reasoning-length distributions by variant
```

Do **not** yet perform the causal paired-variant experiment.

Only make sure Stage 2 can use these pairs cleanly.

---

# Representative Qualitative Set

Select approximately:

```text
10–15 completed-correct trajectories
```

covering diverse patterns such as:

```text
early-heavy visual attention
recurrent visual peaks
persistent visual attention
very low visual attention
large visual-focus shifts
small visual-focus shifts
```

For each, save:

```text
input image
question
complete reasoning
span segmentation
attention timeline
uncertainty timeline
selected visual-focus overlays
```

Document why each example was selected.

Do not select only examples supporting a preferred hypothesis.

---

# Stage 1 Scientific Boundaries

Stage 1 **may** report observations such as:

> Visual attention often shows recurrent peaks.

> Some trajectories are early-heavy while others remain visually engaged.

> Candidate peaks tend to align with certain semantic reasoning stages.

> Different MathVerse variants show different descriptive visual-attention dynamics.

Stage 1 **must not** claim:

> The model causally LOOKs here.

> The model switches to THINK mode here.

> Uncertainty causes re-grounding.

> The model stores visual evidence in reasoning hidden states.

> Low visual attention means it is reasoning from visual memory.

> Repeated visual-attention peaks prove repeated fresh evidence acquisition.

These require causal intervention in later stages.

---

# Suggested Output Structure

Use a structure similar to:

```text
outputs/
  stage1/
    protocol_pilot/
      config_4096.json
      config_8192.json
      protocol_report.md
      faithfulness_check.json

    discovery/
      cohort_manifest.jsonl
      raw_outcome_manifest.jsonl

      examples/
        <example_id>/
          generation.json
          tokens.jsonl
          spans.json
          attention_summary.npz
          uncertainty.npz
          visual_focus/
          plots/

      paired_variants/
        pairing_manifest.jsonl
        pairing_report.md

    summaries/
      stage1_statistics.json
      stage1_summary.md
      candidate_hypotheses.md
```

Do not overwrite Stage 0.

---

# Required Reports

## `protocol_report.md`

Include:

```text
4096 pilot results
8192 pilot results if needed
selected final max_new_tokens
completion/truncation statistics
length distribution
latency implications
storage implications
faithfulness result
```

---

## `stage1_summary.md`

Include:

```text
discovery cohort construction

number of raw examples attempted

correct / wrong / truncated / invalid counts

generation-length distribution

span segmentation procedure

descriptive visual/reasoning dynamics

dataset-level temporal statistics

representative qualitative patterns

paired-variant availability

limitations

explicit reminder:
attention != causal visual usage
```

---

## `candidate_hypotheses.md`

Rank the strongest hypotheses emerging from the data.

For each hypothesis write:

```text
Hypothesis

Supporting Stage 1 observation

Alternative explanations

What causal experiment would distinguish them
```

Examples may include:

```text
Visual engagement is recurrent rather than monotonically decaying.

Candidate visual peaks align more strongly with semantic transitions than uncertainty.

Visual strategies are strongly sample-dependent.

Modality variants appear to modulate direct visual engagement.

Visual access appears concentrated near newly visually grounded subgoals.
```

Do not force these if the observed data do not support them.

This report should directly inform the design of the next causal stage.

---

# Stage 1 Acceptance Criteria

Stage 1 passes only if all of the following hold.

## Generation protocol

1. A final generation cap is prospectively selected.
2. Pilot truncation rate under the selected cap is `<= 10%`.
3. Instrumented/uninstrumented generation under the selected cap matches exactly on `3/3` faithfulness examples.

## Discovery cohort

4. At least `80` completed-correct eligible trajectories are available.
5. Wrong/truncated/invalid raw trajectories are preserved separately.

## Analysis quality

6. Token and span timelines are reproducible.
7. Visual/prompt/reasoning attention statistics are available with source-token-count normalization.
8. Visual-focus distributions and uncertainty signals are available.
9. Dataset-level temporal statistics are computed.
10. At least 10 representative trajectories are manually inspected.
11. MathVerse paired variants can be reliably aligned for the next stage.

## Scientific discipline

12. No attention-only result is presented as causal visual usage.
13. No Stage 2 causal experiment has been started.

---

# Stop Conditions

Stop before Stage 1B if:

```text
8192 still has >10% truncation
```

or if:

```text
new-cap instrumentation is not faithful
runtime/storage becomes impractical
```

Stop before Stage 2 if:

```text
<80 eligible completed-correct trajectories

temporal statistics are not reproducible

span segmentation is too unreliable

MathVerse paired variants cannot be aligned

descriptive signals are too weak or inconsistent to motivate a targeted causal experiment
```

Unexpected scientific results are acceptable.

For example, if the model is persistently visual rather than recurrent, or almost entirely vision-light, report that result instead of forcing the original hypothesis.

---

# Final Deliverables

Before finishing Stage 1, provide:

1. locked generation protocol,
2. `protocol_report.md`,
3. raw-outcome manifest,
4. discovery cohort manifest,
5. target `100` / minimum `80` completed-correct trajectories,
6. span-level descriptive dynamics,
7. dataset-level temporal statistics,
8. representative timeline plots,
9. paired MathVerse variant manifest/report,
10. `stage1_summary.md`,
11. `candidate_hypotheses.md`,
12. explicit PASS/FAIL for every Stage 1 acceptance criterion.

Then **STOP**.

Do not start Stage 2.