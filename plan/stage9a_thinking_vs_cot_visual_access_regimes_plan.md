# Stage 9A — Thinking vs CoT Visual Access Regimes

## 0. One-line objective

Determine whether **native Qwen3-VL-2B Thinking** exhibits a qualitatively different visual-access regime from **Qwen3-VL-2B Instruct** under direct answering or prompted CoT.

Primary question:

\[
\boxed{
\textbf{Does native Thinking exhibit recurrent, reasoning-conditioned visual re-access
that is not reproduced merely by eliciting longer CoT?}
}
\]

This is the first gate of the broader Stage 9 program.

Do **not** proceed to bottleneck, bypass, or same-prefix mechanism studies unless Stage 9A establishes a credible regime difference.

---

# 1. Why this experiment is necessary for the paper

The current paper has a strong mechanistic story within Qwen3-VL Thinking:

\[
\text{reasoning demand}
\rightarrow
\text{target-specific visual retrieval}
\rightarrow
\text{Value-rich transfer}
\rightarrow
\text{short-lived local carrier}
\]

and controlled \(A\rightarrow B\rightarrow A\) experiments show that the causal visual source can dynamically retarget with changing reasoning demand.

However, the current story does not yet distinguish:

\[
\boxed{\text{native Thinking}}
\]

from:

\[
\boxed{\text{prompted CoT / longer generation}}
\]

This distinction is scientifically important because nearby work suggests that longer CoT can remain largely language-side, while other work on parametric factuality suggests that native Thinking may facilitate information retrieval rather than merely produce more tokens.

Stage 9A tests the minimum prerequisite for the stronger thesis:

\[
\boxed{
\textbf{Thinking may learn a state-dependent information-retrieval policy,
rather than merely a longer computation policy.}
}
\]

---

# 2. Models and experimental arms

Use the same model scale.

## Model A
**Qwen3-VL-2B-Instruct**

## Model B
**Qwen3-VL-2B-Thinking**

Run three arms.

### A1 — Instruct Direct
Qwen3-VL-2B-Instruct with the standard direct-answer prompt.

### A2 — Instruct CoT
Qwen3-VL-2B-Instruct with a fixed CoT elicitation prompt.

Recommended frozen wording:

> Think step by step before answering.

Do not tune multiple CoT prompts after outcomes are opened.

### A3 — Native Thinking
Qwen3-VL-2B-Thinking using its native thinking-format inference path.

The key comparisons are:

\[
A1 \rightarrow A2
\]

for the effect of eliciting longer reasoning within the same Instruct checkpoint, and:

\[
A2 \rightarrow A3
\]

for behavior that is not reproduced by prompted CoT.

---

# 3. Claim hierarchy

## Primary claim if positive

> **Prompting an Instruct model to produce longer CoT does not reproduce the recurrent visual-access regime observed in the matched Thinking checkpoint.**

## Stronger claim reserved for later stages

Do **not** yet claim:

> Thinking learns a retrieval policy.

Stage 9A can only establish the behavioral/internal regime difference.

The learned-policy claim requires later same-prefix and bypass evidence.

## Null interpretation

If Stage 9A finds no meaningful difference:

- do not force a Thinking-specific story;
- retain the existing reasoning-conditioned retrieval paper framing;
- stop the Stage 9 bottleneck/bypass branch unless another clear difference emerges.

---

# 4. Benchmark and cohort

Use **MathVision** for continuity with Stage 8.

Recommended design:

\[
\boxed{128 \text{ items for Stage 9A discovery}}
\]

with broad coverage across:

- subject/category
- difficulty
- multiple-choice vs free-response
- visual/problem subtype
- reasoning length

Prefer items not previously used for intervention development if practical.

The same 128 items must be run in all three arms.

Use one conservative visual-family representative per family where possible.

---

# 5. Inference protocol

Use each checkpoint's intended/native inference path for the main comparison.

## Instruct Direct / Instruct CoT

Use the same generation settings across A1 and A2:

- temperature = 1.0
- top_p = 0.95
- top_k = 20
- repetition penalty = 1.0
- presence penalty = 0
- max_new_tokens = 40960
- normal EOS stopping
- frozen MathVision preprocessing/chat template for Instruct

Only the CoT elicitation prompt differs between A1 and A2.

## Native Thinking

Use the frozen Stage 8 Thinking protocol:

- temperature = 1.0
- top_p = 0.95
- top_k = 20
- repetition penalty = 1.0
- presence penalty = 0
- max_new_tokens = 40960
- normal EOS stopping
- native Thinking chat/preprocessing path

Record any unavoidable template differences explicitly.

---

# 6. Core scientific contrast

The stage is not about raw visual attention.

The main hypothesis is a difference in **visual-access regime**.

### Boundary-like regime

\[
\text{early visual engagement}
\rightarrow
\text{long language-side continuation}
\]

### Schedule-like regime

\[
\text{visual engagement}
\rightarrow
\text{gap}
\rightarrow
\text{re-engagement}
\rightarrow
\text{gap}
\rightarrow
\text{re-engagement}
\]

Working conceptual labels:

\[
\boxed{
\text{Visual Access Boundary}
\quad\text{vs}\quad
\text{Visual Access Schedule}
}
\]

Do not use “Visual Access Schedule” as an established phenomenon unless Stage 9A supports it.

---

# 7. Measurement strategy

Do **not** define the result by the frozen Stage 8A detector alone.

The detector was developed on Qwen3-VL-2B-Thinking, so cross-checkpoint score calibration may differ.

Use a **multi-view measurement panel**.

## 7.1 Raw routing features

Measure per generated reasoning token:

- visual attention share
- visual QK statistics
- top visual-source concentration where source partition exists
- source entropy where available
- alphaV / related transport-side quantities if cheap

Use architecture-matched layer/head windows where exact layer numbering is shared.

## 7.2 Frozen retrieval proxy

Apply the frozen Stage 8A retrieval detector **as-is**.

Frozen threshold:

\[
\tau_R = 0.5478025980771918
\]

Do not recalibrate per checkpoint in Stage 9A.

Use it as one measurement channel, not as ground truth.

Report both:

- continuous retrieval score
- thresholded episode structure

## 7.3 Reasoning-time normalization

Because reasoning lengths will differ, report:

\[
\boxed{\text{retrieval episodes per 1k reasoning tokens}}
\]

and:

- retrieval-active token fraction
- late retrieval fraction
- retrieval episode count
- median inter-episode gap
- longest inter-episode gap
- fraction of episodes after 25%, 50%, and 75% normalized reasoning position

## 7.4 Demand alignment

Annotate or automatically identify a bounded set of semantic demand events where the reasoning trace clearly requires visual information.

Examples:

- identifying a new visual object/value
- comparing visual entities
- revisiting a previously used visual fact
- source switch between distinct visual regions

For each demand event, measure whether visual re-engagement occurs within a fixed local window.

Primary window:

\[
\boxed{\pm 16 \text{ generated tokens}}
\]

Secondary:

\[
\pm 32
\]

Primary metric:

\[
\boxed{
P(\text{visual retrieval near demand event})
}
\]

This is more important than raw retrieval count.

---

# 8. Small causal source-sensitive validation subset

To ensure the result is not merely a checkpoint activation-scale difference, select a small frozen subset of clear visual-demand events from each arm.

Recommended:

\[
\boxed{24\text{–}32 \text{ events per arm where feasible}}
\]

Use fixed-history source-sensitive tests:

- target vs irrelevant visual-source substitution
- original vs counterfactual semantic content
- sham/control substitution

Question:

> Does the current visual source/content causally affect the next local evidence at these events?

The purpose is validation, not a full mechanistic replication.

Do not tune event selection after causal results are opened.

---

# 9. Primary endpoints

Freeze these before opening arm-level results.

## P1 — Demand-aligned retrieval rate

\[
P(\text{retrieval within }\pm16\text{ tokens of visual-demand event})
\]

Main comparison:

\[
A3 - A2
\]

## P2 — Late retrieval fraction

Fraction of retrieval episodes occurring after 50% normalized reasoning position.

Main comparison:

\[
A3 - A2
\]

## P3 — Retrieval recurrence density

\[
\text{episodes per 1k reasoning tokens}
\]

Main comparison:

\[
A3 - A2
\]

## P4 — Long-gap re-engagement

Probability that a new retrieval episode occurs after at least 128 reasoning tokens since the previous retrieval episode.

This distinguishes repeated re-access from dense local burstiness.

---

# 10. Secondary endpoints

- retrieval-active token fraction
- episode duration
- inter-episode gap distribution
- earliest retrieval timing
- retrieval after 75% normalized position
- source entropy
- target/source selectivity
- benchmark accuracy
- reasoning length
- EOS/cap rate
- visual attention share
- frozen detector continuous score

Accuracy is **secondary** in Stage 9A.

The scientific question is whether computational regimes differ.

---

# 11. Required length controls

A raw Thinking-vs-CoT difference is insufficient if Thinking simply generates longer traces.

Run all of the following.

## 11.1 Per-token normalization

Episodes per 1k reasoning tokens.

## 11.2 Normalized reasoning position

Map each trajectory to \([0,1]\).

## 11.3 Length-matched subset

Construct a predeclared matched subset of A2 and A3 trajectories with similar reasoning length.

Recommended caliper:

\[
|\log L_{A2} - \log L_{A3}| \le 0.15
\]

or nearest-neighbor matching with the same fixed caliper.

Do not change the caliper after seeing retrieval outcomes.

## 11.4 Length-adjusted regression

Control for:

- log reasoning length
- completion status
- subject/category
- difficulty
- answer format
- question length

The key coefficient is:

\[
\boxed{
\text{Thinking vs Instruct-CoT}
}
\]

---

# 12. Statistical unit

Primary independent unit:

\[
\boxed{
\text{MathVision item / conservative visual family}
}
\]

Do not treat tokens or retrieval episodes as independent samples.

Use:

- family-clustered bootstrap
- family-weighted effects
- item-level paired comparisons across arms

The same item appears in all three arms, enabling paired analyses.

---

# 13. Primary hypothesis pattern

The strongest expected pattern is:

\[
A1 \approx A2
\]

for recurrent visual-access metrics, while:

\[
\boxed{
A3 > A2
}
\]

for:

- demand-aligned retrieval
- late retrieval
- long-gap re-engagement
- retrieval recurrence density

after length control.

Interpretation:

> **Longer prompted CoT alone is insufficient to reproduce the recurrent visual-access regime of the Thinking checkpoint.**

---

# 14. Alternative patterns and interpretation

## Outcome A — Strong Thinking-specific regime

A3 > A2 after length control and causal validation confirms genuine source-sensitive use.

### Claim
> Native Thinking exhibits recurrent, reasoning-conditioned visual re-access not reproduced by prompted CoT.

### Next step
Proceed to Stage 9B/9C.

---

## Outcome B — CoT and Thinking are similar

A2 ≈ A3 across retrieval recurrence, demand alignment, and causal validation.

### Interpretation
The recurrent visual-retrieval mechanism is likely not Thinking-specific.

### Next step
Stop the Thinking-vs-CoT branch and retain the broader reasoning-conditioned retrieval story.

---

## Outcome C — Raw difference disappears after length matching

A3 > A2 in raw counts but not after per-token / length-controlled analysis.

### Interpretation
The difference may be primarily generation-length driven.

### Next step
Do not claim a Thinking-specific retrieval regime.

---

## Outcome D — Detector differs, raw/causal measures do not

Frozen detector score is higher in Thinking, but demand alignment and causal source-sensitive validation are similar.

### Interpretation
Likely detector calibration / activation-scale mismatch.

### Next step
Do not advance the Stage 9 story.

---

## Outcome E — CoT itself develops recurrent retrieval

A2 > A1 and A2 ≈ A3.

### Interpretation
Prompted CoT may be sufficient to induce recurrent visual retrieval.

### Next step
Reframe Stage 9 around reasoning-mode-independent recurrent retrieval rather than Thinking specialization.

---

# 15. What a null does NOT rule out

A null difference between A2 and A3 does not imply:

- Thinking and CoT are computationally identical
- Thinking has no other information-retrieval advantage
- retrieval demand representation is identical
- retrieval source selection is identical under matched prefixes

It only rules against the specific Stage 9A hypothesis that their **native visual-access regimes differ robustly at the trajectory level**.

Do not launch same-prefix or bypass stages solely to rescue a weak Stage 9A result.

---

# 16. Relation to the broader Stage 9 roadmap

If Stage 9A is positive:

## Stage 9B
Reasoning-length control + controlled \(A\rightarrow B\rightarrow A\) comparison.

Question:
> Does Thinking-specific source retargeting remain under controlled recurrent demand?

## Stage 9C
Same-prefix 2×2 assay.

Question:
> Is the difference caused by reasoning trajectory content, checkpoint identity, or both?

## Stage 9D
Controlled task regimes:

- single-read
- delayed reuse
- source switching
- A→B→A refresh

Question:
> When does Thinking outperform CoT?

## Stage 9E
Timed re-look bypass.

Question:
> Does CoT have the perceptual capacity but fail to self-initiate retrieval?

## Stage 9F
JIT vs upfront evidence oracle.

Question:
> Is temporal evidence availability the bottleneck?

## Stage 9G
Event-timed access gating.

Question:
> Is an event-specific visual-access schedule sufficient relative to continuous or early-only access?

## Stage 9H
Cross-family replication.

---

# 17. Scientific story dependency

Stage 9A should change the paper only if it establishes a genuine regime distinction.

### If positive

The paper can evolve from:

> Thinking MLLMs recurrently query vision.

toward:

> **Native Thinking is not merely longer CoT; it exhibits a different information-access regime in which visual evidence is recurrently re-engaged as reasoning demands evolve.**

### If null

Do not weaken the existing core paper by forcing a CoT-vs-Thinking story.

Retain:

\[
\boxed{
\text{reasoning-conditioned dynamic visual retrieval}
}
\]

as the central contribution.

---

# 18. Implementation notes

Reuse as much Stage 8 infrastructure as possible:

- MathVision preprocessing
- trajectory logging
- retrieval-feature extraction
- detector code
- source partitioning
- causal replay utilities

Add only:

- Instruct checkpoint loading
- Direct vs CoT prompt switch
- common arm manifest
- normalized-time trajectory analysis
- demand-event annotation pipeline

Do not modify frozen Stage 8 artifacts.

---

# 19. Required artifacts

Produce:

1. `stage9a_cohort_manifest.json`
2. `stage9a_generation_config.json`
3. `stage9a_instruct_direct_trajectories.parquet`
4. `stage9a_instruct_cot_trajectories.parquet`
5. `stage9a_thinking_trajectories.parquet`
6. `stage9a_retrieval_features.parquet`
7. `stage9a_retrieval_episodes.parquet`
8. `stage9a_demand_events.parquet`
9. `stage9a_length_matched_pairs.json`
10. `stage9a_primary_effects.json`
11. `stage9a_causal_validation.json`
12. `stage9a_accuracy_secondary.json`
13. `stage9a_summary.md`

---

# 20. Key figures

## Figure 1 — Visual-access trajectories by regime

Three rows:

- Instruct Direct
- Instruct CoT
- Thinking

Plot normalized reasoning time with retrieval episodes.

Purpose:
Visually distinguish front-loaded vs recurrent access.

## Figure 2 — Retrieval recurrence and late access

Show:

- episodes / 1k tokens
- late retrieval fraction
- long-gap re-engagement

for A1/A2/A3.

## Figure 3 — Demand alignment

For semantic visual-demand events, show retrieval probability around event time.

Ideal pattern:

\[
\text{Thinking}
>
\text{Instruct-CoT}
\approx
\text{Instruct-Direct}
\]

## Figure 4 — Length-matched comparison

Thinking vs Instruct-CoT after matching reasoning length.

This figure is essential if raw lengths differ substantially.

## Figure 5 — Causal source-sensitive validation

For frozen event subsets, compare:

- target semantic substitution
- irrelevant source substitution
- sham

across Instruct-CoT and Thinking.

Purpose:
Show that the observed regime difference reflects genuine visual-source use, not only activation-scale differences.

---

# 21. Go / no-go criterion

Proceed to Stage 9B/9C only if the evidence supports all of the following:

1. Thinking shows a larger recurrent visual-access phenotype than Instruct-CoT on at least two primary metrics.
2. At least one of those differences remains after reasoning-length control.
3. Demand alignment supports event-specific re-engagement rather than diffuse attention elevation.
4. The small causal subset confirms that at least part of the difference corresponds to genuine source-sensitive visual use.
5. The result is not driven entirely by one subject/subtype.

If these criteria fail, do not proceed to the bottleneck/bypass story.

---

# 22. Final decision target

Stage 9A is successful if it establishes:

\[
\boxed{
\textbf{Prompting Qwen3-VL-2B-Instruct to reason longer does not reproduce
the recurrent, demand-aligned visual-access regime of Qwen3-VL-2B-Thinking.}
}
\]

This result would justify the next mechanistic question:

\[
\boxed{
\textbf{Why does the Thinking checkpoint convert reasoning demand into visual retrieval
when prompted CoT does not?}
}
\]

That is the entry point for the later learned-retrieval-policy, bottleneck, and timed-bypass story.
