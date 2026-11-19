# Stage 3B.3 Plan — Layer-wise Visual-to-Reasoning Transfer Localization

## 0. Purpose

Stage 3B.3 is the first layer-wise mechanistic localization stage.

Stage 3B.2 established that the identity of the future visual source causally controls the upcoming evidence decision even after a long reasoning history is fixed.

Late Stage 3B.2 results:

- E_d-1: median normalized BRI = 0.9703; bidirectional 49/49
- E_d: median normalized BRI = 0.8022; bidirectional 49/49
- sham/target ratio ≈ 1%
- 12 exact-baseline-token cases independently retained strong late source control

The next question is:

> At which transformer layers is evidence-specific visual content transferred into the current reasoning computation?

Stage 3B.3 should build a causal layer-wise map of:

visual source -> current reasoning state -> evidence decision

This stage is focused on layer localization.

Do not yet perform Q/R long-term carrier analysis, ROI-specific source switching, attention-vs-MLP decomposition, head/path analysis, multi-evidence A/B refresh, or correct-vs-wrong failure analysis.

---

## 1. Scientific Handoff

### Stage 2A–2C
Visual ROI attention was mostly aligned with evidence verbalization rather than clearly preceding it.

Therefore high visual attention is not itself evidence of fresh acquisition.

### Stage 3A
Localized visual counterfactuals changed evidence preference in the expected direction for 49/49 unique bases.

### Stage 3B.0
Generation-start visual cutoff retained only 14.5% mean / 6.1% median of the Stage 3A effect. The surviving residual was largely carried by Q-side cached states.

### Stage 3B.1
Future all-visual cutoff remained damaging even immediately before evidence expression:

- 0/49 reached retention >= 0.80
- median retention at E0-1 = 0.1114
- 43/49 showed persistent direct-vision dependence

### Stage 3B.2
Counterfactual future visual-source switching showed that late direct vision carries evidence-specific identity:

- E_d-1 normalized median BRI 0.9703
- E_d normalized median BRI 0.8022
- bidirectional 49/49 at both points
- sham effects ~1%

Therefore Thinking MLLMs actively retrieve evidence-specific visual content during reasoning.

Stage 3B.3 asks where across layer depth this transfer occurs.

---

## 2. Important E_d Boundary

The frozen cohort contains:

- 12 exact-baseline-token cases
- 37 controlled semantic teacher-forced candidate-decision cases

All 49 remain the primary causal cohort.

The 12 exact-baseline cases must be reported as a dedicated robustness stratum.

Natural-trajectory timing claims should not rely only on the 37 semantic-lead cases.

---

## 3. Research Questions

RQ1. Which layer windows are sufficient to transfer counterfactual visual evidence identity into the current evidence decision?

RQ2. Which layer windows are necessary for the full all-layer visual-source-switch effect?

RQ3. Is evidence-specific visual retrieval localized, distributed, redundant, or sequential across layers?

RQ4. At which layer does the current reasoning-token residual state first causally encode donor evidence identity?

RQ5. Does evidence become decodable before, during, or after the causally important transfer layers?

---

## 4. Primary Cohort

Use the same frozen 49 unique base problems:

- 45 numeric-label edits
- 4 structural edits
- 12 exact-baseline-token E_d cases
- 37 semantic-lead E_d cases

Primary statistical unit: base_problem_id.

Attempt all 49 in the coarse scan.

No attention-based or effect-size-based selection.

---

## 5. Primary Decision Coordinates

Use two frozen coordinates:

- E_d - 1
- E_d

E_d-1 allows one step of downstream propagation before the discriminative decision.

E_d switches the visual source for the query directly predicting the first discriminative token.

Both are primary.

---

## 6. Coarse Layer Windows

Qwen3-VL-4B-Thinking has 36 language layers.

Freeze:

- W0 = layers 0–5
- W1 = layers 6–11
- W2 = layers 12–17
- W3 = layers 18–23
- W4 = layers 24–29
- W5 = layers 30–35

The coarse scan is mandatory before fine localization.

---

## 7. Intervention A — Selective Layer-Window Visual-Source Switching

This tests window sufficiency.

For original-history recipient:

- layers outside W use original visual K/V
- layers inside W use counterfactual visual K/V

Keep Q/P/R cache, token identities, and all nonvisual states unchanged.

Run reciprocal C-history + O-vision-in-W as well.

If one layer window alone moves evidence preference toward the donor fact, that window is causally sufficient to transmit part of the evidence identity.

---

## 8. Window Sufficiency Metric

Reuse Stage 3B.2 evidence preference D = L_O - L_C.

For O -> C:

S_W^(O->C) = D_OO - D_O,C(W)

For reciprocal C -> O:

S_W^(C->O) = D_C,O(W) - D_CC

Define bidirectional window sufficiency:

BWS(W) = [S_W^(O->C) + S_W^(C->O)] / 2

Unnormalized BWS is primary.

Secondary normalized score:

BWS_norm(W) = BWS(W) / BRI_all-layer

Do not clip normalized values.

---

## 9. Intervention B — Window Restoration Under Full Donor Switch

Selective switching can underestimate importance if transfer is redundant.

Start with the full Stage 3B.2 donor switch:

O-history + counterfactual visual K/V at all layers

Then restore original visual K/V only in W.

If restoring W moves the decision back toward the original fact, W is necessary for a substantial part of the donor effect.

Run the reciprocal direction too.

---

## 10. Window Necessity Metric

For O-history:

N_W^O = D_O,C(all except W) - D_O,C(all)

Positive values mean restoring original visual K/V in W rescues original evidence preference.

Define the reciprocal source-oriented quantity and average:

BWN(W)

Secondary normalization:

BWN_norm(W) = BWN(W) / BRI_all-layer

Do not assume window effects sum to the full effect.

Nonlinearity and redundancy are expected.

---

## 11. Why Both Sufficiency and Necessity Matter

Possible patterns:

- High BWS + high BWN: strong causal hotspot
- Low BWS + high BWN: necessary but insufficient; possible sequential/distributed computation
- High BWS + low BWN: redundant sufficient pathway
- Low BWS + low BWN across all windows with strong all-layer effect: distributed synergy

Do not infer absence of mechanism from low selective-switch effect alone.

---

## 12. Cumulative Layer-Switch Analysis

Run lower-prefix cumulative donor switching:

- layers 0..5
- 0..11
- 0..17
- 0..23
- 0..29
- 0..35

Run upper-suffix cumulative donor switching:

- 30..35
- 24..35
- 18..35
- 12..35
- 6..35
- 0..35

These curves help distinguish localized, sequential, and distributed transfer.

---

## 13. Prospectively Freeze Fine-Localization Rule

Before inspecting cohort-scale results, freeze a rule such as:

Refine a coarse window if at E_d-1 or E_d:

- median normalized BWS >= 0.20, or
- median normalized BWN >= 0.20, or
- its bootstrap CI clearly separates it from at least two nonadjacent windows.

Include adjacent windows if needed to avoid boundary artifacts.

Save this rule before the coarse scan.

---

## 14. Fine Localization

For qualifying regions, refine with 2-layer windows.

Example for W2:

- 12–13
- 14–15
- 16–17

If a 2-layer window remains strongly localized, optional single-layer refinement may be run inside that window.

Single-layer refinement is exploratory and not required for technical PASS.

Do not scan unrelated layers post hoc.

---

## 15. Intervention C — Current-Reasoning-State Activation Patching

Layer-window source switching localizes where visual input is causally influential.

To test when the evidence identity has entered the current reasoning state, perform a complementary causal trace.

At E_d, run original and counterfactual conditions with identical controlled token sequence.

At layer boundary l, patch only the current query-position residual state from donor C into recipient O:

h_current,l^C -> h_current,l^O

and reciprocally.

Then let remaining layers run normally with recipient visual source.

Question:

At which layer does the current reasoning position contain enough donor evidence identity to causally move the final evidence decision?

---

## 16. Activation-Patching Scope

Patch only the current reasoning/query position residual state.

Do not patch all token positions, Q, previous reasoning positions, or full KV cache.

Use coarse boundaries first:

- after layer 5
- after layer 11
- after layer 17
- after layer 23
- after layer 29
- after layer 35

Refine only near prospectively selected hotspots.

---

## 17. Activation-Patch Metric

Use the same evidence preference.

Define a source-oriented bidirectional activation-patch effect BAP(l).

Primary comparison:

- visual-source causal hotspot
- first layer where BAP(l) becomes strong

A plausible information-flow result would be:

visual-source effect peaks in layers 12–17
-> current-token residual becomes donor-like after layer 17

This would support actual visual-to-reasoning transfer.

---

## 18. Secondary Readout — Layer-wise Evidence Decodability

After causal analyses are frozen, optionally unembed the current reasoning residual at each layer and track the original-vs-counterfactual discriminative-token logit difference.

This is descriptive only.

If a validated tuned lens is already available without training a new model-specific artifact, it may be added as a secondary readout.

Do not train a new probe/tuned lens inside this stage without separate approval.

Goal:

compare when evidence becomes decodable with where source switching and activation patching show causal transfer.

---

## 19. Sham Controls

Every selective layer switch and restoration experiment must include sham-source versions.

At minimum:

O history + sham visual K/V in W

Expected:

abs(sham window effect) << abs(counterfactual window effect)

Self replacement must be transparent.

If a hotspot is equally strong for sham switching, it is not evidence-specific.

---

## 20. Technical Smoke Gate

Use 3 numeric-label bases.

Verify:

1. all-layer switch reproduces Stage 3B.2
2. no-switch reproduces baseline
3. self window switch is transparent
4. sham window switch is small
5. only selected layer-window visual K/V is replaced
6. Q/P/R cache remains unchanged
7. visual token positions match source/recipient
8. E_d-1 and E_d indexing is exact
9. restoration uses donor source everywhere except W
10. current-position activation patch changes only intended residual state
11. reciprocal directions have correct sign conventions
12. all scores are finite and deterministic

Stop if smoke fails.

---

## 21. Primary Analysis A — Coarse Layer Causal Atlas

For each coarse window at E_d-1 and E_d report:

- mean/median BWS
- bootstrap CI
- normalized BWS
- mean/median BWN
- normalized BWN
- O->C consistency
- C->O consistency
- bidirectional consistency
- sham effect

Produce layer-window x causal-transfer plots.

---

## 22. Primary Analysis B — Localized vs Distributed Transfer

Use selective, restoration, and cumulative experiments jointly.

Descriptive mechanism classes:

- L1 narrow hotspot
- L2 sequential transfer
- L3 redundant multi-window transfer
- L4 distributed synergy
- L5 early-dominant transfer
- L6 late-dominant transfer

Do not force one class if heterogeneous patterns coexist.

---

## 23. Primary Analysis C — Visual Transfer vs Current-State Encoding

Compare BWS/BWN with BAP.

Strong mechanistic evidence would show:

1. counterfactual visual K/V is causally influential in a particular layer region
2. after that region, current reasoning residual patching transfers donor evidence identity
3. later layers mainly transform/refine rather than first acquire the evidence

This is stronger than attention-only interpretation.

---

## 24. Exact-Baseline Robustness

For the 12 exact-baseline-token cases report separately:

- coarse BWS/BWN
- cumulative curves
- activation-patch curves
- hotspot agreement with full cohort

Questions:

- do the same causal layer regions appear?
- are conclusions unchanged on natural baseline-token decisions?

Do not use N=12 as the primary cohort, but use it to qualify natural-trace claims.

---

## 25. Evidence-Type Analysis

Report:

- numeric labels N=45
- structural edits N=4

Structural N=4 is descriptive only.

---

## 26. Relation to Prior MLLM Information-Flow Work

Prior non-thinking MLLM work found image-to-language/question transfer in lower-to-middle layers, including an earlier broad-image stage and a later question-relevant stage.

Stage 3B.3 asks a related but different question:

> During an active Thinking step, which layers transfer the currently needed evidence-specific visual content into the current reasoning computation?

Possible outcomes:

- similar lower/middle-layer integration
- later retrieval band during Thinking
- distributed transfer
- multiple transfer stages

Do not assume prior layer patterns must replicate.

---

## 27. Relation to Attention

Do not use attention to select causal layer windows.

After causal layer results are frozen, optionally compare:

- layer-wise causal switch effect
- stored visual attention mass by layer if available
- prior mention-centered ROI attention

Question:

Does high attention identify the layers that causally transmit evidence identity?

This is secondary.

---

## 28. What Stage 3B.3 May Establish

If supported:

> Evidence-specific visual retrieval during Thinking is mediated by a particular causal layer region.

and:

> Counterfactual visual identity enters the current reasoning residual state after/within that region.

Alternatively, the legitimate result may be:

> Retrieval is distributed or redundant across multiple layers.

---

## 29. What Stage 3B.3 Cannot Yet Establish

Do not claim:

- which heads implement transfer
- whether attention or MLP is the key module
- which exact ROI tokens are causal
- where evidence is stored after the current decision
- Q->R long-term handoff
- repeated A/B retrieval episodes
- wrong-answer failure mechanism

---

## 30. Decision After Stage 3B.3

### GO — Module/path localization
If a reproducible causal layer hotspot or narrow region is found.

Next questions:
- attention vs MLP?
- which heads?
- which visual->reasoning paths?

### GO — Distributed layer mechanism analysis
If transfer is clearly distributed/redundant.

Use multi-window/path methods rather than a single-layer hotspot story.

### REDIRECT — Current-state representation analysis
If source-switch effects are diffuse but activation patching shows a sharp residual-state transition.

### REDESIGN
If selective/restoration interventions fail controls or cannot reproduce the all-layer effect.

---

## 31. Output Structure

Create:

```text
outputs/stage3b3/
  config/
    stage3b3_config.json
    cohort_manifest.jsonl
    coarse_layer_windows.json
    fine_localization_rule.json

  smoke/
    layer_switch_validation.md
    layer_switch_validation.json
    activation_patch_validation.json

  scoring/
    coarse_window_switch_results.jsonl
    coarse_window_restoration_results.jsonl
    cumulative_layer_results.jsonl
    activation_patch_results.jsonl
    fine_layer_results.jsonl

  analysis/
    coarse_layer_statistics.json
    window_sufficiency_statistics.json
    window_necessity_statistics.json
    cumulative_transfer_statistics.json
    activation_patch_statistics.json
    exact_baseline_robustness.json
    evidence_type_analysis.json
    optional_layer_readout.json
    figures/

  summaries/
    stage3b3_summary.md
    stage3b3_acceptance.json
    next_stage_recommendation.md
```

---

## 32. Required Figures

At minimum:

1. coarse layer-window BWS at E_d-1
2. coarse layer-window BWS at E_d
3. coarse layer-window BWN at both coordinates
4. lower-prefix cumulative switch curve
5. upper-suffix cumulative switch curve
6. current-position activation-patch recovery by layer
7. source-switch hotspot vs activation-patch transition
8. full 49 vs exact-baseline 12 comparison
9. representative per-problem causal layer profiles

Optional:
10. layer-wise evidence decodability vs causal effects

---

## 33. Acceptance Criteria

Stage 3B.3 technically passes if:

1. all 49 frozen bases are attempted in the coarse scan
2. both E_d-1 and E_d are analyzed
3. six coarse windows are frozen before scoring
4. all-layer positive control reproduces Stage 3B.2
5. self and sham controls pass
6. selective layer-window switching is bidirectional
7. full-switch window restoration is bidirectional
8. cumulative lower/suffix analyses are completed
9. fine-localization rule is frozen prospectively
10. fine localization is limited to qualifying regions
11. current-position residual activation patching is validated
12. base_problem_id remains the statistical unit
13. exact-baseline 12-case robustness is reported
14. attention is not used to select causal windows
15. no module/head/path/Q-R/ROI-specific experiment is started
16. a clear next-stage recommendation is written

Technical PASS does not require a narrow hotspot.

---

## 34. Stop Condition

After completing:

- smoke validation
- 49-base coarse scan
- sufficiency and necessity analyses
- cumulative layer analysis
- prospectively gated fine localization
- current-position activation patching
- exact-baseline robustness
- optional descriptive layer readout
- final mechanistic interpretation

STOP.

Do not start:

- attention-vs-MLP decomposition
- head-level analysis
- path patching
- ROI-specific source switching
- Q/R long-term carrier tracing
- multi-evidence A/B retrieval
- correct-vs-wrong failure analysis

Return the complete Stage 3B.3 results for review.

The next stage must be selected only after considering Stage 3B.3 together with the full Stage 2A–3B.2 evidence chain.
