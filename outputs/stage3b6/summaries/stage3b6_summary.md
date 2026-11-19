# Stage 3B.6 summary

Technical status: **PASS** (17/17 acceptance criteria).

## Frozen design

Stage 3B.6 preserved the three heterogeneous Stage 3B.5 Attention-gain cells and kept `E_d/W5` separate as an upstream-state control. All 32 logical query heads were ranked on eight disjoint discovery bases using paired causal restoration—not raw attention—before any 37-base confirmatory score was read.

The primary intervention retained the recipient current query, swapped donor post-RoPE K/V only at frozen preceding source positions, recomputed Attention, and spliced selected logical query-head outputs before `W_O`. All downstream computation recomputed naturally.

## Head localization

The frozen confirmatory family contained 14 cell/unit tests; 10 passed the Holm-corrected restoration gate.

- `Ed__W4`: H-Partial-Recovery; confirmed units ['Top_4', 'Top_8'].
- `Ed_minus_1__W4`: H-Sparse; confirmed units ['Top_2', 'Top_4', 'Top_8'].
- `Ed_minus_1__W5`: H-Partial-Recovery; confirmed units ['All_robust', 'Top_1', 'Top_4', 'Top_8', 'head_10'].

## Upstream-state control

The frozen minimal source-path target from each qualifying cell was also evaluated at the separate `E_d/W5` control only after head candidates were frozen:
- `Ed__W4/Top_4` at `E_d/W5`: median BHR -0.0033, 95% bootstrap CI [-0.0183, 0.0388], bidirectional fraction 0.270, median HRR -0.0031.
- `Ed_minus_1__W4/Top_2` at `E_d/W5`: median BHR -0.0009, 95% bootstrap CI [-0.0158, 0.0048], bidirectional fraction 0.189, median HRR -0.0003.
- `Ed_minus_1__W5/head_10` at `E_d/W5`: median BHR 0.9841, 95% bootstrap CI [0.6322, 1.4043], bidirectional fraction 0.973, median HRR 0.9771.

## Source paths

The Phase A gate passed for 3 frozen target(s), so all/V/P/R swaps were run on the exact 37-base cohort.
- `Ed__W4/Top_4`: V-dominant; median PRR {'P': 0.009326060180405524, 'R': 0.0, 'V': 0.9792892956048782, 'all': 1.0}. V alone passed the frozen robust-dominance rule.
- `Ed_minus_1__W4/Top_2`: V-dominant; median PRR {'P': 5.29817801484057e-08, 'R': 0.03771623691568244, 'V': 0.8850314748607613, 'all': 1.0}. V alone passed the frozen robust-dominance rule.
- `Ed_minus_1__W5/head_10`: mixed_or_redundant; median PRR {'P': 0.016517502106655306, 'R': 0.019233533251611697, 'V': 0.9886032688658982, 'all': 1.0}. High median PRR was observed for V (median sham/semantic ratio 0.436), but the frozen robustness controls failed; source attribution is inconclusive.

## Secondary triangulation

Stage 3B.1 cutoff damage versus V-path restoration: Spearman {'N': 37, 'spearman_rho': -0.21574205784732098, 'p_value': 0.1996914989305675}.
Raw selected-head visual attention versus causal all-source restoration: Spearman {'N': 37, 'spearman_rho': -0.3627311522048364, 'p_value': 0.02735363988522895}.
These secondary associations do not turn attention magnitude into a causal measurement.

## Scientific boundary

Head restoration localizes a causal Attention computation under this hybrid intervention. It does not identify an exact ROI, K-versus-V mechanism, attention-pattern mechanism, MLP feature, long-term Q/R lifecycle, or discrete LOOK/THINK state. HRR and PRR are unclipped comparative restoration ratios, not unique information fractions.

## Recommendation

**GO — ROI-specific visual path + pattern/value decomposition**

At least one confirmed causal head/set has a robust visual-dominant source path under the frozen PRR rule.

Stage 3B.6 stops here. No recommended follow-on experiment was started.
