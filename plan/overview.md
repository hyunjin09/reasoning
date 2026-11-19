# Research Overview: Visual–Reasoning Dynamics in Thinking MLLMs

## 1. Project Goal

This project studies **how Thinking Multimodal Large Language Models (Thinking MLLMs) allocate computation between fresh visual evidence and their accumulated reasoning context during long-form reasoning**.

The central question is:

> **When does a Thinking MLLM directly rely on fresh visual evidence, when can it continue reasoning from previously accumulated context, what drives transitions between these modes, and how do these dynamics fail on incorrect reasoning trajectories?**

The project is primarily an **analysis / mechanistic interpretability study** at this stage. Do **not** begin by designing a new re-grounding, routing, or attention-control method. The first objective is to understand what current models actually do.

## 2. Core Research Questions

### RQ1 — WHEN / WHAT
**When does the model directly use vision, and which visual evidence is being used?**

Possible behaviors include:
- early visual acquisition followed by vision-light reasoning,
- repeated `LOOK → THINK → LOOK → THINK`,
- persistent visual dependence,
- almost no direct visual dependence,
- input-dependent mixtures of the above.

Ultimately we want **evidence-specific temporal dependence**. If a problem needs evidence A and later evidence B, a strong result would be:

\[
V_{s,A}: 	ext{HIGH} ightarrow 	ext{LOW} ightarrow 	ext{LOW}
\]

\[
V_{s,B}: 	ext{LOW} ightarrow 	ext{LOW} ightarrow 	ext{HIGH}
\]

where \(V_{s,e}\) is the causal dependence of reasoning span \(s\) on visual evidence \(e\).

### RQ2 — WHY
**What determines when the model directly accesses visual evidence?**

Candidate explanations:
- predictive uncertainty,
- semantic subgoal transition,
- demand for new visual evidence,
- insufficient previously acquired evidence,
- elapsed reasoning time,
- lexical or learned heuristics.

Do not assume uncertainty is the trigger. A key hypothesis is that visual access is driven by **current evidence demand** rather than absolute generation time.

### RQ3 — HOW
**What supports reasoning when fresh direct visual dependence becomes small?**

Possible explanations:
1. the visual fact is no longer needed,
2. the model explicitly wrote the fact into its generated CoT,
3. the fact is encoded in prompt/question-token states,
4. the fact is encoded in generated reasoning-token hidden/KV states,
5. the model is no longer grounded and is continuing from language prior.

A major mechanistic goal is to test whether visual information is causally transferred into reasoning-side representations.

### RQ4 — FAILURE
**How do incorrect reasoning trajectories differ from successful ones?**

Possible failure mechanisms:
- acquisition failure,
- wrong visual fixation,
- premature disengagement,
- failed handoff,
- missed refresh,
- available-but-unused / language-prior override,
- pure downstream reasoning failure,
- unnecessary visual dependence / possible over-grounding.

Failure analysis should preferably compare **multiple correct and incorrect stochastic trajectories for the same item**.

## 3. Working Conceptual Model

\[
oxed{
	ext{Evidence Demand}
ightarrow
	ext{Direct Visual Access}
ightarrow
	ext{Evidence Acquisition}
ightarrow
	ext{Reasoning-Side Use}
ightarrow
	ext{New Evidence Demand}
ightarrow
	ext{Direct Visual Access}
}
\]

For discussion only:
- **LOOK**: fresh image information has causal influence on the current continuation.
- **THINK**: fresh direct visual dependence is low and computation proceeds primarily from already constructed context/state.

Do **not** define LOOK/THINK using a raw attention threshold. Use continuous causal quantities first.

## 4. Positioning Against Nearby Work

### vStream
vStream studies **where each reasoning step is visually grounded**, including correct-versus-incorrect attribution trajectories.

Our question is what happens **after** evidence has been observed:
- when is fresh visual access needed again?
- when is reasoning supported by accumulated state?
- what determines the transition?

### Pathways of Visual Information Flow
Prior pathway work studies direct and text-mediated routes by which visual information reaches outputs.

Our focus is the **long-form reasoning-time dynamics** of these routes and the identity of evidence being acquired and carried forward.

### ReGround
ReGround studies diagnosis and visual re-examination for multi-step reasoning failures.

Our project should not begin as another re-grounding method. We first ask **why** fresh visual access was necessary, unnecessary, mistimed, or ineffective.

## 5. Initial Model and Benchmark

### Primary model
- **Qwen3-VL-4B-Thinking**

Possible later replication:
- Qwen3-VL-8B-Thinking,
- another open Thinking MLLM family.

### Primary benchmark
- **MathVerse**

Reasons:
- multi-step visual reasoning,
- visually intensive examples,
- evidence can often be localized,
- different reasoning stages can require different visual facts,
- paired modality-information variants are useful for analysis.

## 6. Dataset Roles

### Discovery Set
- mostly baseline-correct,
- visually dependent,
- multi-step,
- used to discover normal dynamics.

### Controlled / Annotated Mechanistic Set
A smaller subset with explicit evidence and ROI annotations.

Example:

```text
Evidence A:
  semantic fact: AC = 3
  ROI: ...

Evidence B:
  semantic fact: BD is tangent to the circle
  ROI: ...

Reasoning stages:
  S1: acquire A
  S2: compute using A
  S3: acquire B
  S4: compute using A/B
```

### Failure Evaluation Set
- not filtered to correct-only,
- includes same-item multiple stochastic rollouts,
- used for failure prevalence and correct/wrong comparisons.

## 7. Planned Experimental Program

### Stage 0 — Instrumentation
Build and validate the logging/analysis pipeline on ~30–50 MathVerse examples.

### Stage 1 — Baseline Dynamics
Characterize visual/reasoning dynamics on ~100–200 successful trajectories.

### Stage 2 — Paired MathVerse Modality Conditions
Compare the same underlying problem when evidence is more visually versus textually available.

### Stage 3 — Evidence-Specific Causal Usage
Measure when specific evidence A/B causally affects reasoning using:
- matched ROI knockout,
- matched counterfactual images,
- local teacher-forced effects,
- downstream free-rollout effects.

### Stage 4 — WHY
Test competing explanations for visual-access transitions.

Key causal manipulations:
- reasoning order `A → B` versus `B → A`,
- visual-only versus text-available evidence,
- uncertainty × evidence-demand controls if needed.

### Stage 5 — Handoff / Carrier Mechanism
Test whether visual information is carried in:
- question/prompt states,
- generated reasoning states,
- explicit generated text.

Use same-text / different-image cache interventions.

### Stage 6 — Evidence Lifecycle
Track:
- acquisition,
- retention,
- decay,
- refresh,
- replacement,
- accumulation,
- interference.

### Stage 7 — Failure Analysis
Compare same-item correct and wrong trajectories and identify distinct causal failure mechanisms.

Only after these stages should we decide whether a new intervention or method is justified.

## 8. High-Value Candidate Phenomena

Candidate findings include:
- Episodic Visual Acquisition,
- Persistent Visual Conditioning,
- Early Visual Internalization,
- Input-Dependent Visual Strategy,
- Subgoal-Driven Visual Routing,
- Uncertainty-Driven Visual Access,
- Visual Access Reduces Uncertainty,
- Latent Visual Handoff,
- Explicit Scratchpad Memory,
- Prompt-Side Visual Memory,
- Visual Memory Decay / Refresh,
- Evidence Replacement / Accumulation / Interference,
- Premature Visual Disengagement,
- Missed Evidence Refresh,
- Wrong Visual Fixation,
- Available-but-Unused Visual Evidence,
- Language-Prior Override,
- Delayed Error Manifestation,
- Visual Self-Repair,
- Pure Symbolic Reasoning Failure.

Negative results are also informative. Do not force the original LOOK/THINK hypothesis if the model exhibits a different mechanism.

## 9. Methodological Rules

1. Do not equate attention magnitude with causal usage.
2. Do not equate low direct-vision dependence with visual memory.
3. Separate explicit CoT memory from latent hidden/KV memory.
4. Separate local causal effects from downstream behavioral effects.
5. Teacher forcing is for controlled local comparisons; it can leak clean visual facts into later reasoning.
6. Use free rollout after intervention for downstream behavioral consequences.
7. Knockout can cause compensatory rerouting; combine necessity tests with content-sensitive counterfactuals.
8. Use matched irrelevant-ROI controls.
9. Do not call high visual dependence “over-grounding” unless it is causally shown to be unnecessary or harmful.
10. Do not design the final method before identifying the dominant mechanism/failure.

## 10. Strong Result Package

A compelling paper would show:

1. **Evidence-specific temporal allocation**
   - A-direct dependence rises and falls,
   - later B-direct dependence rises.

2. **Demand-driven transitions**
   - changing evidence availability or reasoning order changes the visual-access schedule.

3. **Acquired evidence supports later reasoning**
   - image-specific information persists in reasoning-side representations or explicit scratchpad state.

4. **Distinct failures**
   - incorrect trajectories reflect multiple mechanisms, not one generic “visual forgetting” effect.

A possible paper-level message is:

> **Thinking MLLMs dynamically allocate computation between fresh visual evidence and accumulated reasoning context as their information needs evolve. We study what determines this allocation, how acquired evidence supports subsequent reasoning, and how distinct failures of this process lead to incorrect multimodal reasoning.**

## 11. Current Project Principle

**Analyze first. Intervene only to identify causality. Build a method only after the dominant mechanism or failure is established.**
