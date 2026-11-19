# Stage 3C.7 Summary — Prior-Cache and Residual Joint Rescue

## Outcome

Stage 3C.7 is **technically PASS (20/20)** on all 24 frozen primary base problems. The target-specific scientific outcome is:

- **Target A: O2 — Residual–Cache Complementarity.** The frozen L33 `h_post_attn` residual and L34–35 downstream `t_pre` cache jointly recover the deficit substantially and near-completely.
- **Target B: O1 — Prior-Cache Carrier.** Full P4 `t_pre` K+V exactly restores the native score, but the frozen L35 residual plus L35-only downstream cache remains below the substantial-joint threshold.
- Overall: **target-heterogeneous O2-A / O1-B**.

The sole review-only recommendation is **GO — Token-Type Carrier Atlas**. No follow-on experiment was started.

## Frozen design and validation

The exact Stage 3C.6 seven-base validation and 24-base primary cohorts, Target A/B states, P4 target-ROI suppression (layers 16–35, all 32 logical heads, `t_pre` only), semantic O/C conditions, and A5000 numerical environment were reused. Donors and recipients always shared the same image condition.

Cache patches use the native Qwen3-VL GQA representation: post-RoPE K and projected V with shape `[1, 8 KV heads, 1 t_pre token, 128]`. Only `t_pre` was replaced. Visual prompt K/V, current-query K/V, and every other reasoning-cache position remained recipient-native. The frozen joint scopes were A: L33 `h_post_attn` + L34–35 cache; B: L35 `h_pre` + L35 cache.

The corrected one-base smoke and all seven validation bases passed cache layout, position, component isolation, visual/current-state invariance, exact self-patch, exact Stage 3C.6 reproduction, joint-order, repeatability, and finite-score checks. A first smoke launch that accidentally inherited two Slurm tasks was preserved as `raw/validation_smoke_failed_v1` and excluded before audit; the rerun fixed only the launch task count.

## Phase A — prior-cache rescue

| Target | K median gain / RR | V median gain / RR | K+V median gain / RR | Classification |
|---|---:|---:|---:|---|
| A | -0.0829 / -0.1393 | 0.3638 / 0.6404 | 0.5528 / 1.0000 | C-KV |
| B | -0.0192 / -0.0892 | 0.2047 / 0.6000 | 0.3035 / 1.0000 | C-KV |

K-only rescue is not robust for either target. V-only rescue is robust for both, but its median gain is only about two-thirds of K+V and does not meet the frozen “approaches K+V” rule. K+V exceeds both K and V robustly after target-specific 12-test Holm correction, yielding C-KV for both targets.

Full P4 K+V exactly reproduces the native token-level scores in **96/96** target × condition × base cells. Thus the matching native `t_pre` cache is sufficient to repair the tested P4 deficit under this intervention. This does not make RR a unique causal information fraction.

Suppression-induced cache deltas begin after layer 16, as expected because the layer-16 K/V projection precedes its local suppressed attention output. Delta magnitude was never used to choose layers. Its post-freeze Spearman association with full-cache rescue was 0.446 for A and 0.643 for B; this is secondary and descriptive.

## Phase B — residual and cache joint rescue

| Target | Residual RR | Downstream-cache RR | Joint RR | Frozen joint gate | Outcome |
|---|---:|---:|---:|---|---|
| A | 0.4162 | 0.6902 | 1.0006 | substantial + near-complete | O2 |
| B | 0.3410 | 0.1083 | 0.4611 | below 0.50 | O1 |

For A, joint gain exceeds residual-only on 24/24 bases (median increment 0.3051) and downstream-cache-only on 20/24 bases (median increment 0.1192); both pass the fixed Holm family and robustness rule. This is clean residual–cache complementarity at the frozen boundary. It is not labeled O3 synergy because downstream cache alone is already substantial.

For B, L35 downstream-cache-only and joint-over-residual each have only 16/24 positive bases and fail the 75% robustness rule. Joint RR is 0.4611, below 0.50. Yet full P4 cache rescue is exact, locating B's tested cache support more broadly than the one remaining downstream layer at its L35 boundary.

The Target-A-only gated joint decomposition passed mechanical validation and all 24 bases: K+residual median gain/RR is 0.1939/0.4349 and is not robust because its bootstrap mean CI crosses zero; V+residual is robust at 0.4940/0.7265; K+V+residual is 0.5724/1.0006 and exceeds both. The gated mechanism is Value-dominant with additional K/V interaction. Target B was not run because its J4 gate failed.

## Controls and reproducibility

- Stage 3C.6 native, suppressed, and frozen residual-only scores reproduce exactly for every primary target/condition cell.
- Native→native and suppressed→suppressed cache/residual self patches are exact on all seven validation bases.
- Q/prompt cache replacement is exactly equal to suppressed in 96/96 primary cells; mean and median gain are zero.
- J5 full-cache + residual is exactly native in 96/96 cells.
- Corrected smoke J4 repeats are exact. Validation and primary mechanical audits pass.
- Maximum GPU allocation across primary runs was 8.83 GiB. Optional rollouts were prospectively omitted.

## Interpretation and limits

The exact immediately preceding reasoning token's native K/V cache carries behaviorally useful consequences of the P4 visual-acquisition event in both frozen targets. Target A additionally demonstrates that native late current residual and continued native prior-cache access are complementary. Target B instead needs cache restoration across the broader P4 depth to obtain complete rescue under the tested suffix readout.

This result is conditional on two frozen evidence coordinates, localized numeric MathVerse edits, teacher-forced suffix scoring, and an intervention that replaces native state. It does not establish universal token-type roles, whole-history lifecycle, attention-sink function, upstream vision origin, failure mechanisms, or a unique information decomposition. Raw attention was neither a selection signal nor an intervention target.

## Stop boundary

Stage 3C.7 stops here. No Token-Type Carrier Atlas, sink manipulation, R_last2/R_last4, residual-feature analysis, Stage 4, multi-evidence refresh, or failure experiment has started.
